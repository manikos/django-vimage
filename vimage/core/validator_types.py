from PIL import Image

from django.core.validators import ValidationError
from django.core.files.images import get_image_dimensions
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from django.utils.html import strip_tags

from . import const
from .exceptions import InvalidValueError


# TODO: Move staticmethods to utils.py


class ValidationRuleBase:
    def __init__(self, name, rule):
        self.name = name
        self.rule = rule
        self.equal = const.comparison_operators[const.eq]
        self.trans_name = const.trans_type.get(self.name)

    def __str__(self):
        return f'{self.name}: {self.rule}'

    def __repr__(self):
        return f'{self.__class__.__name__}({self.name!r}, {self.rule!r})'

    def is_valid(self):
        """ Subclass and override this method to check rule's syntax """
        raise NotImplementedError('This method must be overridden.')

    @staticmethod
    def positive_num(x):
        """
        :param int x: int
        :return: boolean
        """
        return x > 0

    def positive_elements(self, iterable):
        """
        Checks if the ``iterable`` contains positive ints.
        ::

            # valid values
            [1, 2, 3]
            [1, 2]
            (1, )

            # invalid values
            [0, 1]
            ['a', 'h']
            [-5, 10]

        :param iterable: an iterable of positive ints
        :return: boolean
        """
        if iterable:
            return all(
                map(lambda x:
                    isinstance(x, int) and self.positive_num(x),
                    iterable)
            )
        return False

    def positive_two_len_tuple(self, t):
        """
        Checks if the tuple, ``t``, is of length 2 and its elements are > 0.
        ::

            # valid values
            (1, 2)

            # invalid values
            (0, 0)
            (2, )
            (1, 2, 3)
            [1, 2]

        :param tuple t: a tuple of two positive ints
        :return: boolean
        """
        if isinstance(t, tuple):
            return len(t) == 2 and self.positive_elements(t)
        return False

    def positive_list(self, ls):
        """
        Checks if the list, ``ls``, contains 2-length tuples of positive ints.
        ::

            # valid values
            [(10, 50), (1, 100), ...]

            # invalid values
            [50, (1, 100)]
            [20]
            [(1, 2, 3)]
            [[1, 2], [3, 4]]

        :param list ls: a list of tuples
        :return: boolean
        """
        if isinstance(ls, list) and ls:
            return all(
                [self.positive_two_len_tuple(t) for t in ls]
            )
        return False

    def only_err_key(self, keys):
        """
        Checks if the keys of the rules is just the ``'err'`` key,
        which is not valid since there is no operator present.

        Example:
        ::

            keys = {
                'err': 'custom error here',
            }

        An operator should be declared (``'gt'``, ``'eq'`` etc)
        along with ``'err'``.

        :param keys: the ``dict_keys`` (operators) of the rule
        :return: None or raises ``InvalidValueError`` exception
        """
        k = list(keys)
        if len(k) == 1 and k[0] == const.err:
            err = f'The value of the rule "{self.name}", "{self.rule}", ' \
                  f'should consist of at least one operator key.'
            raise InvalidValueError(err)

    def nonsense_operators(self, keys):
        """
        Checks if the keys of the rule are nonsense or not.
        ::

            # nonsense rules
            keys = {
                'gt': <value>,
                'eq': <value>,
            }

        since an image cannot be "greater than" a value and at the same time
        "equal" to another value!
        The same applies to other combinations of keys.
        See :func:`~vimage.core.const.nonsense_operators` for more.

        :param keys: the ``dict_keys`` (operators) of the rule
        :return: None or raises ``InvalidValueError`` exception
        """
        set_keys = set(keys)
        for nonsense_operator in const.nonsense_operators():
            if nonsense_operator.issubset(set_keys):
                err = f'Encountered nonsense operators, ' \
                      f'"{", ".join(nonsense_operator)}", ' \
                      f'inside "{self.rule}"!'
                raise InvalidValueError(err)

    def valid_dict_rule_str(self, max_keys=2):
        if len(self.rule) > max_keys:
            err = f'The value of the rule "{self.name}", "{self.rule}", ' \
                  f'should consist of at most two keys: "{const.eq}" or ' \
                  f'"{const.ne}" (mandatory) and "{const.err}" ' \
                  f'(optional, for custom error message).'
            raise InvalidValueError(err)

        # check if only "err" key is defined
        self.only_err_key(self.rule.keys())

        # check if nonsense operators are defined
        self.nonsense_operators(self.rule.keys())

        # Operations that may be applied to str (not int).
        valid_str_keys = [const.eq, const.ne, const.err]
        for k, v in self.rule.items():
            if k not in valid_str_keys:
                err = f'The value of the rule "{self.name}", "{self.rule}", ' \
                      f'has encountered an invalid key "{k}". Valid keys: ' \
                      f'{", ".join(valid_str_keys)}.'
                raise InvalidValueError(err)

    def validate_operators(self, d, valid_value_type):
        """
        Checks if the key-value pairs of the dict, ``d``, are valid ones
        according to the ``valid_value_type`` argument.
        Assumes that ``d`` is a non-empty dict.

        Examples:
        ::

            # VALID
            d = {
                'gte': 50,  # "greater than or equal" to 50 AND
                'lte': 80,  # "less than or equal" to 80
            }
            # and valid_value_type = int, then the above are valid values.

            # INVALID
            d = {
                <opr>: 'a',
                <opr>: 'b',
            }
            # and valid_value_type = int, then the above are invalid values.

            # INVALID
            d = {
                'a': 50,
                'b': 100,
            }
            # 'a' and 'b' are not valid keys.

            # INVALID
            d = {
                <opr>: 50,
                <opr>: (100, 500),
            }
            # if valid_value_type = tuple, then the above are invalid values,
            # since both must be of the same type (tuple is this example).

        :param dict d: dict with valid values as dict values
        :param valid_value_type: str indicating the expected type
        :return: None or raises ``InvalidValueError`` exception
        """
        # check if only "err" key is defined
        self.only_err_key(self.rule.keys())

        # check if nonsense operators are defined
        self.nonsense_operators(self.rule.keys())

        for key, value in d.items():
            if key == const.err:
                continue
            # check for unknown key
            if key not in const.valid_operators_strings:
                err = f'Encountered invalid key, "{key}" inside "{self.rule}"!'
                raise InvalidValueError(err)

            # key is valid, proceed.
            value_type_name = type(value).__name__
            if not isinstance(value, valid_value_type):
                err = f'The value of the key "{key}", inside "{self.rule}", ' \
                      f'should be "{valid_value_type.__name__}". ' \
                      f'Now it\'s type is "{value_type_name}".'
                raise InvalidValueError(err)
            if isinstance(value, int) and not self.positive_num(value):
                err = f'The value of the key "{key}", inside "{self.rule}", ' \
                      f'should be a positive integer. ' \
                      f'Now it\'s value is "{value}".'
                raise InvalidValueError(err)
            elif isinstance(value, tuple) \
                    and not self.positive_two_len_tuple(value):
                err = f'The value of the key "{key}", inside "{self.rule}", ' \
                      f'should consist of tuples with two positive ' \
                      f'integers, each. Now it\'s value is "{value}".'
                raise InvalidValueError(err)

    @staticmethod
    def humanize_dict_rules(rule, human_func=None, unit=''):
        """
        Assumes that ``self.rule`` is a dict.
        Converts each key:value to a string and adds it to a list.

        If ``human_func`` is provided, it'll be applied to each value
        to make it look more human-friendly.

        If ``unit`` is provided, it'll be appended at the end of the string.

        :param dict rule: a dict of rules
        :param human_func: a function to be applied in values
        :param str unit: a str representing the unit (if any)
        :return: list of strings
        """
        human_func = human_func if human_func else lambda x: x
        return [
            f'{const.human_opr.get(opr)} {human_func(v)}{unit}'
            for opr, v in rule.items()
        ]

    @staticmethod
    def format_humanized_rules(rules, sep='', prefix=''):
        """
        Given a list of strings (the humanized rules), return them in a
        prettified format.

        Examples:
        ::

            rules = ['less than 30KB', 'not equal to 15KB']
            print(ValidationRuleBase.format_humanized_rules(rules))
           'less than 30KB and not equal to 15KB'

            rules = ['greater than 1KB', 'less than 50KB', 'not equal to 15KB']
            print(ValidationRuleBase.format_humanized_rules(rules))
            'greater than 1KB, less than 50KB and not equal to 15KB'

        :param list rules: list of humanized rule strings
        :param str sep: separator for the strings
        :param str prefix: str to prefix the return value (if any)
        :return: str
        """
        sep = sep or const.trans_and
        prefix = f'{prefix} ' if prefix else prefix
        no_of_rules = len(rules)
        if no_of_rules == 1:
            return rules[0]
        elif no_of_rules == 2:
            human_rules = f' {sep} '.join(rules)
        else:
            joined = ', '.join(rules[:-1])
            human_rules = f'{joined} {sep} {rules[-1]}'

        return f'{prefix}{human_rules}'

    @staticmethod
    def render_human_rule(rule, safe=True):
        return mark_safe(rule) if safe else strip_tags(rule)

    @staticmethod
    def error_message_template(rule_name, value, rule):
        """
        Set the error template to be displayed in Django admin when the
        uploaded image does not meet the validation rule.

        :param str rule_name: the rule's name (size, format etc)
        :param value: the value under test of the image
        :param str rule: the humanized form of the rule
        :return: str
        """
        return _('<strong>[IMAGE {rule_name}]</strong> Validation error: '
                 '<strong>{value}</strong> does not meet validation rule: '
                 '<strong>{rule}</strong>.').\
            format(rule_name=rule_name.upper(),
                   value=value,
                   rule=rule)

    @staticmethod
    def build_tests(rule, value):
        """
        Given some rules (``rule``) and a ``value`` to test against,
        create the tests as a list and return them.
        In addition, return the custom error (if any) in case the tests fails.
        Assumes that ``rule`` is a non-empty dict.

        Example:

        >>> import operator
        >>> rule = {'gte': 100, 'lte': 500}
        >>> value = 50
        >>> tests = [operator.ge(50, 100), operator.le(50, 500)]

        :param dict rule: the rule(s) to create the tests
        :param value: the value to be tested against the rule(s)
        :return: tuple (list, str)
        """
        err = ''
        tests = []
        for str_opr, validator_value in rule.items():
            if str_opr == const.err:
                err = validator_value
                continue
            opr = const.comparison_operators[str_opr]
            tests.append(opr(value, validator_value))
        return tests, err


