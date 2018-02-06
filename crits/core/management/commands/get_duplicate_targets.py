from bson import Code

from django.core.management.base import BaseCommand
from optparse import make_option

from crits.emails.email import Email
from crits.targets.target import Target

class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--delete',
                    '-d',
                    dest='is_delete',
                    default=False,
                    action='store_true',
                    help='Delete duplicate targets based on the email_address field.'),
    )
    help = 'Prints out duplicate target emails due to case sensitivity.'

    is_delete = False

    def handle(self, *args, **options):
        """
        Script Execution.
        """

        self.is_delete = options.get('is_delete')

        mapcode = """
            function () {
                try {
                    this.to.forEach(function(z) {
                        emit(z.toLowerCase(), {count: 1});
                    });
                } catch(err) {}
            }
        """
        reducecode = """
            function(k,v) {
                var count = 0;
                v.forEach(function(v) {
                    count += v["count"];
                });
                return {count: count};
            }
        """
        m = Code(mapcode)
        r = Code(reducecode)
        results = Email.objects(to__exists=True).map_reduce(m, r, 'inline')
        for result in results:
            try:
                targets = Target.objects(email_address__iexact=result.key)
                targ_dup_count = targets.count()

                if targ_dup_count > 1:
                    print str(result.key) + " [" + str(targ_dup_count) + "]"

                    for target in targets:
                        print target.to_json()

                    if self.is_delete:
                        delete_up_to = targets.count() - 1
                        for target in targets[:delete_up_to]:
                            print "Deleting target: " + str(target.id)
                            target.delete()

            except Exception, e:
                print e
                pass

