from types import FunctionType
from unittest.mock import patch

from django.test import TestCase
from django.core.exceptions import ValidationError

from vimage.core.validator_types import ValidationRuleDimensions
from vimage.core.exceptions import InvalidValueError

from .test_validation_rule_base import ValidatorTestCase
from .const import dotted_path


class ValidationRuleDimensionsTestCase(TestCase):
    def test_init(self):
        vr = ValidationRuleDimensions('DIMENSIONS', 100)
        self.assertEqual(vr.unit, 'px')

    def test_humanize_rule(self):
        vr = ValidationRuleDimensions('DIMENSIONS', (400, 400))
        self.assertEqual(vr.humanize_rule(), 'equal to 400 x 400px')

        vr = ValidationRuleDimensions('DIMENSIONS', [(40, 40), (50, 50)])
        self.assertEqual(
            vr.humanize_rule(),
            'equal to one of the following dimensions 40 x 40px or 50 x 50px'
        )

        vr = ValidationRuleDimensions('DIMENSIONS', [(4, 4), (5, 5), (6, 6)])
        self.assertEqual(
            vr.humanize_rule(),
            'equal to one of the following dimensions 4 x 4px, 5 x 5px '
            'or 6 x 6px'
        )

    def test_humanize_rule_dict(self):
        vr = ValidationRuleDimensions('DIMENSIONS', {
            'w': {
                'gte': 1000,
                'lte': 1500,
            },
            'h': {
                'gt': 500,
                'lt': 600,
            }
        })
        self.assertEqual(
            vr.humanize_rule(),
            'Width greater than or equal to 1000px and less than or equal to '
            '1500px. Height greater than 500px and less than 600px'
        )

        vr = ValidationRuleDimensions('DIMENSIONS', {
            'w': {
                'gte': 1000,
                'lte': 1500,
            },
        })
        self.assertEqual(
            vr.humanize_rule(),
            'Width greater than or equal to 1000px and less than or equal to '
            '1500px'
        )

        vr = ValidationRuleDimensions('DIMENSIONS', {
            'h': {
                'gt': 500,
                'lt': 600,
            },
        })
        self.assertEqual(
            vr.humanize_rule(),
            'Height greater than 500px and less than 600px'
        )

        vr = ValidationRuleDimensions('DIMENSIONS', {
            'gt': (500, 500),
            'lt': (600, 600),
        })
        self.assertEqual(
            vr.humanize_rule(),
            'greater than 500 x 500px and less than 600 x 600px'
        )

    def test_prettify_list(self):
        vr = ValidationRuleDimensions('DIMENSIONS', [(3, 3), (4, 4)])
        self.assertListEqual(
            vr.prettify_list([(3, 3), (4, 4)]),
            ['3 x 3px', '4 x 4px']
        )

    def test_prettify_value(self):
        vr = ValidationRuleDimensions('DIMENSIONS', (3, 3))
        self.assertEqual(vr.prettify_value((3, 3)), '3 x 3px')
        self.assertEqual(vr.prettify_value((3, 3), 'Χ'), '3 Χ 3px')

    def test_has_width_height_keys(self):
        # Rule value must be a dict
        vr = ValidationRuleDimensions('DIMENSIONS', 100)
        with self.assertRaises(AttributeError):
            vr.has_width_height_keys()

        width_height_rules = [
            ValidationRuleDimensions('DIMENSIONS', {'w': 1}),
            ValidationRuleDimensions('DIMENSIONS', {'h': 1}),
            ValidationRuleDimensions('DIMENSIONS', {'w': 1, 'h': 1}),
        ]
        for rule in width_height_rules:
            with self.subTest(rule=rule):
                self.assertTrue(rule.has_width_height_keys())

        no_width_height_rules = [
            ValidationRuleDimensions('DIMENSIONS', {}),
            ValidationRuleDimensions('DIMENSIONS', {'gte': 100}),
        ]
        for rule in no_width_height_rules:
            with self.subTest(rule=rule):
                self.assertFalse(rule.has_width_height_keys())

    @patch(dotted_path('validator_types', 'ValidationRuleDimensions',
                       'validate_operators'))
    def test_valid_dict_rule_width_height(self, patch_method):
        vr = ValidationRuleDimensions('DIMENSIONS', {'w': {}})
        vr.valid_dict_rule()
        args, kwargs = patch_method.call_args
        self.assertTrue(patch_method.called)
        self.assertEqual(args, ({}, int))
        self.assertEqual(kwargs, {})

    @patch(dotted_path('validator_types', 'ValidationRuleDimensions',
                       'validate_operators'))
    def test_valid_dict_rule_wo_width_height(self, patch_method):
        vr = ValidationRuleDimensions('DIMENSIONS', {})
        vr.valid_dict_rule()
        args, kwargs = patch_method.call_args
        self.assertTrue(patch_method.called)
        self.assertEqual(args, ({}, tuple))
        self.assertEqual(kwargs, {})

    def test_is_valid__dimensions_rule_type(self):
        """
        "rule" should be either a tuple, a list or a dict filled with proper
        key-value validation rules.
        """
        vr = ValidationRuleDimensions('DIMENSIONS', '')
        err = f'The value of the rule "DIMENSIONS", "", ' \
              f'should be either a tuple, a list or a dict.'
        with self.assertRaisesMessage(InvalidValueError, err):
            vr.is_valid()

        vr = ValidationRuleDimensions('DIMENSIONS', 12)
        err = f'The value of the rule "DIMENSIONS", "12", ' \
              f'should be either a tuple, a list or a dict.'
        with self.assertRaisesMessage(InvalidValueError, err):
            vr.is_valid()

    def test_is_valid__dimensions_rule_tuple(self):
        invalid_vrs = [
            ValidationRuleDimensions('DIMENSIONS', ()),
            ValidationRuleDimensions('DIMENSIONS', (10,)),
            ValidationRuleDimensions('DIMENSIONS', (-10, 10)),
            ValidationRuleDimensions('DIMENSIONS', (-10, -10)),
            ValidationRuleDimensions('DIMENSIONS', (10, 10, 10)),
        ]
        for vr in invalid_vrs:
            with self.subTest(vr=vr):
                err = f'The value of the rule "DIMENSIONS", "{vr.rule}", ' \
                      f'should consist of two positive integers.'
                with self.assertRaisesMessage(InvalidValueError, err):
                    vr.is_valid()

        vr = ValidationRuleDimensions('DIMENSIONS', (10, 10))
        self.assertIsNone(vr.is_valid())

    def test_is_valid__dimensions_rule_list(self):
        invalid_vrs = [
            ValidationRuleDimensions('DIMENSIONS', []),
            ValidationRuleDimensions('DIMENSIONS', [(10,)]),
            ValidationRuleDimensions('DIMENSIONS', [(10, -10)]),
            ValidationRuleDimensions('DIMENSIONS', [(10, 10), (-10, 10)]),
        ]
        for vr in invalid_vrs:
            with self.subTest(vr=vr):
                err = f'The value of the rule "DIMENSIONS", "{vr.rule}", ' \
                      f'should consist of tuples with two positive ' \
                      f'integers, each.'
                with self.assertRaisesMessage(InvalidValueError, err):
                    vr.is_valid()

        vr = ValidationRuleDimensions('DIMENSIONS', [(10, 10), (5, 5)])
        self.assertIsNone(vr.is_valid())

    def test_is_valid__dimensions_rule_dict(self):
        vr = ValidationRuleDimensions('DIMENSIONS', {})
        err = f'The value of the rule "DIMENSIONS", "{{}}", ' \
              f'should be a non-empty dict.'
        with self.assertRaisesMessage(InvalidValueError, err):
            vr.is_valid()

        with patch(dotted_path('validator_types', 'ValidationRuleDimensions',
                               'valid_dict_rule')) as m:
            vr = ValidationRuleDimensions('DIMENSIONS', {'gte': 100})
            vr.is_valid()
            # if dict is non-empty check that "valid_dict_rule" is called.
            self.assertTrue(m.called)


