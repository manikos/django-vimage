from unittest.mock import patch

from django.conf import settings
from django.test import TestCase, override_settings

from vimage.core import exceptions
from vimage.core.const import CONFIG_NAME, APP_NAME
from vimage.core.checker import configuration_check

from .const import dotted_path


class ConfigurationTestCase(TestCase):
    @override_settings()
    def test_missing_config(self):
        del settings.VIMAGE
        error = f'"{APP_NAME}" is in INSTALLED_APPS but has not been ' \
                f'configured! Either add "{CONFIG_NAME}" dict to your ' \
                f'settings or remove "{APP_NAME}" from INSTALLED_APPS.'
        with self.assertRaisesMessage(exceptions.MissingConfigError, error):
            configuration_check()

    @override_settings()
    def test_invalid_config_type(self):
        invalid_config_types = [int, float, complex, list, tuple,
                                str, bytes, bytearray, set, frozenset]
        for invalid_type in invalid_config_types:
            with self.subTest(invalid_type=invalid_type):
                del settings.VIMAGE
                settings.VIMAGE = invalid_type
                error = f'"{CONFIG_NAME}" type is not a dictionary. ' \
                        f'The value should be a non-empty dict!'
                with self.assertRaisesMessage(
                    exceptions.InvalidConfigValueError, error
                ):
                    configuration_check()

    def test_empty_config(self):
        with self.settings(VIMAGE={}):
            error = f'"{CONFIG_NAME}" configuration is an empty dict! ' \
                    f'Add validation rules inside the "{CONFIG_NAME}" dict.'
            with self.assertRaisesMessage(exceptions.EmptyConfigError, error):
                configuration_check()

    def test_vimage_entry_is_valid_called(self):
        with self.settings(VIMAGE={'my_app': {'SIZE': 100}}):
            with patch(dotted_path('base', 'VimageEntry', 'is_valid')) as m:
                configuration_check()
                self.assertTrue(m.called)
