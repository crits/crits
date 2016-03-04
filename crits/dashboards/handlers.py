"""
This File will often refer to 'default dashboard tables.' They currently are:
Counts, Top Campaigns, Recent Indicators, Recent Emails, and
Recent Samples in that order. The user has the ability to change they're 
positioning, size, columns, and sort order but they are always there and their 
names cannot be changed.
"""
from crits.dashboards.dashboard import SavedSearch, Dashboard
from crits.core.crits_mongoengine import json_handler
from mongoengine import Q
from django.core.urlresolvers import reverse
from crits.campaigns.campaign import Campaign
from crits.indicators.indicator import Indicator
from crits.emails.email import Email
from crits.samples.sample import Sample
from django.http import HttpResponse
import json
from django.utils.html import escape as html_escape
import cgi
import datetime
from django.http import HttpRequest
from crits.dashboards.utilities import getHREFLink, get_obj_name_from_title, get_obj_type_from_string
import HTMLParser

def get_dashboard(user,dashId=None):
    """
    Gets a specific dashbaord for the user. If dashId is provided it looks it up.
    If dashId is not provided or the dashboard does not exist, it gets the user's
    default dashboard. If that dashboard does not exist, it first looks for a 
    user-modified child of the public Default dashboard. Finally it will retrieve 
    the public default dashboard if no others exist.
    """
    dashboard = None
    if dashId:
        dashboard = Dashboard.objects(id=dashId).first()
        if not dashboard:
            return {'success': False,
                'message': "The dashboard you selected no longer exists."}
    elif user.defaultDashboard:
        try:
            dashboard = Dashboard.objects(id=user.defaultDashboard).first()
        except:
            user.defaultDashboard = None
            user.save()
    if not dashboard:
        dashboard = Dashboard.objects(name="Default", analystId__not__exists=1, isPublic=True).first()
        cloneOfDefault = Dashboard.objects(parent=dashboard.id, analystId=user.id).first()
        if cloneOfDefault:
            dashboard = cloneOfDefault
    dashId = dashboard.id
    tables = []
    savedTables = SavedSearch.objects(dashboard=dashId, isPinned=True)
    for table in savedTables:
        tables.append(createTableObject(user, table=table))
    otherDashboardIds = []
    otherDashboards = {}
    for dash in Dashboard.objects(id__ne=dashId, analystId=user.id):
        otherDashboardIds.append(dash.id)
        otherDashboards[dash.id] = dash.name
    otherSearches = []
    for search in SavedSearch.objects(dashboard__in=otherDashboardIds, isPinned=True) :
        otherSearches.append({
                        "id":search.id,
                        "dash":otherDashboards[search.dashboard],
                        "name":search.name
                        })
    return {"success": True,
            "tables": tables,
            "dashboards": getDashboardsForUser(user),
            "currentDash": str(dashId),
            'parentHasChanged':dashboard.hasParentChanged,
            'parent':dashboard.parent,
            'dashTheme':dashboard.theme,
            "otherSearches":otherSearches,
            "userId": dashboard.analystId}
    
def createTableObject(user, title="", table=None):
    """
    Parent method in creating the table object, called by get_dashboard 
    for each table
    """
    if table.isDefaultOnDashboard:
        records = getRecordsForDefaultDashboardTable(user.username, table.name)
    else:  #the only time table does not exist is if its a default table
        response = get_table_data(obj=table.objType, user=user, 
                                  searchTerm=table.searchTerm, search_type="global", 
                                  maxRows=table.maxRows, sort=table.sortBy)
        #records to be inserted in the table
        records = response["Records"]
        for record in records:
            if "thumb" in record:
                record["thumb"] = "<img class='screenshotImg' src='"+record["url"]+"thumb/' />"
    return constructSavedTable(table, records)
    
