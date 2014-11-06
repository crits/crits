from django.core.management.base import BaseCommand

from crits.core.crits_mongoengine import RelationshipType

class Command(BaseCommand):
    """
    Script Class.
    """

    help = 'Creates relationship types in MongoDB.'

    def handle(self, *args, **options):
        """
        Script Execution.
        """

        add_relationship_types(True)

def add_relationship_types(drop=False):
    """
    Add Relationship Types to the system.

    :param drop: Drop collection before adding.
    :type drop: boolean
    """

    types = [
        ("Allocated", "Allocated_By"),
        ("Bound", "Bound_By"),
        ("Closed", "Closed_By"),
        ("Compressed", "Compressed_By"),
        ("Compressed_From", "Compressed_Into"),
        ("Connected_From", "Connected_To"),
        ("Contains", "Contained_Within"),
        ("Copied", "Copied_By"),
        ("Copied_From", "Copied_To"),
        ("Created", "Created_By"),
        ("Decoded", "Decoded_By"),
        ("Decompressed", "Decompressed_By"),
        ("Decrypted", "Decrypted_By"),
        ("Deleted", "Deleted_By"),
        ("Deleted_From","Previously_Contained"),
        ("Downloaded", "Downloaded_By"),
        ("Downloaded_From", "Downloaded_To"),
        ("Dropped", "Dropped_By"),
        ("Encoded", "Encoded_By"),
        ("Encrypted", "Encrypted_By"),
        ("Encrypted_From", "Encrypted_To"),
        ("Extracted_From","Contains"),
        ("Freed", "Freed_By"),
        ("Hooked", "Hooked_By"),
        ("Initialized_To", "Initialized_By"),
        ("Injected", "Injected_By"),
        ("Injected_Into", "Injected_As"),
        ("Installed", "Installed_By"),
        ("Joined", "Joined_By"),
        ("Killed", "Killed_By"),
        ("Listened_On", "Listened_On_By"),
        ("Loaded_Into", "Loaded_From"),
        ("Locked", "Locked_By"),
        ("Mapped_Into", "Mapped_By"),
        ("Merged", "Merged_By"),
        ("Modified_Properties_Of", "Properties_Modified_By"),
        ("Monitored", "Monitored_By"),
        ("Moved_From", "Moved_To"),
        ("Moved", "Moved_By"),
        ("Opened", "Opened_By"),
        ("Packed", "Packed_By"),
        ("Packed_From","Packed_Into"),
        ("Parent_Of", "Child_Of"),
        ("Paused", "Paused_By"),
        ("Properties_Queried", "Properties_Queried_By"),
        ("Read_From", "Read_From_By"),
        ("Received", "Received_By"),
        ("Received_From", "Sent_To"),
        ("Received_Via_Upload", "Uploaded_To"),
        ("Related_To","Related_To"),
        ("Renamed_From", "Renamed_To"),
        ("Renamed", "Renamed_By"),
        ("Resolved_To", "Resolved_To"),
        ("Resumed", "Resumed_By"),
        ("Searched_For", "Searched_For_By"),
        ("Sent", "Sent_By"),
        ("Set_From", "Set_To"),
        ("Sub-domain_Of","Supra-domain_Of"),
        ("Suspended", "Suspended_By"),
        ("Unhooked", "Unhooked_By"),
        ("Unlocked", "Unlocked_By"),
        ("Unpacked", "Unpacked_By"),
        ("Uploaded_From","Sent_Via_Upload"),
        ("Uploaded", "Uploaded_By"),
        ("Values_Enumerated", "Values_Enumerated_By"),
        ("Wrote_To", "Written_To_By"),
    ]
    if not drop:
        print "Drop protection does not apply to relationship types"
    RelationshipType.drop_collection()
    count = 0
    for t in types:
        rt = RelationshipType()
        rt.active = 'off'
        rt.description = ''
        rt.forward = t[0]
        rt.reverse = t[1]
        rt.save()
        count += 1
    print "Added %s Relationship Type Pairs." % count
