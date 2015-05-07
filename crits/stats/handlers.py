from bson import Code
import datetime

from django.conf import settings
from crits.core.mongo_tools import mongo_connector

from crits.emails.email import Email
from crits.samples.yarahit import YaraHit
from crits.targets.target import Target
from crits.targets.division import Division

def generate_yara_hits():
    """
    Generate yara hits mapreduce.
    """

    samples = mongo_connector(settings.COL_SAMPLES)
    map_code = """
    function() {
            this.analysis.forEach(function(z) {
                    if ("results" in z && z.service_name == "yara") {
                            z.results.forEach(function(x) {
                                    emit({engine: z.service_name, version: x.version, result: x.result} ,{count: 1});
                            })
                    }
                    })
            }
    """
    m = Code(map_code, {})
    r = Code('function(k,v) { var count=0; v.forEach(function(v) { count += v["count"]; }); return {count: count}; }', {})
    try:
        yarahits = samples.inline_map_reduce(m, r,
                                             query={'analysis.service_name': 'yara'})
    except:
        return
    yarahits_col = mongo_connector(settings.COL_YARAHITS)
    yarahits_col.drop()
    sv = YaraHit._meta['latest_schema_version']
    for hit in yarahits:
        yarahits_col.update({'engine': hit["_id"]["engine"],
                             "version": hit["_id"]["version"],
                             "result": hit["_id"]["result"]},
                            {"$set": {"sample_count": hit["value"]["count"],
                                      "schema_version": sv}},
                            True,
                            False)

def generate_sources():
    """
    Generate sources mapreduce.
    """

    samples = mongo_connector(settings.COL_SAMPLES)
    m = Code('function() { this.source.forEach(function(z) {emit({name: z.name}, {count: 1});}) }', {})
    r = Code('function(k,v) { var count=0; v.forEach(function(v) { count += v["count"]; }); return {count: count}; }', {})
    try:
        sources = samples.inline_map_reduce(m,r,
                                            query={"source.name": {"$exists": 1}})
    except:
        return
    source_access = mongo_connector(settings.COL_SOURCE_ACCESS)
    for source in sources:
        source_access.update({"name": source["_id"]["name"]},
                             {"$set": {"sample_count": source["value"]["count"]}})

def generate_filetypes():
    """
    Generate filetypes mapreduce.
    """

    samples = mongo_connector(settings.COL_SAMPLES)
    m = Code('function() emit({filetype: this.mimetype} ,{count: 1});}) }', {})
    r = Code('function(k,v) { var count = 0; v.forEach(function(v) { count += v["count"]; }); return {count: count}; }', {})
    try:
        samples.map_reduce(m,r, settings.COL_FILETYPES)
    except:
        return

def zero_campaign():
    """
    Zero out the campaign counts before recalculating.
    """

    return {
        'actor_count': 0,
        'backdoor_count': 0,
        'indicator_count': 0,
        'sample_count': 0,
        'email_count': 0,
        'domain_count': 0,
        'event_count': 0,
        'exploit_count': 0,
        'ip_count': 0,
        'pcap_count': 0,
    }

def update_results(collection, m, r, stat_query, field, campaign_stats):
    """
    Update campaign results.

    :param collection: The collection to get campaign results for.
    :type collection: str
    :param m: The map.
    :type m: :class:`bson.Code`
    :param r: The reduce.
    :type r: :clas:`bson.Code`
    :param stat_query: The query to use in the mapreduce.
    :type stat_query: dict
    :param field: The field to update.
    :type field: str
    :param campaign_stats: The campaign stats.
    :type campaign_stats: dict
    :returns: dict
    """

    if collection.find().count() > 0:
        results = collection.inline_map_reduce(m,r, query=stat_query)
        for result in results:
            if result["_id"] != None:
                if result["_id"] not in campaign_stats:
                    campaign_stats[result["_id"]] = zero_campaign()
                campaign_stats[result["_id"]][field] = result["value"]["count"]
    return campaign_stats

def generate_campaign_stats(source_name=None):
    """
    Generate campaign stats.

    :param source_name: Limit to a specific source.
    :type source_name: None, str
    """

    # build the query used in the mapreduces
    stat_query = {}
    stat_query["campaign.name"] = {"$exists": "true"}
    if source_name:
        stat_query["source.name"] = source_name
    actors = mongo_connector(settings.COL_ACTORS)
    backdoors = mongo_connector(settings.COL_BACKDOORS)
    campaigns = mongo_connector(settings.COL_CAMPAIGNS)
    domains = mongo_connector(settings.COL_DOMAINS)
    emails = mongo_connector(settings.COL_EMAIL)
    events = mongo_connector(settings.COL_EVENTS)
    exploits = mongo_connector(settings.COL_EXPLOITS)
    indicators = mongo_connector(settings.COL_INDICATORS)
    ips = mongo_connector(settings.COL_IPS)
    pcaps = mongo_connector(settings.COL_PCAPS)
    samples = mongo_connector(settings.COL_SAMPLES)
    # generate an initial campaign listing so we can make sure all campaigns get updated
    campaign_listing = campaigns.find({}, {'name': 1})
    # initialize each campaign to zeroed out stats
    campaign_stats = {}
    for campaign in campaign_listing:
        campaign_stats[campaign["name"]] = zero_campaign()
    mapcode = """
    function() {
            if ("campaign" in this) {
                campaign_list = this.campaign; }
            if (campaign_list.length > 0) {
                campaign_list.forEach(function(c) {
                    emit(c.name, {count: 1}); }); }
        }
    """
    m = Code(mapcode, {})
    r = Code('function(k,v) { var count = 0; v.forEach(function(v) { count += v["count"]; }); return {count: count}; }', {})
    campaign_stats = update_results(actors, m, r, stat_query,
                                    "actor_count", campaign_stats)
    campaign_stats = update_results(backdoors, m, r, stat_query,
                                    "backdoor_count", campaign_stats)
    campaign_stats = update_results(domains, m, r, stat_query,
                                    "domain_count", campaign_stats)
    campaign_stats = update_results(emails, m, r, stat_query,
                                    "email_count", campaign_stats)
    campaign_stats = update_results(events, m, r, stat_query,
                                    "event_count", campaign_stats)
    campaign_stats = update_results(exploits, m, r, stat_query,
                                    "exploit_count", campaign_stats)
    campaign_stats = update_results(indicators, m, r, stat_query,
                                    "indicator_count", campaign_stats)
    campaign_stats = update_results(ips, m, r, stat_query,
                                    "ip_count", campaign_stats)
    campaign_stats = update_results(pcaps, m, r, stat_query,
                                    "pcap_count", campaign_stats)
    campaign_stats = update_results(samples, m, r, stat_query,
                                    "sample_count", campaign_stats)
    # update all of the campaigns here
    for campaign in campaign_stats.keys():
        campaigns.update({"name": campaign},
                         {"$set": campaign_stats[campaign]}, upsert=True)

