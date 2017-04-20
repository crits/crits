from crits.core.crits_mongoengine import EmbeddedCampaign
from crits.vocabulary.indicators import (
    IndicatorThreatTypes,
    IndicatorAttackTypes
)

def migrate_indicator(self):
    """
    Migrate to the latest schema version.
    """

    migrate_4_to_5(self)

def migrate_4_to_5(self):
    """
    Migrate from schema 4 to 5.
    """

    if self.schema_version < 4:
        migrate_3_to_4(self)

    if self.schema_version == 4:
        old_threat_type = getattr(self.unsupported_attrs, 'threat_type', None)
        old_attack_type = getattr(self.unsupported_attrs, 'attack_type', None)
        if old_threat_type is None:
            old_threat_type = IndicatorThreatTypes.UNKNOWN
        if old_attack_type is None:
            old_attack_type = IndicatorAttackTypes.UNKNOWN
        self.threat_types = [old_threat_type]
        self.attack_types = [old_attack_type]
        self.schema_version = 5
        self.save()
        self.reload()

def migrate_3_to_4(self):
    """
    Migrate from schema 3 to 4.
    """

    if self.schema_version < 3:
        migrate_2_to_3(self)

    if self.schema_version == 3:
        self.schema_version = 4
        self.lower = self.value.lower()
        self.save()
        self.reload()

def migrate_2_to_3(self):
    """
    Migrate from schema 2 to 3.
    """

    if self.schema_version < 2:
        migrate_1_to_2(self)

    if self.schema_version == 2:
        from crits.core.core_migrate import migrate_analysis_results
        migrate_analysis_results(self)
        self.schema_version = 3

def migrate_1_to_2(self):
    """
    Migrate from schema 1 to 2.
    """

    if self.schema_version < 1:
        migrate_0_to_1(self)

    if self.schema_version == 1:
        old_analysis = getattr(self.unsupported_attrs, 'old_analysis', None)
        self.activity = []
        self.campaign = []
        if old_analysis:
            # activity
            if 'activity' in old_analysis:
                for a in old_analysis['activity']:
                    (analyst, description) = ('', '')
                    (date, start_date, end_date) = (None, None, None)
                    if 'analyst' in a:
                        analyst = a['analyst']
                    if 'description' in a:
                        description = a['description']
                    if 'date' in a:
                        date = a['date']
                    if 'start_date' in a:
                        start_date = a['start_date']
                    if 'end_date' in a:
                        end_date = a['end_date']
                    self.add_activity(
                        analyst=analyst,
                        start_date=start_date,
                        end_date=end_date,
                        date=date,
                        description=description
                    )
            # campaign
            if 'campaign' in old_analysis:
                for c in old_analysis['campaign']:
                    (analyst, description) = ('', '')
                    (date, confidence, name) = (None, 'low', '')
                    if not 'analyst' in c:
                        c['analyst'] = analyst
                    if not 'description' in c:
                        c['description'] = description
                    if not 'date' in c:
                        c['date'] = date
                    if not 'confidence' in c:
                        c['confidence'] = confidence
                    if not 'name' in c:
                        c['name'] = name
                    ec = EmbeddedCampaign(
                        analyst=c['analyst'],
                        description=c['description'],
                        date=c['date'],
                        confidence=c['confidence'],
                        name=c['name']
                    )
                    self.add_campaign(ec)
            # confidence
            if 'confidence' in old_analysis:
                confidence = old_analysis['confidence']
                (analyst, rating) = ('', 'unknown')
                if 'analyst' in confidence:
                    analyst = confidence['analyst']
                if 'rating' in confidence:
                    rating = confidence['rating']
                self.set_confidence(analyst=analyst, rating=rating)
            # impact
            if 'impact' in old_analysis:
                impact = old_analysis['impact']
                (analyst, rating) = ('', 'unknown')
                if 'analyst' in impact:
                    analyst = impact['analyst']
                if 'rating' in impact:
                    rating = impact['rating']
                self.set_impact(analyst=analyst, rating=rating)
        self.schema_version = 2

def migrate_0_to_1(self):
    """
    Migrate from schema 0 to 1.
    """

    if self.schema_version < 1:
        self.schema_version = 1