def getRecordsForDefaultDashboardTable(username, tableName):
    """
    Called by createTableObject to retrieve the proper records from the
    database for the default dashboard tables. These queries are different then 
    the saved searches which is why it is needed.
    
    This is also called via ajax on the saved_search.html page by 
    get_dashboard_table_data in Views.py. This is to get the records when 
    editing the default tables.
    """
    from crits.core.handlers import data_query, generate_counts_jtable
    
    if tableName == "Recent_Samples" or tableName == "Recent Samples":
        obj_type = "Sample"
        response = data_query(Sample, username, query={}, sort=["-created"], limit=5)
    elif tableName == "Recent_Emails" or tableName == "Recent Emails":
        obj_type = "Email"
        response = data_query(Email, username, query={}, sort=["-isodate"], limit=5)
    elif tableName == "Recent_Indicators" or tableName == "Recent Indicators":
        obj_type = "Indicator"
        response = data_query(Indicator, username, query={}, sort=["-created"], limit=5)
    elif tableName == "Top_Campaigns" or tableName == "Top Campaigns":
        obj_type = "Campaign"
        response = data_query(Campaign, username, query={}, limit=5)
    elif tableName == "Counts":
        response = generate_counts_jtable(None, "jtlist")
        records = json.loads(response.content)["Records"]
        for record in records:
            record["recid"] = record.pop("id")
        return records
    else:
        # This only happens if we have a dashboard which is no longer valid.
        # For example, after Backdoor and Exploit were added the "Top_Backdoors"
        # dashboard is no longer valid. Produce an "empty" response.
        response = {'data': []}
        obj_type = None

    return parseDocumentsForW2ui(response, obj_type)

def constructSavedTable(table, records):
    """
    Creates all the needed parameters to be passed into constructTable.
    Called by createTableObject.
    """
    columns = []
    colNames = []
    for column in table.tableColumns:
        col = {}
        for k,v in column.iteritems():
            if k == "sizeCalculated" or k == "sizeCorrected" or k == 'min':
                continue
            elif k == "field":
                colNames.append(v)
            col[str(k)] = str(v)
        columns.append(col)
    return constructTable(table, records, columns, colNames)

def constructTable(table, records, columns, colNames):
    """
    Creates and returns the dict object representing the table. This is the
    final method called in the creation of a table and is used for both
    default and saved tables.
    """
    tableObject = {
        "title": table.name,
        "records": records,
        "columns": columns,
        "colNames": colNames,
        "id" : str(table.id),
        "searchTerm":table.searchTerm,
        "sortBy":table.sortBy,
        "maxRows":table.maxRows,
        "isHereByDefault":table.isDefaultOnDashboard,
        "sizex": table.sizex,
        "sizey": table.sizey,
        "row": table.row,
        "col": table.col
    }
    if table.objType:
        tableObject["objType"] = table.objType
        tableObject["url"] = reverse("crits.dashboards.views.load_data",
                                          kwargs={"obj":table.objType})
    return tableObject
    
def parseDocumentsForW2ui(response, obj_type):
    """
    called by getRecordsForDeafultDashboardTable in order to turn the BSON objects 
    into dictionaries and relpaces the _id field with recid - which is a 
    necessary thing for w2ui.
    """
    records = []
    #create a list of dicts
    for record in response["data"]:
        records.append(record.to_mongo())
    return parseDocObjectsToStrings(records, obj_type)

def parseDocObjectsToStrings(records, obj_type):
    """
    called by parseDocumentsForW2ui and get_table_data to convert some of 
    the objects in the record dictionaries into strings.
    For example converts the sources into their names instead of returning the
    entire object
    """
    for doc in records:
        for key, value in doc.items():
            # all dates should look the same
            if isinstance(value, datetime.datetime):
                doc[key] = datetime.datetime.strftime(value,
                                                      "%Y-%m-%d %H:%M:%S")
            if key == "_id" or key == "id":
                doc["recid"] = str(value)
                doc["details"] = "<a href='"+getHREFLink(doc, obj_type)+"'>"\
                    "<div class='icon-container'>"\
                        "<span class='ui-icon ui-icon-document'></span>"\
                    "</div>"\
                "</a>"
            elif key == "password_reset":
                doc['password_reset'] = None
            elif key == "campaign":
                camps = []
                for campdict in value:
                    camps.append(campdict['name'])
                doc[key] = "|||".join(camps)
            elif key == "source":
                srcs = []
                for srcdict in doc[key]:
                    srcs.append(srcdict['name'])
                doc[key] = "|||".join(srcs)
            elif key == "tags":
                tags = []
                for tag in doc[key]:
                    tags.append(tag)
                doc[key] = "|||".join(tags)
            elif key == "is_active":
                if value:
                    doc[key] = "True"
                else:
                    doc[key] = "False"
            elif key == "tickets":
                tickets = []
                for ticketdict in value:
                    tickets.append(ticketdict['ticket_number'])
                doc[key] = "|||".join(tickets)
            elif key == "datatype":
                doc[key] = value.keys()[0]
            elif key == "to":
                doc[key] = len(value)
            elif key == "thumb":
                doc['url'] = reverse("crits.screenshots.views.render_screenshot",
                                      args=(unicode(doc["_id"]),))
            elif key=="results" and obj_type == "AnalysisResult":
                doc[key] = len(value)
            elif isinstance(value, list):
                if value:
                    for item in value:
                        if not isinstance(item, basestring):
                            break
                    else:
                        doc[key] = ",".join(value)
                else:
                    doc[key] = ""
            doc[key] = html_escape(doc[key])
            value = doc[key].strip()
            if isinstance(value, unicode) or isinstance(value, str):
                val = ' '.join(value.split())
                val = val.replace('"',"'")
                doc[key] = val
    return records