class ValidationRuleSize(ValidationRuleBase):
    def __init__(self, name, rule):
        super().__init__(name, rule)
        self.unit = 'KB'

    def humanize_rule(self):
        """
        Convert the rule into a more readable form (in order to render it
        to the Django admin) than the one defined in the settings.

        Examples:

        >>> self.rule = {
        >>>    'gt': 100,
        >>>    'lt': 200,
        >>> }
        >>> print(self.humanize_rule())
        'greater than 100KB and less than 200KB'
        >>> self.rule = 500
        >>> print(self.humanize_rule())
        'equal to 500KB'

        :return: str
        """
        if isinstance(self.rule, int):
            return f'{const.human_opr[const.eq]} {self.rule}{self.unit}'
        else:
            rules = self.humanize_dict_rules(self.rule, unit=self.unit)
            return self.format_humanized_rules(rules)

    def prettify_value(self, value):
        """
        Prettifies the value of the size by appending the ``self.unit``
        at the end of the value.

        :param value: str or dict
        :return: str
        """
        return f'{value}{self.unit}'

    def valid_dict_rule(self):
        """
        Assumes that ``self.rule`` is a non-empty dict.
        Checks if the dict syntax for key ``'SIZE'`` is valid.

        :return: None or raises ``InvalidValueError`` exception
        """
        return self.validate_operators(self.rule, int)

    def is_valid(self):
        """
        Checks if the SIZE validation rule is syntactically correct.

        Valid syntax:
        ::

            'SIZE': <int>
            'SIZE': {
                <operator>: <int>,
                <operator>: <int>,
                'err': 'custom error message',  # optional entry
            }

        :return: None or raises ``InvalidValueError`` exception
        """
        if not isinstance(self.rule, (int, dict)):
            err = f'The value of the rule "{self.name}", "{self.rule}", ' \
                  f'should be either an int or a dict.'
            raise InvalidValueError(err)

        if isinstance(self.rule, int) and not self.positive_num(self.rule):
            err = f'The value of the rule "{self.name}", "{self.rule}", ' \
                  f'should be a positive integer.'
            raise InvalidValueError(err)

        if isinstance(self.rule, dict):
            if not self.rule:
                err = const.errors['empty_dict'].\
                    format(name=self.name, rule=self.rule)
                raise InvalidValueError(err)
            self.valid_dict_rule()

    def generate_validator(self):
        @const.docstring_parameter(rule_name=self.name, rule=self.rule)
        def validator(value):
            """{rule_name}: {rule}"""
            tests = []
            err = ''
            value = value.size // 1024
            if isinstance(self.rule, int):
                tests.append(self.equal(value, self.rule))
            elif isinstance(self.rule, dict):
                tests, err = self.build_tests(self.rule, value)
            if not all(tests):
                err = err or self.error_message_template(
                    self.trans_name,
                    self.prettify_value(value),
                    self.humanize_rule()
                )
                error = self.render_human_rule(err)
                raise ValidationError(error)
        return validator


