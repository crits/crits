def migrate_campaign(self):
    """
    Latest migration.
    """

    migrate_3_to_4(self)

def migrate_3_to_4(self):
    """
    Migrate from schema 3 to 4.
    """
    from crits.core.core_migrate import migrate_relationships

    if self.schema_version < 3:
        migrate_2_to_3(self)
    
    if self.schema_version == 3:
        migrate_relationships(self)
        self.schema_version = 4
        self.save()
        self.reload()

def migrate_1_to_2(self):
    """
    Migrate from schema 1 to 2.
    """

    if self.schema_version < 1:
        migrate_0_to_1(self)

    if self.schema_version == 1:
        self.schema_version = 2

def migrate_0_to_1(self):
    """
    Migrate from schema 0 to 1.
    """

    if self.schema_version < 1:
        self.schema_version = 1
