def migrate_user(self):
    """
    Migrate to latest schema version.
    """

    migrate_1_to_2(self)
    migrate_2_to_3(self)

def migrate_1_to_2(self):
    """
    Migrate from schema 1 to schema 2.
    """

    if self.schema_version == 1:
        self.schema_version = 2

        notify_email = getattr(self.unsupported_attrs, 'email_notifications', False)
        theme = getattr(self.unsupported_attrs, 'theme', 'default')
        pagesize = getattr(self.unsupported_attrs, 'jtable_list_size', 25)

        for k in ('email_notifications', 'theme', 'jtable_list_size'):
            setattr(self.unsupported_attrs, k, None)

        setattr(self.prefs, 'ui', {'theme': theme, 'table_page_size': pagesize})
        setattr(self.prefs,'notify', {'email': notify_email})

        self.save()
        self.reload()

def migrate_2_to_3(self):
    """
    Migrate from schema 2 to schema 3.
    """

    if self.schema_version == 2:
        self.schema_version = 3

        self.favorites['Backdoor'] = []
        self.favorites['Exploit'] = []

        self.save()
        self.reload()