def save_data(userId, columns, tableName, searchTerm="", objType="", sortBy=None, 
              tableId=None, isDefaultOnDashboard=False, maxRows=0,
              dashboard=None, clone=False, row=0, grid_col=0, sizex=0,
              sizey=0):
    """
    Saves the customized table in the dashboard. Called by save_search and
    save_new_dashboard via ajax in views.py.
    """
    try:
        if searchTerm:
            searchTerm = HTMLParser.HTMLParser().unescape(searchTerm)
        #if user is editing a table
        if tableId :
            newSavedSearch = SavedSearch.objects(id=tableId).first()
            if not newSavedSearch:
                raise Exception("Cannot find Table")
            elif clone:
                clonedSavedSearch = cloneSavedSearch(newSavedSearch, dashboard.id)
        else:
            newSavedSearch = SavedSearch()
        cols = []
        for col in columns:
            if "field" not in col or "caption" not in col:
                continue
            cols.append(col)
        if not cols:
            raise("There are no columns to save")
        newSavedSearch.tableColumns = cols
        newSavedSearch.name = tableName
        oldDashId = None
        if dashboard and newSavedSearch.dashboard != dashboard.id:
            newSavedSearch.dashboard= dashboard.id
        #if it is not a deault dashboard table, it must have a searchterm and objtype
        if searchTerm:
            newSavedSearch.searchTerm = searchTerm
        if objType:
            newSavedSearch.objType = objType
        #this is to identify the default tables on every user dashboard
        newSavedSearch.isDefaultOnDashboard = isDefaultOnDashboard
        if sortBy:
            newSavedSearch.sortBy = sortBy
        if sizex:
            newSavedSearch.sizex = sizex
        elif not newSavedSearch.sizex:
            newSavedSearch.sizex = 50
        if sizey:
            newSavedSearch.sizey = sizey
        elif maxRows and maxRows != newSavedSearch.maxRows:
            newSavedSearch.sizey = int(maxRows)+1
        elif not newSavedSearch.sizey:
            newSavedSearch.sizey = 7
        if row:
            newSavedSearch.row = row
        elif not newSavedSearch.row:
            newSavedSearch.row = 1
        if grid_col:
            newSavedSearch.col = grid_col
        elif not newSavedSearch.col:
            newSavedSearch.col = 1
        if maxRows:
            newSavedSearch.maxRows = maxRows;
        newSavedSearch.save()
        #if the old dashboard is empty, delete it
        if oldDashId:
            deleteDashboardIfEmpty(oldDashId)
    except Exception as e:
        print "ERROR: "
        print e
        return {'success': False,
                'message': "An unexpected error occurred while saving table. Please refresh and try again"}
    return {'success': True,'message': tableName+" Saved Successfully!"}

def clear_dashboard(dashId):
    """
    Clears all the set positions and sizes of the tables on the dashboard
    """
    default_tables = {
                        "Counts": {
                            "sizex": 10,
                            "sizey": 13,
                            "row": 1,
                            "col": 1
                        },
                        "Top Campaigns": {
                            "sizex": 25,
                            "sizey": 8,
                            "row": 1,
                            "col": 20
                        },
                        "Recent Indicators": {
                            "sizex": 50,
                            "sizey": 8,
                            "row": 15,
                            "col": 1
                        },
                        "Recent Emails": {
                            "sizex": 50,
                            "sizey": 8,
                            "row": 23,
                            "col": 1
                        },
                        "Recent Samples": {
                            "sizex": 50,
                            "sizey": 8,
                            "row": 31,
                            "col": 1
                        },
                      }
    try:
        for search in SavedSearch.objects(dashboard=dashId):
            if search.isDefaultOnDashboard:
                tempDict = default_tables[search.name]
                search.sizex = tempDict["sizex"]
                search.sizey = tempDict["sizey"]
                search.row = tempDict["row"]
                search.col = tempDict["col"]
                search.save()
            else:
                search.update(unset__col=1,unset__row=1,unset__sizex=1)
    except Exception as e:
        print e
        return {'success': False, 
                'message': "An unexpected error occurred while resetting dash. Please refresh and try again"}
    return {'success': True, 
            'message': "Dashboard Reset"}