class ValidationRuleDimensions(ValidationRuleBase):
    def __init__(self, name, rule):
        super().__init__(name, rule)
        self.unit = 'px'

    def humanize_rule(self):
        """
        Convert the rule into a more readable form (in order to render it
        to the Django admin) than the one defined in the settings.

        Examples:

        >>> self.rule = {
        >>>    'w': {'gte': 100}
        >>> }
        >>> print(self.humanize_rule())
        'Width greater than or equal to 100px'
        >>> self.rule = [(10, 10), (20, 20)]
        >>> print(self.humanize_rule())
        'equal to one of the following dimensions 10 x 10px or 20 x 20px'

        :return: str
        """
        if isinstance(self.rule, dict):
            if self.has_width_height_keys():
                wh_rules = []
                for dimension, rules in self.rule.items():
                    # Get the translated dimension
                    dim = const.trans_wh[dimension].capitalize()
                    # Humanize the rules for this dimension
                    rules = self.humanize_dict_rules(rules, unit=self.unit)
                    rules = self.format_humanized_rules(rules=rules)
                    # Prefix with dimension
                    rules = f'{dim} {rules}'
                    wh_rules.append(rules)
                return '. '.join(wh_rules)
            # No w/h defined. Humanize the dict rules
            rules = self.humanize_dict_rules(
                rule=self.rule,
                human_func=self.prettify_value
            )
            return self.format_humanized_rules(rules)
        # Rules are either tuple or list
        equal_to = const.human_opr[const.eq]
        rule = self.rule
        if isinstance(rule, tuple):
            rule = [self.rule]
        list_message = _('one of the following dimensions')
        s = self.format_humanized_rules(
            self.prettify_list(rule),
            sep=const.trans_or,
            prefix=list_message
        )
        return f'{equal_to} {s}'

    def prettify_list(self, ls):
        """
        Formats each tuple in the list in a more readable form.

        :param list ls: a list of one or more tuples
        :return: list of strings
        """
        return [self.prettify_value(t) for t in ls]

    def prettify_value(self, value, sep='x'):
        """
        Formats the dimensions tuple (10, 10) into a more readable form:
        '10 x 10px'.

        :param tuple value: tuple with two positive integers
        :param str sep: a string to separate width and height
        :return: str
        """
        return f'{value[0]} {sep} {value[1]}{self.unit}'

    def has_width_height_keys(self):
        """
        Checks if the ``self.rule``, dict, has either ``'w'`` or ``'h'``
        or both as keys. If so, returns True.

        :return: boolean
        """
        set_keys = set(self.rule.keys())
        if not set_keys:
            return False
        return set_keys.issubset(const.width_height_operators)

    def valid_dict_rule(self):
        """
        Assumes that ``self.rule`` is a non-empty dict.
        Checks if the dict syntax for key ``'DIMENSIONS'`` is valid.

        :return: None or raises ``InvalidValueError`` exception
        """
        if self.has_width_height_keys():
            # each key is either 'w' or 'h' and
            # each value should be a dict (<operator>: <int>)
            for k, v in self.rule.items():
                self.validate_operators(v, int)
        else:
            self.validate_operators(self.rule, tuple)

    def is_valid(self):
        """
        Checks if the DIMENSIONS validation rule is syntactically correct.

        Valid syntax:
        ::

            'DIMENSIONS': <tuple>
            'DIMENSIONS': [<tuple>, <tuple>, ...]
            'DIMENSIONS': {
                <operator>: <tuple>,
                <operator>: <tuple>,
                'err': 'custom error message',  # optional entry
            }
            'DIMENSIONS': {
                'w|h': {
                    <operator>: <int>,
                    <operator>: <int>,
                    'err': 'custom error message',  # optional entry
                }
            }

        :return: None or raises ``InvalidValueError`` exception
        """
        if not isinstance(self.rule, (tuple, list, dict)):
            err = f'The value of the rule "{self.name}", "{self.rule}", ' \
                  f'should be either a tuple, a list or a dict.'
            raise InvalidValueError(err)

        if isinstance(self.rule, tuple) and not \
                self.positive_two_len_tuple(self.rule):
            err = f'The value of the rule "{self.name}", "{self.rule}", ' \
                  f'should consist of two positive integers.'
            raise InvalidValueError(err)

        if isinstance(self.rule, list) and not self.positive_list(self.rule):
            err = f'The value of the rule "{self.name}", "{self.rule}", ' \
                  f'should consist of tuples with two positive integers, each.'
            raise InvalidValueError(err)

        if isinstance(self.rule, dict):
            if not self.rule:
                err = const.errors['empty_dict'].\
                    format(name=self.name, rule=self.rule)
                raise InvalidValueError(err)
            self.valid_dict_rule()

    def generate_validator(self):
        @const.docstring_parameter(rule_name=self.name, rule=self.rule)
        def validation_results(value):
            """{rule_name}: {rule}"""
            tests = []
            err = ''
            test_condition = all
            width, height = get_image_dimensions(value)
            if isinstance(self.rule, tuple):
                tests.append(self.equal(width, self.rule[0]))
                tests.append(self.equal(height, self.rule[1]))
            elif isinstance(self.rule, list):
                test_condition = any
                tests = [
                    self.equal(width, dimensions[0]) and
                    self.equal(height, dimensions[1])
                    for dimensions in self.rule
                ]
            elif isinstance(self.rule, dict):
                if self.has_width_height_keys():
                    err = []
                    for dimension, opr_values in self.rule.items():
                        test_value = width if dimension == const.w else height
                        loc_tests, e = self.build_tests(opr_values, test_value)
                        tests += loc_tests
                        if e:
                            err.append(e)
                    err = ' '.join(err)
                else:
                    for str_opr, validator_value in self.rule.items():
                        if str_opr == const.err:
                            err = validator_value
                            continue
                        opr = const.comparison_operators[str_opr]
                        tests.append(opr(width, validator_value[0]))
                        tests.append(opr(height, validator_value[1]))
            if not test_condition(tests):
                err = err or self.error_message_template(
                    self.trans_name,
                    self.prettify_value((width, height)),
                    self.humanize_rule()
                )
                error = self.render_human_rule(err)
                raise ValidationError(error)
        return validation_results


