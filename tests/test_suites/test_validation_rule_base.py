import os
import operator
from unittest.mock import patch

from django.test import TestCase
from django.utils.safestring import SafeText

from vimage.core import const
from vimage.core import validator_types
from vimage.core.exceptions import InvalidValueError
from tests.apps.myapp.models import MyModel

from .const import IMAGES_PATH, dotted_path, image


class ValidationRuleBaseTestCase1(TestCase):
    def setUp(self):
        self.vr = validator_types.ValidationRuleBase('SIZE', 100)

    def test_init(self):
        self.assertEqual(self.vr.name, 'SIZE')
        self.assertEqual(self.vr.rule, 100)
        self.assertEqual(self.vr.equal, operator.eq)
        self.assertEqual(self.vr.trans_name, const.trans_type[self.vr.name])

    def test_str(self):
        self.assertEqual(str(self.vr), 'SIZE: 100')

    def test_repr(self):
        self.assertEqual(repr(self.vr), 'ValidationRuleBase(\'SIZE\', 100)')
        vr = validator_types.ValidationRuleBase('SIZE', {'gt': 100})
        self.assertEqual(
            repr(vr),
            'ValidationRuleBase(\'SIZE\', {\'gt\': 100})'
        )

    def test_positive_num(self):
        with self.assertRaises(TypeError):
            self.vr.positive_num('')
        self.assertTrue(self.vr.positive_num(1))
        self.assertFalse(self.vr.positive_num(0))
        self.assertFalse(self.vr.positive_num(-1))

    def test_positive_elements(self):
        invalid_values = [
            '',  # not int
            ['a'],  # not int
            [-1, -2],  # not positive
            [0, 0],  # not positive
            [0, 10],  # not positive
            [10, 0],  # not positive
        ]
        valid_values = [
            [1],
            [1, 1],
            [10, 10, 10],
            (1, 2, 3),
        ]
        for value in invalid_values:
            with self.subTest(value=value):
                self.assertFalse(self.vr.positive_elements(value))
        for value in valid_values:
            with self.subTest(value=value):
                self.assertTrue(self.vr.positive_elements(value))

    def test_positive_two_len_tuple(self):
        invalid_values = [
            [1],  # not tuple
            (1,),  # positive but not 2-len
            [10, 10],  # positive, 2-len but not tuple
            (-1, -2),  # not positive
            (1, -2),  # not positive
            (-2, 2),  # not positive
            [10, 0],  # not tuple
        ]
        for value in invalid_values:
            with self.subTest(value=value):
                self.assertFalse(self.vr.positive_two_len_tuple(value))

        self.assertTrue(self.vr.positive_two_len_tuple((1, 2)))

    def test_positive_list(self):
        invalid_values = [
            '',  # not a list
            [''],  # a list but not a tuple inside
            [(-1, -2)],  # negative tuple elements
            [(1, 2, 3)],  # 3-len tuple instead of 2
            [(1, 0)],  # 2-len tuple but not positive
        ]
        for value in invalid_values:
            with self.subTest(value=value):
                self.assertFalse(self.vr.positive_list(value))

        self.assertTrue(self.vr.positive_list(
            [(1, 2), (3, 4)]
        ))

    def test_only_err_key(self):
        vr = validator_types.ValidationRuleBase('SIZE', {'err': 'aa'})
        err = f'The value of the rule "SIZE", "{{\'err\': \'aa\'}}", ' \
              f'should consist of at least one operator key.'
        with self.assertRaisesMessage(InvalidValueError, err):
            vr.only_err_key(vr.rule.keys())

        vr = validator_types.ValidationRuleBase('SIZE', {'gt': 1, 'err': 'a'})
        self.assertIsNone(vr.only_err_key(vr.rule.keys()))

    def test_nonsense_operators(self):
        vr = validator_types.ValidationRuleBase('SIZE', {'gte': 1, 'eq': 2})
        with self.assertRaises(InvalidValueError):
            vr.validate_operators(vr.rule, int)

        vr = validator_types.ValidationRuleBase('SIZE', {'gte': 1, 'lte': 2})
        self.assertIsNone(vr.validate_operators(vr.rule, int))

    def test_valid_dict_rule_str(self):
        # too many keys (invalid)
        vr = validator_types.ValidationRuleBase('FORMAT', {
            'eq': 'jpeg',
            'ne': 'png',
            'other': 'other',
        })
        with self.assertRaises(InvalidValueError):
            vr.valid_dict_rule_str()

        # test that "only_err_key()" is called
        vr = validator_types.ValidationRuleBase('FORMAT', {'err': 'aa'})
        with patch(dotted_path('validator_types', 'ValidationRuleBase',
                               'only_err_key')) as m:
            vr.valid_dict_rule_str()
            self.assertTrue(m.called)

        # test that "nonsense_operators()" is called
        vr = validator_types.ValidationRuleBase('FORMAT', {
            'ne': 'jpeg',
            'eq': 'png',
        })
        with patch(dotted_path('validator_types', 'ValidationRuleBase',
                               'nonsense_operators')) as m:
            vr.valid_dict_rule_str()
            self.assertTrue(m.called)

        # invalid key (gt) for str comparisons (invalid)
        vr = validator_types.ValidationRuleBase('FORMAT', {
            'ne': 'jpeg',
            'gt': 'png',
        })
        err = f'The value of the rule "FORMAT", ' \
              f'"{{\'ne\': \'jpeg\', \'gt\': \'png\'}}", has encountered ' \
              f'an invalid key "gt". Valid keys: eq, ne, err.'
        with self.assertRaisesMessage(InvalidValueError, err):
            vr.valid_dict_rule_str()

        # valid keys
        valid_keys = [
            validator_types.ValidationRuleBase(
                'SIZE', {'ne': 'a', 'err': 'a'}
            ),
            validator_types.ValidationRuleBase('SIZE', {'ne': 'jpeg'})
        ]
        for valid_key in valid_keys:
            with self.subTest(valid_key=valid_key):
                self.assertIsNone(valid_key.valid_dict_rule_str())


