def migrate_raw_data(self):
    """
    Migrate to the latest schema version.
    """

    migrate_2_to_3(self)

def migrate_2_to_3(self):
    """
    Migrate from schema 3 to 4.
    """
    from crits.core.core_migrate import migrate_relationships
    
    if self.schema_version < 2:
        migrate_1_to_2(self)
    
    if self.schema_version == 2:
        migrate_relationships(self)
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
        from crits.core.core_migrate import migrate_analysis_results
        migrate_analysis_results(self)
        self.schema_version = 2
        self.save()
        self.reload()

def migrate_0_to_1(self):
    """
    Migrate from schema 0 to 1.
    """

    if self.schema_version < 1:
        self.schema_version = 1
