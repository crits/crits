def migrate_signature(self):
    """
    Migrate to the latest schema version.
    """

    migrate_1_to_2(self)

def migrate_1_to_2(self):
    """
    Migrate from schema 1 to 2.
    """
    from crits.core.core_migrate import migrate_relationships
    
    if self.schema_version < 1:
        pass
    
    if self.schema_version == 1:
        migrate_relationships(self)
        self.schema_version = 2
        self.save()
        self.reload()