class ValidationRuleBaseTestCase2(TestCase):
    def test_validate_operators_keys(self):
        # test that "only_err_key()" is called
        vr = validator_types.ValidationRuleBase('FORMAT', {'err': 'aa'})
        with patch(dotted_path('validator_types', 'ValidationRuleBase',
                               'only_err_key')) as m:
            vr.validate_operators(vr.rule, int)
            self.assertTrue(m.called)

        # test that "nonsense_operators()" is called
        vr = validator_types.ValidationRuleBase('SIZE', {'gte': 1, 'eq': 2})
        with patch(dotted_path('validator_types', 'ValidationRuleBase',
                               'nonsense_operators')) as m:
            vr.validate_operators(vr.rule, int)
            self.assertTrue(m.called)

        # invalid rule keys (unknown)
        vr = validator_types.ValidationRuleBase('SIZE', {'a': 1})
        err = f'Encountered invalid key, "a" inside "{{\'a\': 1}}"!'
        with self.assertRaisesMessage(InvalidValueError, err):
            vr.validate_operators(vr.rule, int)

        valid_operators_int = [
            {'gt': 100, 'lte': 100},
            {'gt': 1, 'lt': 2},
            {'ne': 900},
        ]
        for value in valid_operators_int:
            with self.subTest(value=value):
                vr.rule = value
                self.assertIsNone(vr.validate_operators(value, int))

        valid_operators_tuple = [
            {'gt': (100, 100), 'lte': (500, 500)},
            {'gt': (100, 100), 'lt': (200, 200)},
            {'ne': (500, 500)},
        ]
        for value in valid_operators_tuple:
            with self.subTest(value=value):
                vr.rule = value
                self.assertIsNone(vr.validate_operators(value, tuple))

    def test_validate_operators_dict_values(self):
        # rule value is a str, it should be an int
        vr = validator_types.ValidationRuleBase('SIZE', {'gte': ''})
        err = f'The value of the key "gte", inside "{{\'gte\': \'\'}}", ' \
              f'should be "int". Now it\'s type is "str".'
        with self.assertRaisesMessage(InvalidValueError, err):
            vr.validate_operators(vr.rule, int)

        # rule value is a negative int, it should be positive
        vr = validator_types.ValidationRuleBase('SIZE', {'gte': -1})
        err = f'The value of the key "gte", inside "{{\'gte\': -1}}", ' \
              f'should be a positive integer. Now it\'s value is "-1".'
        with self.assertRaisesMessage(InvalidValueError, err):
            vr.validate_operators(vr.rule, int)

        # rule value's tuple contains negative element, must be all positive
        vr = validator_types.ValidationRuleBase('SIZE', {'gte': (1, -1)})
        err = f'The value of the key "gte", inside "{{\'gte\': (1, -1)}}", ' \
              f'should consist of tuples with two positive ' \
              f'integers, each. Now it\'s value is "(1, -1)".'
        with self.assertRaisesMessage(InvalidValueError, err):
            vr.validate_operators(vr.rule, tuple)

        # valid rule values
        vr = validator_types.ValidationRuleBase('SIZE', {'gte': 1})
        self.assertIsNone(vr.validate_operators(vr.rule, int))
        vr = validator_types.ValidationRuleBase('DIMENSIONS', {
            'gt': (100, 100)
        })
        self.assertIsNone(vr.validate_operators(vr.rule, tuple))
        vr = validator_types.ValidationRuleBase('DIMENSIONS', {
            'gt': (100, 100),
            'err': 'custom error here',
        })
        self.assertIsNone(vr.validate_operators(vr.rule, tuple))


