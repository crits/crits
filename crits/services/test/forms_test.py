import unittest

from crits.services.core import Service, ServiceConfigOption
from crits.services.forms import (_get_config_fields, make_edit_config_form,
        make_run_config_form)


class ServiceWithNoDefaultConfig(Service):
    name = "dummy"
    version = "1.0"

class ServiceWithDefaultConfig(Service):
    name = "dummy2"
    version = "1.1"
    default_config = [
            ServiceConfigOption("some option", ServiceConfigOption.STRING),
            ServiceConfigOption("private option", ServiceConfigOption.BOOL,
                                private=True),
        ]

class TestForms(unittest.TestCase):

    def test_default_config(self):
        FormClass = make_edit_config_form(ServiceWithDefaultConfig)
        self.assertNotEqual(None, FormClass)

        FormClass2 = make_run_config_form(ServiceWithDefaultConfig)
        self.assertNotEqual(None, FormClass)

        fields = _get_config_fields(ServiceWithDefaultConfig, True)
        self.assertEqual(1, len(fields))

        private_fields = _get_config_fields(ServiceWithDefaultConfig, False)
        self.assertEqual(2, len(private_fields))


    def test_no_default_config(self):
        FormClass = make_edit_config_form(ServiceWithNoDefaultConfig)
        self.assertEqual(None, FormClass)

        FormClass2 = make_run_config_form(ServiceWithNoDefaultConfig)
        self.assertNotEqual(None, FormClass2)


if __name__ == "__main__":
    unittest.main()
