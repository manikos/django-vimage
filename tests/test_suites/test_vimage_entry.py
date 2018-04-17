from unittest.mock import patch

from django.test import TestCase

from vimage.core.base import VimageKey, VimageValue, VimageEntry

from .const import dotted_path


class VimageEntryTestCase(TestCase):
    def test_entry(self):
        ve = VimageEntry('app', {})
        self.assertIsInstance(ve.key, VimageKey)
        self.assertEqual(ve.key.key, VimageKey('app').key)
        self.assertIsInstance(ve.value, VimageValue)
        self.assertEqual(ve.value.value, VimageValue({}).value)

    def test_str(self):
        ve = VimageEntry('app', {})
        self.assertEqual(str(ve), 'app: {}')

    def test_repr(self):
        ve = VimageEntry('app', {})
        self.assertEqual(
            repr(ve),
            "VimageEntry('app', {})"
        )
        self.assertIsInstance(eval(repr(ve)), VimageEntry)

    def test_is_valid(self):
        m_path = dotted_path('base', 'VimageKey', 'is_valid')
        with patch(m_path) as m:
            ve = VimageEntry('myapp.models', {'SIZE': 10})
            ve.is_valid()
            self.assertTrue(m.called)

        m_path = dotted_path('base', 'VimageValue', 'is_valid')
        with patch(m_path) as m:
            ve = VimageEntry('myapp.models', {'SIZE': 10})
            ve.is_valid()
            self.assertTrue(m.called)

    def test_app_label(self):
        m_path = dotted_path('base', 'VimageKey', 'get_app_label')
        with patch(m_path) as m:
            ve = VimageEntry('myapp.models', {'SIZE': 10})
            label = ve.app_label
            self.assertTrue(m.called)

    def test_fields(self):
        m_path = dotted_path('base', 'VimageKey', 'get_fields')
        with patch(m_path) as m:
            ve = VimageEntry('myapp.models', {'SIZE': 10})
            sp = ve.fields
            self.assertTrue(m.called)

    def test_specificity(self):
        m_path = dotted_path('base', 'VimageKey', 'get_specificity')
        with patch(m_path) as m:
            ve = VimageEntry('myapp.models', {'SIZE': 10})
            sp = ve.specificity
            self.assertTrue(m.called)

    def test_mapping(self):
        m_path = dotted_path('base', 'VimageValue', 'type_validator_mapping')
        with patch(m_path) as m:
            ve = VimageEntry('myapp.models', {'SIZE': 10})
            sp = ve.mapping
            self.assertTrue(m.called)

    def test_entry_info(self):
        ve = VimageEntry('myapp.models', {'SIZE': 10})
        self.assertEqual(
            sorted(ve.entry_info.keys()),
            ['app_label', 'fields', 'mapping', 'specificity']
        )