class ValidationRuleFormat(ValidationRuleBase):
    def humanize_rule(self):
        """
        Convert the rule into a more readable form (in order to render it
        to the Django admin) than the one defined in the settings.

        Examples:

        >>> self.rule = {
        >>>    'ne': ['gif', 'png']
        >>> }
        >>> print(self.humanize_rule())
        'not equal to the following formats GIF and PNG'
        >>> self.rule = ['jpeg', 'webp']
        >>> print(self.humanize_rule())
        'equal to one of the following formats JPEG or WEBP'

        :return: str
        """
        list_message = _('the following formats')
        if isinstance(self.rule, dict):
            # Only one operator is allowed, "ne" or "eq".
            for k, v in self.rule.items():
                trans_opr = const.human_opr[k]
                if isinstance(v, list):
                    rule = self.format_humanized_rules(
                        rules=self.prettify_list(v),
                        prefix=list_message
                    )
                else:
                    rule = self.prettify_value(v)
            return f'{trans_opr} {rule}'

        # rule is either a str or a list of strings.
        equal_to = const.human_opr[const.eq]
        rule = self.rule
        one_of = _('one of')
        if isinstance(rule, str):
            rule = [self.rule]
        s = self.format_humanized_rules(
            self.prettify_list(rule),
            sep=const.trans_or,
            prefix=f'{one_of} {list_message}'
        )
        return f'{equal_to} {s}'

    def prettify_list(self, ls):
        """
        Formats each str in the list in a more readable form.

        :param list ls: a list of one or more str
        :return: list of strings
        """
        return [self.prettify_value(s) for s in ls]

    @staticmethod
    def prettify_value(value):
        """
        Converts value str to uppercase.

        :param str value: str
        :return: str
        """
        return value.upper()

    @staticmethod
    def valid_format(format_str):
        """
        Checks if ``'format_str'`` is an allowed image format extension.

        :param str format_str: a valid image format string
        :return: boolean
        """
        if isinstance(format_str, str):
            return format_str.lower() in const.allowable_web_image_extensions
        return False

    def valid_format_list(self, list_formats):
        """
        Checks if all elements inside the list are allowed image
        format extensions.

        :param list list_formats: a list of image format string
        :return: boolean
        """
        if list_formats:
            return all([self.valid_format(ext) for ext in list_formats])
        return False

    def valid_dict_rule(self):
        """
        Assumes that ``self.rule`` is a non-empty dict.
        Checks if the dict syntax for key ``'FORMAT'`` is valid.

        :return: None or raises ``InvalidValueError`` exception
        """
        self.valid_dict_rule_str()
        for k, v in self.rule.items():
            if k == const.err:
                continue
            if not isinstance(v, (str, list)):
                err = f'The value of the key "{k}", ' \
                      f'inside "{self.name}: {self.rule}", ' \
                      f'should be either a str or a list. ' \
                      f'Now it\'s type is "{type(v).__name__}".'
                raise InvalidValueError(err)
            if isinstance(v, str) and not self.valid_format(v):
                err = f'The value of the key "{k}", inside "{self.name}: ' \
                      f'{self.rule}", should be one of: ' \
                      f'"{", ".join(const.allowable_web_image_extensions)}".'
                raise InvalidValueError(err)
            elif isinstance(v, list) and not self.valid_format_list(v):
                err = f'The value of the key "{k}", inside "{self.name}: ' \
                      f'{self.rule}", should be one or more of: ' \
                      f'"{", ".join(const.allowable_web_image_extensions)}".'
                raise InvalidValueError(err)

    def is_valid(self):
        """
        Checks if the FORMAT validation rule is syntactically correct.

        Valid syntax:
        ::

            'FORMAT': <str>
            'FORMAT': [<str>, <str>, ...]
            'FORMAT': {
                'ne|eq': <str>,
                'err': 'custom error message',  # optional entry
            }
            'FORMAT': {
                'ne|eq': [<str>, <str>, ...],
                'err': 'custom error message',  # optional entry
            }

        :return: None or raises ``InvalidValueError`` exception
        """
        if not isinstance(self.rule, (str, list, dict)):
            err = f'The value of the rule "{self.name}", "{self.rule}", ' \
                  f'should be either a str, list or dict.'
            raise InvalidValueError(err)

        if isinstance(self.rule, str) and not self.valid_format(self.rule):
            err = f'The value of the rule "{self.name}", "{self.rule}", ' \
                  f'should be one of the valid formats: ' \
                  f'"{", ".join(const.allowable_web_image_extensions)}".'
            raise InvalidValueError(err)

        if isinstance(self.rule, list) and not \
                self.valid_format_list(self.rule):
            err = f'The value of the rule "{self.name}", "{self.rule}", ' \
                  f'should be one or more of the valid image formats: ' \
                  f'"{", ".join(const.allowable_web_image_extensions)}".'
            raise InvalidValueError(err)

        if isinstance(self.rule, dict):
            if not self.rule:
                err = const.errors['empty_dict'].\
                    format(name=self.name, rule=self.rule)
                raise InvalidValueError(err)
            self.valid_dict_rule()

    def generate_validator(self):
        def __str_value(value, rule, opr):
            return [(opr(value, rule))]

        def __list_value(value, rule, opr):
            return [
                opr(value, format_string)
                for format_string in rule
            ]

        @const.docstring_parameter(rule_name=self.name, rule=self.rule)
        def validator(value):
            """{rule_name}: {rule}"""
            tests = []
            err = ''
            test_condition = all
            # By now, PIL.Image.verify() has run and "value" is a valid image.
            value = Image.open(value).format.lower()
            if isinstance(self.rule, str):
                tests = __str_value(value, self.rule, self.equal)
            elif isinstance(self.rule, list):
                test_condition = any
                tests = __list_value(value, self.rule, self.equal)
            elif isinstance(self.rule, dict):
                for str_opr, validator_value in self.rule.items():
                    if str_opr == const.err:
                        err = validator_value
                        continue
                    opr = const.comparison_operators[str_opr]
                    if isinstance(validator_value, str):
                        tests = __str_value(value, validator_value, opr)
                    elif isinstance(validator_value, list):
                        tests = __list_value(value, validator_value, opr)
            if not test_condition(tests):
                err = err or self.error_message_template(
                    self.trans_name,
                    self.prettify_value(value),
                    self.humanize_rule()
                )
                error = self.render_human_rule(err)
                raise ValidationError(error)
        return validator


