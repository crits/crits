from crits.vocabulary.relationships import RelationshipTypes

def migrate_backdoors(self):
    """
    Create backdoor objects from backdoors on samples.
    """

    if not self.unsupported_attrs:
        return

    if 'backdoor' not in self.unsupported_attrs:
        return

    print "Migrating backdoor for %s" % self.id

    from crits.backdoors.handlers import add_new_backdoor
    backdoor = self.unsupported_attrs['backdoor']
    name = backdoor.get('name', '')
    version = backdoor.get('version', None)
    if not name:
        return

    # Create a new backdoor family, and if we have a version the more specific
    # backdoor will be created too. Use source and campaign of the current
    # Sample.
    result = add_new_backdoor(name,
                              version=version,
                              source=self.source,
                              campaign=self.campaign)
    if result['success']:
        self.add_relationship(result['object'],
                              RelationshipTypes.RELATED_TO,
                              rel_reason="Migrated")
        # Save the object after relationship was created.
        self.save()
    else:
        print "Error migrating %s: %s" % (self.id, result['message'])

def migrate_exploits(self):
    """
    Create exploit objects from exploits on samples.
    """

    if not self.unsupported_attrs:
        return

    if 'exploit' not in self.unsupported_attrs:
        return

    from crits.exploits.handlers import add_new_exploit
    exploits = self.unsupported_attrs['exploit']
    for exp in exploits:
        print "Migrating exploit for %s" % self.id

        # Create a new exploit object. Use the source and campaign from the
        # current sample. The "old" exploit format was a list of dictionaries
        # with the key of "cve" and a value that we will use for name and CVE.
        result = add_new_exploit(exp['cve'],
                                 cve=exp['cve'],
                                 source=self.source,
                                 campaign=self.campaign)
        if result['success']:
            self.add_relationship(result['object'],
                                  RelationshipTypes.RELATED_TO,
                                  rel_reason="Migrated")
            # Save the object after relationship was created.
            self.save()
        else:
            print "Error migrating %s: %s" % (self.id, result['message'])



def migrate_sample(self):
    """
    Migrate to the latest schema version.
    """

    migrate_3_to_4(self)

def migrate_3_to_4(self):
    """
    Migrate from schema 3 to 4.
    """

    if self.schema_version < 3:
        migrate_2_to_3(self)

    if self.schema_version == 3:
        migrate_backdoors(self)
        migrate_exploits(self)
        self.schema_version = 4
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
        self.discover_binary()
        self.schema_version = 2

def migrate_0_to_1(self):
    """
    Migrate from schema 0 to 1.
    """

    if self.schema_version < 1:
        self.schema_version = 1
