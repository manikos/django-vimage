from types import FunctionType
from unittest.mock import patch

from django.test import TestCase
from django.core.exceptions import ValidationError

from vimage.core.validator_types import ValidationRuleAspectRatio
from vimage.core.exceptions import InvalidValueError

from .test_validation_rule_base import ValidatorTestCase
from .const import dotted_path


class ValidationRuleAspectRatioTestCase(TestCase):
    def test_humanize_rule(self):
        vr = ValidationRuleAspectRatio('ASPECT_RATIO', 1.5)
        self.assertEqual(vr.humanize_rule(), 'equal to 1.5')

        vr = ValidationRuleAspectRatio('ASPECT_RATIO', {'eq': 1.5})
        self.assertEqual(vr.humanize_rule(), 'equal to 1.5')

        vr = ValidationRuleAspectRatio('ASPECT_RATIO', {'gt': 1.5, 'lt': 2.1})
        self.assertEqual(
            vr.humanize_rule(),
            'greater than 1.5 and less than 2.1'
        )

    def test_valid_dict_rule(self):
        vr = ValidationRuleAspectRatio('ASPECT_RATIO', {'gt': 1.5, 'lt': 2.1})
        with patch(dotted_path('validator_types', 'ValidationRuleBase',
                               'validate_operators')) as m:
            vr.valid_dict_rule()
            args, kwargs = m.call_args
            self.assertTrue(m.called)
            self.assertEqual(args, ({'gt': 1.5, 'lt': 2.1}, float))
            self.assertEqual(kwargs, {})

    def test_is_valid(self):
        # Rule value must be a float
        vr = ValidationRuleAspectRatio('ASPECT_RATIO', '')
        err = f'The value of the rule "ASPECT_RATIO", "", ' \
              f'should be either a float or dict.'
        with self.assertRaisesMessage(InvalidValueError, err):
            vr.is_valid()

        # positive int (invalid)
        vr = ValidationRuleAspectRatio('ASPECT_RATIO', 1)
        err = f'The value of the rule "ASPECT_RATIO", "1", ' \
              f'should be either a float or dict.'
        with self.assertRaisesMessage(InvalidValueError, err):
            vr.is_valid()

        # negative float (invalid)
        vr = ValidationRuleAspectRatio('ASPECT_RATIO', -1.5)
        err = f'The value of the rule "ASPECT_RATIO", "-1.5", ' \
              f'should be a positive float.'
        with self.assertRaisesMessage(InvalidValueError, err):
            vr.is_valid()

        # invalid value (empty dict)
        vr = ValidationRuleAspectRatio('ASPECT_RATIO', {})
        err = f'The value of the rule "ASPECT_RATIO", "{{}}", ' \
              f'should be a non-empty dict.'
        with self.assertRaisesMessage(InvalidValueError, err):
            vr.is_valid()

        # valid value (correct dict)
        vr = ValidationRuleAspectRatio('ASPECT_RATIO', {'eq': 1.0})
        m_path = dotted_path('validator_types', 'ValidationRuleAspectRatio',
                             'valid_dict_rule')
        with patch(m_path) as m:
            vr.is_valid()
            self.assertTrue(m.called)

        # valid values
        vr = ValidationRuleAspectRatio('ASPECT_RATIO', 1.0)
        self.assertIsNone(vr.is_valid())
        vr = ValidationRuleAspectRatio('ASPECT_RATIO', 2.3)
        self.assertIsNone(vr.is_valid())


class ValidationRuleAspectRatioValidatorTestCase(ValidatorTestCase):
    def test_generator_is_function(self):
        vr = ValidationRuleAspectRatio('a', 1.0)
        validator = vr.generate_validator()
        self.assertIsInstance(validator, FunctionType)

    def test_generator_docstring(self):
        vr = ValidationRuleAspectRatio('a', 1.0)
        validator = vr.generate_validator()
        self.assertEqual(validator.__doc__, 'a: 1.0')

    def test_generate_validator__valid(self):
        valid_rules = [
            ValidationRuleAspectRatio('ASPECT_RATIO', 1.0),
            ValidationRuleAspectRatio('ASPECT_RATIO', {'gte': 1.0}),
            ValidationRuleAspectRatio('ASPECT_RATIO', {'lt': 1.1}),
            ValidationRuleAspectRatio('ASPECT_RATIO', {'gt': 0.9, 'lt': 1.1}),
        ]
        for valid_rule in valid_rules:
            with self.subTest(valid_rule=valid_rule):
                validator = valid_rule.generate_validator()
                self.assertIsNone(validator(self.img))

    def test_generate_validator__invalid(self):
        invalid_rules = [
            ValidationRuleAspectRatio('ASPECT_RATIO', 2.0),
            ValidationRuleAspectRatio('ASPECT_RATIO', {'gt': 1.0}),
            ValidationRuleAspectRatio('ASPECT_RATIO', {'lt': 0.8}),
            ValidationRuleAspectRatio('ASPECT_RATIO', {'gt': 1.9, 'lt': 1.1}),
        ]
        for invalid_rule in invalid_rules:
            with self.subTest(invalid_rule=invalid_rule):
                with self.assertRaises(ValidationError):
                    validator = invalid_rule.generate_validator()
                    validator(self.img)

    def test_generate_validator_custom_error(self):
        vr = ValidationRuleAspectRatio('ASPECT_RATIO', {
            'lt': 0.3,
            'err': 'aspect ratio error here!',
        })
        validator = vr.generate_validator()
        err = 'aspect ratio error here!'
        with self.assertRaisesMessage(ValidationError, err):
            validator(self.img)