class ValidationRuleBaseTestCase3(ValidationRuleBaseTestCase1):
    def test_humanize_dict_rules(self):
        rule = {'gt': 10, 'lt': 20}
        unit = 'KB'
        human_dict_rules = self.vr.humanize_dict_rules(rule=rule, unit=unit)
        self.assertIsInstance(human_dict_rules, list)

        # No human_func provided. Values (10, 20) displayed as is.
        self.assertIn('greater than 10KB', human_dict_rules)
        self.assertIn('less than 20KB', human_dict_rules)

        rule = {'ne': 'jpeg'}
        # human_func is str.upper. Each value should be uppercase.
        human_dict_rules = self.vr.humanize_dict_rules(rule, str.upper)
        self.assertIn('not equal to JPEG', human_dict_rules)

    def test_format_humanized_rules_default_kwargs(self):
        # single rule - keep defaults
        rules = ['greater than 10KB']
        human_rules = self.vr.format_humanized_rules(rules=rules)
        self.assertIsInstance(human_rules, str)
        self.assertEqual(human_rules, 'greater than 10KB')

        # two rules - keep defaults
        rules = ['greater than 10KB', 'less than 20KB']
        human_rules = self.vr.format_humanized_rules(rules=rules)
        self.assertEqual(human_rules, 'greater than 10KB and less than 20KB')

        # three rules - keep defaults
        rules = ['greater than 10KB', 'less than 20KB', 'not equal to 15KB']
        human_rules = self.vr.format_humanized_rules(rules=rules)
        self.assertEqual(
            human_rules,
            'greater than 10KB, less than 20KB and not equal to 15KB'
        )

    def test_format_humanized_rules_custom_separator(self):
        sep = 'or'

        # single rule - "or" separator
        rules = ['greater than 10KB']
        human_rules = self.vr.format_humanized_rules(rules=rules, sep=sep)
        self.assertEqual(human_rules, 'greater than 10KB')

        # two rules - "or" separator
        rules = ['greater than 10KB', 'less than 20KB']
        human_rules = self.vr.format_humanized_rules(rules=rules, sep=sep)
        self.assertEqual(human_rules, 'greater than 10KB or less than 20KB')

        # three rules - "or" separator
        rules = ['greater than 10KB', 'less than 20KB', 'not equal to 15KB']
        human_rules = self.vr.format_humanized_rules(rules=rules, sep=sep)
        self.assertEqual(
            human_rules,
            'greater than 10KB, less than 20KB or not equal to 15KB'
        )

    def test_format_humanized_rules_custom_prefix(self):
        pref = 'AA'

        # single rule - custom prefix
        rules = ['greater than 10KB']
        human_rules = self.vr.format_humanized_rules(rules=rules, prefix=pref)
        self.assertEqual(human_rules, 'greater than 10KB')

        # two rules - custom prefix
        rules = ['greater than 10KB', 'less than 20KB']
        human_rules = self.vr.format_humanized_rules(rules=rules, prefix=pref)
        self.assertEqual(
            human_rules,
            'AA greater than 10KB and less than 20KB'
        )

        # three rules - custom prefix
        rules = ['greater than 10KB', 'less than 20KB', 'not equal to 15KB']
        human_rules = self.vr.format_humanized_rules(rules=rules, prefix=pref)
        self.assertEqual(
            human_rules,
            'AA greater than 10KB, less than 20KB and not equal to 15KB'
        )

    def test_render_human_rule(self):
        rule = '<strong>greater than 10KB<strong>'

        safe_rule = self.vr.render_human_rule(rule)
        self.assertIsInstance(safe_rule, SafeText)

        safe_rule = self.vr.render_human_rule(rule, safe=False)
        self.assertIsInstance(safe_rule, str)

    def test_error_message_template(self):
        template = self.vr.error_message_template('SIZE', '100KB', 'rule here')
        self.assertEqual(
            '<strong>[IMAGE SIZE]</strong> Validation error: '
            '<strong>100KB</strong> does not meet validation rule: '
            '<strong>rule here</strong>.',
            template
        )

    def test_build_tests(self):
        vr = validator_types.ValidationRuleBase('', {'gte': 100, 'lte': 500})
        self.assertEqual(
            vr.build_tests(vr.rule, 400),
            ([operator.ge(400, 100), operator.le(400, 500)], '')
        )

        vr = validator_types.ValidationRuleBase('', {
            'gte': 100,
            'lte': 500,
            'err': 'hello',
        })
        self.assertEqual(
            vr.build_tests(vr.rule, 400),
            ([operator.ge(400, 100), operator.le(400, 500)], 'hello')
        )

        vr = validator_types.ValidationRuleBase('', {
            'eq': 'jpeg',
            'err': 'hello',
        })
        self.assertEqual(
            vr.build_tests(vr.rule, 'jpeg'),
            ([operator.eq('jpeg', 'jpeg')], 'hello')
        )