class ValidationRuleDimensionsValidatorTestCase(ValidatorTestCase):
    def test_generator_is_function(self):
        vr = ValidationRuleDimensions('a', 1)
        validator = vr.generate_validator()
        self.assertIsInstance(validator, FunctionType)

    def test_generator_docstring(self):
        vr = ValidationRuleDimensions('a', 1)
        validator = vr.generate_validator()
        self.assertEqual(validator.__doc__, 'a: 1')

    def test_generate_validator_tuple_valid(self):
        vr = ValidationRuleDimensions('DIMENSIONS', (500, 498))
        validator = vr.generate_validator()
        self.assertIsNone(validator(self.img))

    def test_generate_validator_tuple_invalid(self):
        vr = ValidationRuleDimensions('DIMENSIONS', (500, 500))
        validator = vr.generate_validator()
        with self.assertRaises(ValidationError):
            validator(self.img)

    def test_generate_validator_list_valid(self):
        vr = ValidationRuleDimensions('DIMENSIONS', [(500, 500), (500, 498)])
        validator = vr.generate_validator()
        self.assertIsNone(validator(self.img))

    def test_generate_validator_list_invalid(self):
        vr = ValidationRuleDimensions('DIMENSIONS', [(500, 500), (100, 100)])
        validator = vr.generate_validator()
        with self.assertRaises(ValidationError):
            validator(self.img)

    def test_generate_validator_dict_valid(self):
        valid_rules = [
            ValidationRuleDimensions('DIMENSIONS', {
                'gte': (500, 498),
                'lte': (500, 498),
            }),
            ValidationRuleDimensions('DIMENSIONS', {'lt': (600, 600)}),
            ValidationRuleDimensions('DIMENSIONS', {'lte': (500, 498)}),
            ValidationRuleDimensions('DIMENSIONS', {'gte': (500, 498)}),
            ValidationRuleDimensions('DIMENSIONS', {
                'gte': (500, 498),
                'lte': (500, 498),
                'ne': (100, 100),
            }),
            ValidationRuleDimensions('DIMENSIONS', {
                'gte': (500, 498),
                'lte': (500, 498),
                'ne': (100, 100),
                'err': 'dimensions error message',
            }),
            ValidationRuleDimensions('DIMENSIONS', {'ne': (100, 100)}),
            ValidationRuleDimensions('DIMENSIONS', {'eq': (500, 498)}),
            ValidationRuleDimensions('DIMENSIONS', {
                'w': {
                    'gt': 100,
                },
                'h': {
                    'eq': 498,
                }
            }),
            ValidationRuleDimensions('DIMENSIONS', {
                'w': {
                    'eq': 500,
                },
            }),
            ValidationRuleDimensions('DIMENSIONS', {
                'h': {
                    'eq': 498,
                    'err': 'width error message',
                }
            }),
            ValidationRuleDimensions('DIMENSIONS', {
                'w': {
                    'gt': 100,
                    'err': 'width error message',
                },
                'h': {
                    'eq': 498,
                    'err': 'height error message',
                }
            }),
        ]
        for vr in valid_rules:
            with self.subTest(vr=vr):
                validator = vr.generate_validator()
                self.assertIsNone(validator(self.img))

    def test_generate_validator_dict_invalid(self):
        invalid_rules = [
            ValidationRuleDimensions('DIMENSIONS', {'gte': (150, 1000)}),
            ValidationRuleDimensions('DIMENSIONS', {'lt': (500, 498)}),
            ValidationRuleDimensions('DIMENSIONS', {'lte': (300, 400)}),
            ValidationRuleDimensions('DIMENSIONS', {
                'gte': (150, 700),
                'lte': (100, 100),
            }),
            ValidationRuleDimensions('DIMENSIONS', {
                'gte': (600, 100),
                'lt': (1000, 1000),
                'ne': (450, 450),
            }),
            ValidationRuleDimensions('DIMENSIONS', {'ne': (500, 498)}),
            ValidationRuleDimensions('DIMENSIONS', {'eq': (50, 498)}),
            ValidationRuleDimensions('DIMENSIONS', {
                'w': {
                    'lt': 100,
                },
                'h': {
                    'eq': 498,
                }
            }),
            ValidationRuleDimensions('DIMENSIONS', {
                'h': {
                    'ne': 498,
                }
            }),
            ValidationRuleDimensions('DIMENSIONS', {
                'w': {
                    'lte': 499,
                },
            }),
        ]
        for vr in invalid_rules:
            with self.subTest(vr=vr):
                validator = vr.generate_validator()
                with self.assertRaises(ValidationError):
                    validator(self.img)

    def test_generate_validator_custom_error(self):
        # testing custom width/height error messages
        vr = ValidationRuleDimensions('DIMENSIONS', {
            'w': {
                'gt': 500,
                'err': 'width error message.',
            },
            'h': {
                'eq': 100,
                'err': 'height error message.',
            }
        })
        validator = vr.generate_validator()
        err = 'width error message. height error message'
        with self.assertRaisesMessage(ValidationError, err):
            validator(self.img)

        vr = ValidationRuleDimensions('DIMENSIONS', {
            'w': {
                'gt': 500,
                'err': 'width error message.',
            },
            'h': {
                'eq': 100,
            }
        })
        validator = vr.generate_validator()
        err = 'width error message.'
        with self.assertRaisesMessage(ValidationError, err):
            validator(self.img)

        vr = ValidationRuleDimensions('DIMENSIONS', {
            'w': {
                'gt': 500,
                'err': 'width error message.',
            }
        })
        validator = vr.generate_validator()
        err = 'width error message.'
        with self.assertRaisesMessage(ValidationError, err):
            validator(self.img)

        vr = ValidationRuleDimensions('DIMENSIONS', {
            'lt': (50, 50),
            'err': 'error here!',
        })
        validator = vr.generate_validator()
        err = 'error here!'
        with self.assertRaisesMessage(ValidationError, err):
            validator(self.img)
