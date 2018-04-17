from unittest.mock import patch

from django.conf import settings
from django.test import TestCase, override_settings

from vimage.core import add_validators
from .const import dotted_path


class CoreInitTestCase(TestCase):
    @override_settings()
    def test_add_validators(self):
        settings.VIMAGE = 'VIMAGE'
        with patch(dotted_path('base', 'VimageConfig', 'add_validators')) as m:
            add_validators()
            self.assertTrue(m.called)