class ValidationRuleFactoryTestCase(TestCase):
    def test_validation_rule_factory_valid(self):
        self.assertIsInstance(
            validator_types.validation_rule_factory('SIZE', ''),
            validator_types.ValidationRuleSize
        )
        self.assertIsInstance(
            validator_types.validation_rule_factory('DIMENSIONS', ''),
            validator_types.ValidationRuleDimensions
        )
        self.assertIsInstance(
            validator_types.validation_rule_factory('FORMAT', ''),
            validator_types.ValidationRuleFormat
        )
        self.assertIsInstance(
            validator_types.validation_rule_factory('ASPECT_RATIO', ''),
            validator_types.ValidationRuleAspectRatio
        )

    def test_validation_rule_factory_invalid(self):
        inv = 'INVALID_TYPE'
        err = f'[{inv}]: This is not a valid key for a value. ' \
              f'Valid values are "SIZE, DIMENSIONS, FORMAT, ASPECT_RATIO"'
        with self.assertRaisesMessage(InvalidValueError, err):
            validator_types.validation_rule_factory(inv, '')


class ValidatorTestCase(TestCase):
    def setUp(self):
        path_to_image = os.path.join(IMAGES_PATH, '500x498-100KB.jpeg')
        img = image(name='test_image_size', path=path_to_image)
        my_model = MyModel(heading='heading', img=img, number=1)
        self.img = my_model.img
