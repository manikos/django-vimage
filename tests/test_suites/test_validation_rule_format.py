from types import FunctionType
from unittest.mock import patch

from django.test import TestCase
from django.core.exceptions import ValidationError

from vimage.core.validator_types import ValidationRuleFormat
from vimage.core.exceptions import InvalidValueError

from .test_validation_rule_base import ValidatorTestCase
from .const import dotted_path


class ValidationRuleFormatTestCase(TestCase):
    def test_humanize_rule(self):
        vr = ValidationRuleFormat('FORMAT', 'jpeg')
        self.assertEqual(vr.humanize_rule(), 'equal to JPEG')

        vr = ValidationRuleFormat('FORMAT', ['jpeg'])
        self.assertEqual(vr.humanize_rule(), 'equal to JPEG')

        vr = ValidationRuleFormat('FORMAT', ['jpeg', 'webp'])
        self.assertEqual(
            vr.humanize_rule(),
            'equal to one of the following formats JPEG or WEBP'
        )

        vr = ValidationRuleFormat('FORMAT', {'ne': 'gif'})
        self.assertEqual(vr.humanize_rule(), 'not equal to GIF')

        vr = ValidationRuleFormat('FORMAT', {'eq': 'gif'})
        self.assertEqual(vr.humanize_rule(), 'equal to GIF')

        vr = ValidationRuleFormat('FORMAT', {'ne': ['gif', 'png']})
        self.assertEqual(
            vr.humanize_rule(),
            'not equal to the following formats GIF and PNG'
        )

    def test_prettify_list(self):
        vr = ValidationRuleFormat('FORMAT', ['jpeg', 'png'])
        self.assertListEqual(
            vr.prettify_list(['jpeg', 'png']),
            ['JPEG', 'PNG']
        )

    def test_prettify_value(self):
        vr = ValidationRuleFormat('FORMAT', 'aaa')
        self.assertEqual(vr.prettify_value('aaa'), 'AAA')

    def test_valid_format(self):
        # rule value must be a str
        vr = ValidationRuleFormat('FORMAT', 100)
        self.assertFalse(vr.valid_format(vr.rule))

        # str but not an allowable one
        vr = ValidationRuleFormat('FORMAT', 'hello')
        self.assertFalse(vr.valid_format(vr.rule))

        # an allowable str
        vr = ValidationRuleFormat('FORMAT', 'png')
        self.assertTrue(vr.valid_format(vr.rule))

    def test_valid_format_list(self):
        # Must be a non-empty list of allowable strings (image extensions)
        vr = ValidationRuleFormat('FORMAT', [])
        self.assertFalse(vr.valid_format_list(vr.rule))

        vr = ValidationRuleFormat('FORMAT', ['a', 'b'])
        self.assertFalse(vr.valid_format_list(vr.rule))

        # Valid
        vr = ValidationRuleFormat('FORMAT', ['jpeg', 'png', 'gif'])
        self.assertTrue(vr.valid_format_list(vr.rule))

    def test_valid_dict_rule(self):
        """ Assumes that "self.rule" is a dict """

        # dict with invalid key. Invalid.
        vr = ValidationRuleFormat('FORMAT', {'eq': 'jpeg'})
        with patch(dotted_path('validator_types', 'ValidationRuleBase',
                               'valid_dict_rule_str')) as m:
            vr.valid_dict_rule()
            self.assertTrue(m.called)

        # Dict with valid key but wrong value type
        vr = ValidationRuleFormat('FORMAT', {'ne': 1})
        err = f'The value of the key "ne", ' \
              f'inside "FORMAT: {{\'ne\': 1}}", ' \
              f'should be either a str or a list. ' \
              f'Now it\'s type is "int".'
        with self.assertRaisesMessage(InvalidValueError, err):
            vr.valid_dict_rule()

        # Dict with valid key but not an allowable str value
        vr = ValidationRuleFormat('FORMAT', {'ne': 'hello'})
        err = f'The value of the key "ne", inside "FORMAT: ' \
              f'{{\'ne\': \'hello\'}}", should be one of: ' \
              f'"jpeg, png, gif, bmp, webp".'
        with self.assertRaisesMessage(InvalidValueError, err):
            vr.valid_dict_rule()

        # Dict with valid key, list value but not an allowable one
        vr = ValidationRuleFormat('FORMAT', {'ne': ['hello', 123]})
        err = f'The value of the key "ne", inside "FORMAT: ' \
              f'{{\'ne\': [\'hello\', 123]}}", should be one or more of: ' \
              f'"jpeg, png, gif, bmp, webp".'
        with self.assertRaisesMessage(InvalidValueError, err):
            vr.valid_dict_rule()

        # Dict with valid key-value [str]
        vr = ValidationRuleFormat('FORMAT', {'ne': 'bmp'})
        self.assertIsNone(vr.valid_dict_rule())

        # Dict with valid key-value and custom error [str]
        vr = ValidationRuleFormat('FORMAT', {'ne': 'bmp', 'err': 'error here'})
        self.assertIsNone(vr.valid_dict_rule())

        # Dict with valid key-value [list]
        vr = ValidationRuleFormat('FORMAT', {'ne': ['bmp', 'gif']})
        self.assertIsNone(vr.valid_dict_rule())

    def test_is_valid__false(self):
        # Rule not one of [str, list, dict]
        vr = ValidationRuleFormat('FORMAT', 123)
        err = f'The value of the rule "FORMAT", "123", ' \
              f'should be either a str, list or dict.'
        with self.assertRaisesMessage(InvalidValueError, err):
            vr.is_valid()

        # Rule is not an allowable string
        vr = ValidationRuleFormat('FORMAT', 'hello')
        err = f'The value of the rule "FORMAT", "hello", ' \
              f'should be one of the valid formats: ' \
              f'"jpeg, png, gif, bmp, webp".'
        with self.assertRaisesMessage(InvalidValueError, err):
            vr.is_valid()

        # Rule is not an allowable list
        vr = ValidationRuleFormat('FORMAT', ['hello'])
        err = f'The value of the rule "FORMAT", "[\'hello\']", ' \
              f'should be one or more of the valid image formats: ' \
              f'"jpeg, png, gif, bmp, webp".'
        with self.assertRaisesMessage(InvalidValueError, err):
            vr.is_valid()

        # Rule is an empty dict. Invalid
        vr = ValidationRuleFormat('FORMAT', {})
        err = f'The value of the rule "FORMAT", "{{}}", ' \
              f'should be a non-empty dict.'
        with self.assertRaisesMessage(InvalidValueError, err):
            vr.is_valid()

    def test_is_valid__true(self):
        vr = ValidationRuleFormat('FORMAT', 'jpeg')
        self.assertIsNone(vr.is_valid())

        vr = ValidationRuleFormat('FORMAT', ['jpeg', 'bmp'])
        self.assertIsNone(vr.is_valid())

        vr = ValidationRuleFormat('FORMAT', {'ne': 'bmp'})
        with patch(dotted_path('validator_types', 'ValidationRuleFormat',
                               'valid_dict_rule')) as m:
            self.assertIsNone(vr.is_valid())
            self.assertTrue(m.called)