def delete_table(userId, id):
    """
    Deletes a table from the db. Only can be called via the saved_search.html
    """
    try:
        savedSearch = SavedSearch.objects(id=id).first()
        tableName = savedSearch.name
        doDelete = True
        message = tableName+" deleted successfully!"
        if savedSearch.isDefaultOnDashboard:
            dashboards = []
            for dash in Dashboard.objects(analystId=userId):
                dashboards.append(dash.id)
            if SavedSearch.objects(dashboard__in=dashboards, isDefaultOnDashboard=True, name=tableName).count() == 1:
                savedSearch.col = 1
                savedSearch.row = 1
                savedSearch.isPinned = False
                savedSearch.save()
                doDelete = False
                message = tableName+" is now hidden."
        if doDelete:
            dashId = savedSearch.dashboard
            savedSearch.delete()
            deleteDashboardIfEmpty(dashId)
    except Exception as e:
        print e
        return {'success': False,
                'message': "Search could not be found. Please refresh and try again."}
    return {'success': True,'message': message, 'wasDeleted': doDelete}

def get_table_data(request=None,obj=None,user=None,searchTerm="",
                   search_type=None, includes=[], excludes=[], maxRows=25, 
                   sort={}, pageNumber=1):
    """
    gets the records needed for the table, can be called via ajax on the 
    saved_search.html or the above ConstructTable function
    """
    from crits.core.handlers import get_query, data_query
    response = {"Result": "ERROR"}
    obj_type = get_obj_type_from_string(obj)
    # Build the query
    term = ""
    #if its being called from saved_search.html
    if request and request.is_ajax():
        resp = get_query(obj_type, request)
    #if its calling to get data for the dashbaord
    elif user and search_type:
        resp = get_query_without_request(obj_type, user.username, searchTerm, search_type)
    else:
        return HttpResponse(json.dumps(response, default=json_handler),
                             content_type="application/json")
    if resp['Result'] in ["ERROR", "IGNORE"]:
        return resp
    query = resp['query']
    term = resp['term']
    sortBy = []
    if 'direction' in sort:
        if sort['direction'] == 'asc':
            sortBy.append(sort['field'])
        elif sort['direction'] == 'desc':
            sortBy.append("-"+sort['field'])
    skip = (int(pageNumber)-1)*25
    if request:
        response = data_query(obj_type, user=request.user.username, query=query,
                          projection=includes, limit=int(maxRows), sort=sortBy, skip=skip)
    else:
        response = data_query(obj_type, user=user.username, query=query,
                          projection=includes, limit=maxRows, sort=sortBy,skip=skip)
    if response['result'] == "ERROR":
        return {'Result': "ERROR", 'Message': response['msg']}
    response['crits_type'] = obj_type
    # Escape term for rendering in the UI.
    response['term'] = cgi.escape(term)
    response['data'] = response['data'].to_dict(excludes, includes)
    response['Records'] = parseDocObjectsToStrings(response.pop('data'), obj)
    response['TotalRecordCount'] = response.pop('count')
    response['Result'] = response.pop('result')
    if request:
        return HttpResponse(json.dumps(response, default=json_handler),
                             content_type="application/json")
    else:
        return response

def get_query_without_request(obj_type, username, searchTerm, search_type="global"):
    """
    Builds the query without the request, very similar to the 
    get_query method in the core of crits
    """
    from crits.core.handlers import gen_global_query
    
    query = {}
    response = {}
    qdict = gen_global_query(obj_type, username, searchTerm, search_type, force_full=False)
    if not qdict.get('success', True):
        if qdict.get('ignore', False):
            response['Result'] = "IGNORE"
        else:
            response['Result'] = "ERROR"
        response['Message'] = qdict.get('error', 'Unable to process query')
        return response
    query.update(qdict)
    results = {}
    results['Result'] = "OK"
    results['query'] = query
    results['term'] = searchTerm
    return results
    
