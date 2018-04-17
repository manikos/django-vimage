from types import FunctionType
from unittest.mock import patch

from django.test import TestCase
from django.core.exceptions import ValidationError

from vimage.core.validator_types import ValidationRuleSize
from vimage.core.exceptions import InvalidValueError

from .test_validation_rule_base import ValidatorTestCase
from .const import dotted_path


class ValidationRuleSizeTestCase(TestCase):
    def test_init(self):
        vr = ValidationRuleSize('SIZE', 100)
        self.assertEqual(vr.unit, 'KB')

    def test_humanize_rule(self):
        vr = ValidationRuleSize('SIZE', 100)
        self.assertEqual(vr.humanize_rule(), 'equal to 100KB')

        with patch(dotted_path('validator_types', 'ValidationRuleBase',
                               'format_humanized_rules')) as m:
            vr = ValidationRuleSize('SIZE', {'ne': 100})
            vr.humanize_rule()
            self.assertTrue(m.is_called)

    def test_prettify_value(self):
        vr = ValidationRuleSize('SIZE', 100)
        self.assertEqual(vr.prettify_value(100), '100KB')
        self.assertEqual(vr.prettify_value('Hello'), 'HelloKB')

    @patch(dotted_path('validator_types', 'ValidationRuleSize',
                       'validate_operators'))
    def test_valid_dict_rule(self, patch_method):
        vr = ValidationRuleSize('SIZE', 100)
        vr.valid_dict_rule()
        self.assertTrue(patch_method.called)

    def test_is_valid__size_rule_type(self):
        """
        "rule" should be either a positive int or a dict filled with proper
        key-value validation rules.
        """
        vr = ValidationRuleSize('SIZE', '')
        err = f'The value of the rule "SIZE", "", ' \
              f'should be either an int or a dict.'
        with self.assertRaisesMessage(InvalidValueError, err):
            vr.is_valid()

        vr = ValidationRuleSize('SIZE', [])
        err = f'The value of the rule "SIZE", "[]", ' \
              f'should be either an int or a dict.'
        with self.assertRaisesMessage(InvalidValueError, err):
            vr.is_valid()

        vr = ValidationRuleSize('SIZE', ())
        err = f'The value of the rule "SIZE", "()", ' \
              f'should be either an int or a dict.'
        with self.assertRaisesMessage(InvalidValueError, err):
            vr.is_valid()

    def test_is_valid__size_rule_value(self):
        # invalid value (negative int)
        vr = ValidationRuleSize('SIZE', -1)
        err = f'The value of the rule "SIZE", "-1", ' \
              f'should be a positive integer.'
        with self.assertRaisesMessage(InvalidValueError, err):
            vr.is_valid()

        # invalid value (empty dict)
        vr = ValidationRuleSize('SIZE', {})
        err = f'The value of the rule "SIZE", "{{}}", ' \
              f'should be a non-empty dict.'
        with self.assertRaisesMessage(InvalidValueError, err):
            vr.is_valid()

        # valid value (positive int)
        vr = ValidationRuleSize('SIZE', 1)
        self.assertIsNone(vr.is_valid())

        # valid value (correct dict)
        vr = ValidationRuleSize('SIZE', {'gte': 100})
        m_path = dotted_path('validator_types', 'ValidationRuleSize',
                             'valid_dict_rule')
        with patch(m_path) as m:
            vr.is_valid()
            self.assertTrue(m.called)

        # valid dict
        self.assertIsNone(vr.is_valid())


class ValidationRuleSizeValidatorTestCase(ValidatorTestCase):
    def test_generator_is_function(self):
        vr = ValidationRuleSize('a', 1)
        validator = vr.generate_validator()
        self.assertIsInstance(validator, FunctionType)

    def test_generator_docstring(self):
        vr = ValidationRuleSize('a', 1)
        validator = vr.generate_validator()
        self.assertEqual(validator.__doc__, 'a: 1')

    def test_generate_validator_int_valid(self):
        # "validator" is a function
        vr = ValidationRuleSize('SIZE', 100)
        validator = vr.generate_validator()
        self.assertIsNone(validator(self.img))

    def test_generate_validator_int_invalid(self):
        invalid_rules = [
            ValidationRuleSize('SIZE', 50),
            ValidationRuleSize('SIZE', -1)
        ]
        for vr in invalid_rules:
            with self.subTest(vr=vr):
                validator = vr.generate_validator()
                with self.assertRaises(ValidationError):
                    validator(self.img)

    def test_generate_validator_dict_valid(self):
        valid_rules = [
            ValidationRuleSize('SIZE', {'gte': 50}),
            ValidationRuleSize('SIZE', {'lt': 200}),
            ValidationRuleSize('SIZE', {'lte': 200}),
            ValidationRuleSize('SIZE', {'gte': 50, 'lt': 200}),
            ValidationRuleSize('SIZE', {'gte': 50, 'lt': 200, 'ne': 300}),
            ValidationRuleSize('SIZE', {'ne': 300}),
            ValidationRuleSize('SIZE', {'eq': 100}),
        ]
        for vr in valid_rules:
            with self.subTest(vr=vr):
                validator = vr.generate_validator()
                self.assertIsNone(validator(self.img))

    def test_generate_validator_dict_invalid(self):
        invalid_rules = [
            ValidationRuleSize('SIZE', {'gte': 150}),
            ValidationRuleSize('SIZE', {'lt': 100}),
            ValidationRuleSize('SIZE', {'lte': 99}),
            ValidationRuleSize('SIZE', {'gte': 150, 'lte': 100}),
            ValidationRuleSize('SIZE', {'gte': 99, 'lt': 100, 'ne': 300}),
            ValidationRuleSize('SIZE', {'ne': 100}),
            ValidationRuleSize('SIZE', {'eq': 200}),
        ]
        for vr in invalid_rules:
            with self.subTest(vr=vr):
                validator = vr.generate_validator()
                with self.assertRaises(ValidationError):
                    validator(self.img)

    def test_generate_validator_custom_error(self):
        vr = ValidationRuleSize('SIZE', {
            'lt': 50,
            'err': 'size error here!',
        })
        validator = vr.generate_validator()
        err = 'size error here!'
        with self.assertRaisesMessage(ValidationError, err):
            validator(self.img)