class ValidationRuleFormatValidatorTestCase(ValidatorTestCase):
    def test_generator_is_function(self):
        vr = ValidationRuleFormat('a', 1)
        validator = vr.generate_validator()
        self.assertIsInstance(validator, FunctionType)

    def test_generator_docstring(self):
        vr = ValidationRuleFormat('a', 1)
        validator = vr.generate_validator()
        self.assertEqual(validator.__doc__, 'a: 1')

    def test_generate_validator_str_valid(self):
        vr = ValidationRuleFormat('FORMAT', 'jpeg')
        validator = vr.generate_validator()
        self.assertIsNone(validator(self.img))

    def test_generate_validator_str_invalid(self):
        vr = ValidationRuleFormat('FORMAT', 'bmp')
        validator = vr.generate_validator()
        with self.assertRaises(ValidationError):
            validator(self.img)

    def test_generate_validator_list_valid(self):
        vr = ValidationRuleFormat('FORMAT', ['bmp', 'webp', 'jpeg'])
        validator = vr.generate_validator()
        self.assertIsNone(validator(self.img))

    def test_generate_validator_list_invalid(self):
        vr = ValidationRuleFormat('FORMAT', ['bmp', 'gif'])
        validator = vr.generate_validator()
        with self.assertRaises(ValidationError):
            validator(self.img)

    def test_generate_validator_dict_valid(self):
        valid_rules = [
            ValidationRuleFormat('FORMAT', {'ne': 'webp'}),
            ValidationRuleFormat('FORMAT', {'ne': ['bmp', 'gif']}),
            ValidationRuleFormat('FORMAT', {
                'ne': ['bmp', 'gif'],
                'err': 'invalid format',
            }),
        ]
        for vr in valid_rules:
            with self.subTest(vr=vr):
                validator = vr.generate_validator()
                self.assertIsNone(validator(self.img))

    def test_generate_validator_dict_invalid(self):
        invalid_rules = [
            ValidationRuleFormat('FORMAT', {'ne': 'jpeg'}),
            ValidationRuleFormat('FORMAT', {'ne': ['webp', 'jpeg']}),
        ]
        for vr in invalid_rules:
            with self.subTest(vr=vr):
                validator = vr.generate_validator()
                with self.assertRaises(ValidationError):
                    validator(self.img)

    def test_generate_validator_custom_error(self):
        vr = ValidationRuleFormat('FORMAT', {
            'ne': 'jpeg',
            'err': 'format error here!',
        })
        validator = vr.generate_validator()
        err = 'format error here!'
        with self.assertRaisesMessage(ValidationError, err):
            validator(self.img)