def generate_search_for_saved_table(user, id=None,request=None):
    """
    Called by edit_save_search in views.py. This is for editing a previously
    saved table or one of the default dashboard tables
    """
    from crits.core.handlers import data_query
    response = {}
    savedSearch = None
    try:
        savedSearch = SavedSearch.objects(id=id).first()
        if not savedSearch:
            response['Result'] = "ERROR"
            response['Message'] = "Error finding table, please try again later."
            return response
    except:
        savedSearch = SavedSearch()
        savedSearch.isDefaultOnDashboard = True
        savedSearch.name = id.replace("_", " ")
        id = None
    results = []
    records = []
    term = ""
    url = ""
    if not savedSearch.isDefaultOnDashboard:
        objType = get_obj_type_from_string(savedSearch.objType)
        resp = get_query_without_request(objType, user.username, savedSearch.searchTerm, "global")
        if resp['Result'] == "ERROR":
            return resp
        formatted_query = resp['query']
        term = resp['term']
        resp = data_query(objType, user.username, query=formatted_query, count=True)
        results.append({'count': resp['count'],
                                      'name': savedSearch.objType}) 
    else:
        results = {"name":savedSearch.name,
                   "count":str(len(records)),
                   "type":get_obj_name_from_title(savedSearch.name)}
        #special url to get the records of a default dashboard since their queries are different 
        url = reverse("crits.dashboards.views.get_dashboard_table_data", 
                      kwargs={"tableName":str(savedSearch.name.replace(" ", "_"))})
    args = {'term': term,
            'results': results,
            'dataUrl':url,
            'Result': "OK"
            }
    if savedSearch:
        args.update({'tableId':id,
                'tableName': savedSearch.name,
                'columns': savedSearch.tableColumns,
                'sortBy': savedSearch.sortBy,
                'sizex' : savedSearch.sizex,
                'maxRows': savedSearch.maxRows,
                'isDefaultOnDashboard': savedSearch.isDefaultOnDashboard,
                })
        if savedSearch.dashboard:
            args["currentDash"] = str(savedSearch.dashboard)
            args["dashtheme"] = Dashboard.objects(id=savedSearch.dashboard).first().theme
    return args
    
def toggleTableVisibility(id, isVisible):
    """
    Changes the tables visibility to either pinned or hidden.
    """
    table = SavedSearch.objects(id=id).first()
    if not table:
        return {'success': False,
                'message': "Error finding table. Please refresh and try again"}
    message = table.name+ " is now "
    if isVisible:
        message += "visible"
    else:
        message += "hidden"
    table.isPinned = isVisible
    table.save()
    return {'success': True,'message': message}
    
def get_saved_searches_list(user):
    """
    Returns all user dashboards and their affiliated saved searches.
    """
    dashboards = []
    for dash in Dashboard.objects(analystId=user.id):
        tables = []
        for table in SavedSearch.objects(dashboard=dash.id):
            if table.isDefaultOnDashboard:
                table.searchTerm = ""
                table.objType = ""
            tables.append(table)
        tempDash = {
                    "name":dash.name,
                   "id": dash.id,
                   "theme":dash.theme,
                   'isPublic':dash.isPublic,
                   "tables": tables
                }
        if dash.parent:
            tempDash['isModified'] = True
        dashboards.append(tempDash)
            
    return {"dashboards": dashboards}
    

    
def deleteDashboardIfEmpty(dashId):
    """
    Checks if a dashboard has saved searches. Deletes it if it doesn't.
    """
    if not SavedSearch.objects(dashboard=dashId):
        Dashboard.objects(id=dashId).delete()
    
def createNewDashboard(userId, name):
    """
    Creates a new dashboard for the user
    """
    if Dashboard.objects(analystId=userId,name=name):
        return
    newDash = Dashboard()
    newDash.name = name
    newDash.analystId = userId
    newDash.save()
    return newDash

def setDefaultDashboard(user, dashId):
    """
    Sets the users default dashboard
    """
    try:
        name = Dashboard.objects(id=dashId).first().name
        user.defaultDashboard = dashId
        user.save()
        return name
    except:
        return False
    
