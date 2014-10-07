import uuid

def migrate_event(self):
    """
    Migrate to the latest schema version.
    """

    migrate_2_to_3(self)

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
        self.save()
        self.reload()

def migrate_1_to_2(self):
    """
    Migrate from schema 1 to 2.
    """

    if self.schema_version < 1:
        migrate_0_to_1(self)

    if self.schema_version == 1:
        event_id = self.event_id
        if not isinstance(event_id, uuid.UUID):
            if not isinstance(event_id, basestring):
                event_id = str(event_id)
            try:
                event_id = uuid.UUID(event_id)
            except ValueError:
                event_id = uuid.uuid4()
            self.event_id = event_id
        self.schema_version = 2

def migrate_0_to_1(self):
    """
    Migrate from schema 0 to 1.
    """

    if self.schema_version < 1:
        self.schema_version = 1