class ValidationRuleAspectRatio(ValidationRuleBase):
    def humanize_rule(self):
        """
        Convert the rule into a more readable form (in order to render it
        to the Django admin) than the one defined in the settings.

        Examples:

        >>> self.rule = {
        >>>    'gt': 1.0,
        >>>    'lt': 2.0,
        >>> }
        >>> print(self.humanize_rule())
        'greater than 1.0 and less than 2.0'
        >>> self.rule = 1.23
        >>> print(self.humanize_rule())
        'equal to 1.23'

        :return: str
        """
        if isinstance(self.rule, float):
            return f'{const.human_opr[const.eq]} {self.rule}'

        else:  # dict
            humanized_list_rules = self.humanize_dict_rules(self.rule)
            human_rules = self.format_humanized_rules(humanized_list_rules)
            return human_rules

    def valid_dict_rule(self):
        """
        Assumes that ``self.rule`` is a non-empty dict.
        Checks if the dict syntax for key ``'ASPECT_RATIO'`` is valid.

        :return: None or raises ``InvalidValueError`` exception
        """
        return self.validate_operators(self.rule, float)

    def is_valid(self):
        """
        Checks if the ASPECT_RATIO validation rule is syntactically correct.

        Valid syntax:
        ::

            'ASPECT_RATIO': <float>
            'ASPECT_RATIO': {
                <operator>: <float>,
                <operator>: <float>,
                'err': 'custom error message',  # optional entry
            }

        :return: None or raises ``InvalidValueError`` exception
        """
        if not isinstance(self.rule, (float, dict)):
            err = f'The value of the rule "{self.name}", "{self.rule}", ' \
                  f'should be either a float or dict.'
            raise InvalidValueError(err)

        if isinstance(self.rule, (int, float)):
            if not self.positive_num(self.rule):
                err = f'The value of the rule "{self.name}", "{self.rule}", ' \
                      f'should be a positive float.'
                raise InvalidValueError(err)

        if isinstance(self.rule, dict):
            if not self.rule:
                err = const.errors['empty_dict'].\
                    format(name=self.name, rule=self.rule)
                raise InvalidValueError(err)
            self.valid_dict_rule()

    def generate_validator(self):
        @const.docstring_parameter(rule_name=self.name, rule=self.rule)
        def validator(value):
            """{rule_name}: {rule}"""
            tests = []
            err = ''
            width, height = get_image_dimensions(value)
            aspect_ratio = round(width / height, 2)
            if isinstance(self.rule, float):
                tests.append(self.equal(aspect_ratio, self.rule))
            else:
                tests, err = self.build_tests(self.rule, aspect_ratio)
            if not all(tests):
                err = err or self.error_message_template(
                    self.trans_name,
                    aspect_ratio,
                    self.humanize_rule()
                )
                error = self.render_human_rule(err)
                raise ValidationError(error)
        return validator


mapping = {
    const.type_size: ValidationRuleSize,
    const.type_dimensions: ValidationRuleDimensions,
    const.type_format: ValidationRuleFormat,
    const.type_aspect_ratio: ValidationRuleAspectRatio,
    # const.type_mode: ValidationRuleMode,
}


def validation_rule_factory(key, value):
    """
    Returns the corresponding class instance based on the ``key`` parameter.

    :param str key: a valid ``VIMAGE`` key
    :param dict value: a valid ``VIMAGE`` value
    :return: class instance
    """
    cls = mapping.get(key, None)
    if cls:
        return cls(key, value)
    err = f'[{key}]: This is not a valid key for a value. Valid values are ' \
          f'"{", ".join(const.valid_types_strings)}"'
    raise InvalidValueError(err)