def cloneDashboard(userId, dashboard, cloneSearches=False, skip=None):
    """
    Clones a public dashboard to a user-modified version of if.
    cloneSearches will clone all affiliated searches with the dashboard.
    Skip will skip a specific table if cloning searches
    """
    if Dashboard.objects(analystId=userId,name=dashboard.name):
        return
    newDash = Dashboard()
    newDash.name = dashboard.name
    newDash.theme = dashboard.theme
    newDash.analystId = userId
    newDash.parent = dashboard.id
    newDash.save()
    if cloneSearches:
        for search in SavedSearch.objects(dashboard = dashboard.id):
            if skip != str(search.id):
                cloneSavedSearch(search, newDash.id)
    return newDash

def cloneSavedSearch(savedSearch, dashId):
    """
    Clones the saved search and returns result
    """
    clonedSavedSearch = savedSearch
    clonedSavedSearch.id = None
    clonedSavedSearch.dashboard = dashId
    clonedSavedSearch.save()
    return clonedSavedSearch

def getDashboardsForUser(user):
    """
    Gets all the users dashboards and public dashboards. It will then remove 
    all public dashboards that have been cloned by the user
    """
    dashboards = Dashboard.objects(Q(analystId=user.id) | Q(isPublic=True))
    parents = []
    userDashboards = []
    #get all id's of parent dashboards
    for dash in dashboards:
        if dash.parent:
            parents.append(dash.parent)
    #remove any parent from the list to prevent duplicate dashboards
    for dash in dashboards:
        if not dash.id in parents:
            userDashboards.append(dash)
    return userDashboards


def setPublic(id, makePublic):
    """
    Sets the dashboards visibility to public or private
    """
    try:
        dashboard = Dashboard.objects(id=id).first()
        if makePublic and Dashboard.objects(name=dashboard.name, isPublic=True):
            return "There already exists a public dashboard with that name. "\
                "You must rename your dashboard before making it public."
        Dashboard.objects(id=id).update(set__isPublic=makePublic)
        #if making a dashboard private, clear all parent-child relationships
        if not makePublic:
            updateChildren(id, deletingParent=True)
        else:#if making public, remove parent
            Dashboard.objects(id=id).update(unset__parent=1)
    except Exception as e:
        print e
        return "An error occured while updating table. Please try again later."
    return True

def updateChildren(parentId, deletingParent=False):
    """
    Sets field 'hasParentChanged' to true on all dashboards that are clones of 
    the changing dashboard.
    If the dashboard is being deleted(or private) then it unsets the parent field.
    """
    Dashboard.objects(parent=parentId).update(set__hasParentChanged=True)
    if deletingParent:
        Dashboard.objects(parent=parentId).update(unset__parent=1)

def deleteDashboard(id):
    """
    Deletes the dashboard with the given id and updates clones of it.
    Also deletes all saved searches affiliated with it
    """
    try:
        dashboard = Dashboard.objects(id=id).first()
        name = dashboard.name
        if dashboard.isPublic:
            updateChildren(id, deletingParent=True)
        SavedSearch.objects(dashboard=id).delete()
        Dashboard.objects(id=id).delete()
    except Exception as e:
        print e
        return False
    return name

def renameDashboard(id, name, userId):
    """
    Renames the given dashboard
    """
    if not name:
        return "You must give a name to the dashboard."
    if Dashboard.objects(name=name, analystId=userId):
        return "You already have a dashboard with that name."
    Dashboard.objects(id=id).update(set__name=name)
    return True

def changeTheme(id, theme):
    """
    Changes theme of the dashboard. 
    CURRENTLY UNUSED.
    """
    try:
        Dashboard.objects(id=id).update(set__theme=theme)
    except Exception as e:
        print e
        return False
    return "Dashboard updated successfully."
    
def add_existing_search_to_dashboard(id, dashboard, user):
    search = SavedSearch.objects(id = id).first()
    if not search:
        return {"success":False,
                "message":"Could not find search. Please refresh and try again."}
    else:
        search = cloneSavedSearch(search, dashboard)
        return {"success":True,
                "message": search.name+" has been added to your dashboard.",
                "newSearch": createTableObject(user, table=search)}

def switch_existing_search_to_dashboard(id, dashboard):
    if SavedSearch.objects(id=id).update(set__dashboard=dashboard) == 1:
        return {"success":True,
                "message": "Search Switched Sucessfully"}
    return {"success":False,
            "message": "Could not find search. Please refresh and try again."}
