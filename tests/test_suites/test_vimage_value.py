from unittest.mock import patch
from types import GeneratorType

from django.test import TestCase

from vimage.core import validator_types
from vimage.core.base import VimageValue
from vimage.core.exceptions import InvalidValueError

from .const import CORE, dotted_path


class VimageValueTestCase(TestCase):
    def test_value(self):
        vv = VimageValue({})
        self.assertEqual(vv.value, {})
        err = f'Each VIMAGE dict value should be a ' \
              f'<dict> type. Current value: "1", is <int>!'
        with self.assertRaisesMessage(TypeError, err):
            VimageValue(1)

    def test_str(self):
        vv = VimageValue({})
        self.assertEqual(str(vv), '{}')
        vv = VimageValue({'SIZE': 100})
        self.assertEqual(str(vv), "{'SIZE': 100}")

    def test_repr(self):
        vv = VimageValue({})
        self.assertEqual(repr(vv), 'VimageValue({})')
        self.assertIsInstance(eval(repr(vv)), VimageValue)

        vv = VimageValue({'SIZE': 100})
        self.assertEqual(repr(vv), 'VimageValue({\'SIZE\': 100})')
        self.assertIsInstance(eval(repr(vv)), VimageValue)

    def test_validation_rule_generator(self):
        # A generator is returned
        v = VimageValue({'SIZE': 1})
        self.assertIsInstance(v.validation_rule_generator(), GeneratorType)

        # Size ValidationRule
        size_vv = VimageValue({'SIZE': {}})
        size_vr = next(size_vv.validation_rule_generator())
        self.assertIsInstance(size_vr, validator_types.ValidationRuleSize)

        # Dimensions ValidationRule
        dimensions_vv = VimageValue({'DIMENSIONS': {}})
        dimensions_vr = next(dimensions_vv.validation_rule_generator())
        self.assertIsInstance(
            dimensions_vr,
            validator_types.ValidationRuleDimensions
        )

        # Format ValidationRule
        format_vv = VimageValue({'FORMAT': {}})
        format_vr = next(format_vv.validation_rule_generator())
        self.assertIsInstance(format_vr, validator_types.ValidationRuleFormat)

        # Aspect Ratio ValidationRule
        ratio_vv = VimageValue({'ASPECT_RATIO': {}})
        ratio_vr = next(ratio_vv.validation_rule_generator())
        self.assertIsInstance(
            ratio_vr,
            validator_types.ValidationRuleAspectRatio
        )

    def test_validate_value(self):
        """ Test that is_valid() method is called """
        mappings = {
            'SIZE': 'ValidationRuleSize',
            'DIMENSIONS': 'ValidationRuleDimensions',
            'FORMAT': 'ValidationRuleFormat',
            'ASPECT_RATIO': 'ValidationRuleAspectRatio',
        }
        for name, class_name in mappings.items():
            const_path = [CORE, 'validator_types', 'is_valid']
            # Insert the "class_name" before the "is_valid" element
            const_path.insert(-1, class_name)
            with patch('.'.join(const_path)) as m:
                vv = VimageValue({name: {}})
                vv.validate_value()
                self.assertTrue(m.called)

    def test_nonsense_keys_together(self):
        vv = VimageValue({'SIZE': 15})
        self.assertIsNone(vv.nonsense_keys_together())

        vv = VimageValue({'DIMENSIONS': 15, 'ASPECT_RATIO': 1})
        with self.assertRaises(InvalidValueError):
            vv.nonsense_keys_together()

    def test_type_validator_mapping(self):
        vv = VimageValue({'SIZE': 15})
        self.assertIsInstance(vv.type_validator_mapping(), dict)

    def test_is_valid(self):
        vv = VimageValue({})
        err = f'The value "{{}}" should be a non-empty dict ' \
              f'with the proper validation rules. ' \
              f'Please check the documentation for more information.'
        with self.assertRaisesMessage(InvalidValueError, err):
            vv.is_valid()

        value = {
            'DIMENSIONS': (100, 100),
            'ASPECT_RATIO': 1,
        }
        vv = VimageValue(value)
        with patch(dotted_path('base', 'VimageValue',
                               'nonsense_keys_together')) as m:
            with self.assertRaises(InvalidValueError):
                vv.is_valid()
                self.assertTrue(m.called)

        vv = VimageValue({'FORMAT': 'jpeg'})
        m_path = dotted_path('base', 'VimageValue', 'validate_value')
        with patch(m_path) as m:
            vv.is_valid()
            self.assertTrue(m.called)