def generate_counts():
    """
    Generate dashboard counts.
    """

    counts = mongo_connector(settings.COL_COUNTS)
    samples = mongo_connector(settings.COL_SAMPLES)
    emails = mongo_connector(settings.COL_EMAIL)
    indicators = mongo_connector(settings.COL_INDICATORS)
    domains = mongo_connector(settings.COL_DOMAINS)
    pcaps = mongo_connector(settings.COL_PCAPS)
    today = datetime.datetime.fromordinal(datetime.datetime.now().toordinal())
    start = datetime.datetime.now()
    last_seven = start - datetime.timedelta(7)
    last_thirty = start - datetime.timedelta(30)
    count = {}
    count['Samples'] = samples.find().count()
    count['Emails'] = emails.find().count()
    count['Indicators'] = indicators.find().count()
    count['PCAPs'] = pcaps.find().count()
    count['Domains'] = domains.find().count()
    count['Emails Today'] = emails.find({"source.instances.date": {"$gte": today}}).count()
    count['Emails Last 7'] = emails.find({'source.instances.date': {'$gte': last_seven}}).count()
    count['Emails Last 30'] = emails.find({'source.instances.date': {'$gte': last_thirty}}).count()
    count['Indicators Today'] = indicators.find({"source.instances.date": {"$gte": today}}).count()
    count['Indicators Last 7'] = indicators.find({"source.instances.date": {"$gte": last_seven}}).count()
    count['Indicators Last 30'] = indicators.find({"source.instances.date": {"$gte": last_thirty}}).count()
    counts.update({'name': "counts"}, {'$set': {'counts': count}}, upsert=True)


def target_user_stats():
    """
    Generate targets from email To/CC fields, then generate divisions from
    targets list.
    No cleanup or logic is being done on the To/CC fields. If they are not
    valid email addresses (user@domain), they do not get added as a target.
    """

    mapcode = """
        function () {
            try {
                this.to.forEach(function(z) {
                    emit(z.toLowerCase(), {count: 1});
                });
            } catch(err) {}
        }
    """
    reducecode = """
        function(k,v) {
            var count = 0;
            v.forEach(function(v) {
                count += v["count"];
            });
            return {count: count};
        }
    """
    m = Code(mapcode)
    r = Code(reducecode)
    results = Email.objects(to__exists=True).map_reduce(m, r, 'inline')
    for result in results:
        try:
            targs = Target.objects(email_address__iexact=result.key)
            if not targs:
                targs = [Target()]
                targs[0].email_address = result.key.strip().lower()

            for targ in targs:
                targ.email_count = result.value['count']
                targ.save()
        except:
            pass
    mapcode = """
        function() {
            if ("division" in this) {
                emit(this.division, {count: this.email_count})
            }
        }
    """
    m = Code(mapcode)
    try:
        results = Target.objects().map_reduce(m, r, 'inline')
        for result in results:
            div = Division.objects(division__iexact=result.key).first()
            if not div:
                div = Division()
                div.division = result.key
            div.email_count = result.value['count']
            div.save()
    except:
        raise


def campaign_date_stats():
    """
    Generate Campaign date stats.
    """

    emails = mongo_connector(settings.COL_EMAIL)
    mapcode = """
            function () {
                    try {
                    if ("campaign" in this) {
                        stats = {};
                        if ("isodate" in this) {
                            var d = new Date(this.isodate);
                            stats[new Date(d.getFullYear(), d.getMonth()).getTime()] = 1;
                        }
                        else {
                            stats[new Date(this.source[0].instances[0].date.getFullYear(), this.source[0].instances[0].date.getMonth()).getTime()] = 1;
                        }
                        emit({campaign:this.campaign[0].name}, stats);
                    } }
                    catch (err) {}
            }
    """
    reducecode = """
            function reduce(key, values) {
              var out = {};
              function merge(a, b) {
                for (var k in b) {
                  if (!b.hasOwnProperty(k)) {
                    continue;
                  }
                  a[k] = (a[k] || 0) + b[k];
                }
              }
              for (var i=0; i < values.length; i++) {
                merge(out, values[i]);
              }
              return out;
            }
    """
    m = Code(mapcode, {})
    r = Code(reducecode, {})
    results = emails.inline_map_reduce(m, r)
    stat_coll = mongo_connector(settings.COL_STATISTICS)
    stats = {}
    stats["results"] = []
    for result in results:
        stats["results"].append({
        "campaign": result["_id"]["campaign"],
        "value": result["value"]
        })
    stat_coll.update({'name': 'campaign_monthly'}, {"$set": stats},
                     upsert=True)
