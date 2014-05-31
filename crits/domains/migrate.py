def migrate_domain(self):
    """
    Migrate to latest schema.
    """

    migrate_0_to_1(self)

def migrate_0_to_1(self):
    """
    Migrate from schema 0 to 1.
    """

    if self.schema_version < 1:
        self.schema_version = 1
        self.save()
        self.reload()
