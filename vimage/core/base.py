from keyword import iskeyword
from collections import defaultdict

from django.apps import apps
from django.apps.config import MODELS_MODULE_NAME
from django.db.models.fields.files import ImageField

from .exceptions import InvalidKeyError, InvalidValueError
from .const import CONFIG_NAME, nonsense_values_together
from .validator_types import validation_rule_factory


class VimageKey:
    def __init__(self, key):
        """
        ``key`` must be one of the following:

        - ``'app_label.models'``
        - ``'app_label.models.MyModel'``
        - ``'app_label.models.MyModel.field'``

        :param str key: dotted path to models/model/ImageField
        """
        if not isinstance(key, str):
            raise TypeError(f'Each {CONFIG_NAME} dict key should be a '
                            f'<str> type. Current key: "{key}", is '
                            f'<{type(key).__name__}>!')
        self.key = key

    def __str__(self):
        return self.key

    def __repr__(self):
        return f'{self.__class__.__name__}({self.key!r})'

    def split_key(self):
        return self.key.split('.')

    @staticmethod
    def models_in_key(keywords):
        """
        Whether ``django.apps.config.MODELS_MODULE_NAME`` word is the
        second word in the dotted key.

        :return: boolean
        """
        return len(keywords) > 1 and keywords[1] == MODELS_MODULE_NAME

    @staticmethod
    def valid_key_length(keywords):
        """
        Whether length of ``keywords`` is between 2 and 4 (inclusive)

        :param list keywords: list of strings
        :return: boolean
        """
        return len(keywords) in range(2, 5)

    def key_non_empty_str(self):
        """
        Whether ``self.key`` is a non-empty str.

        :return: boolean
        """
        return isinstance(self.key, str) and bool(self.key)

    def validate_dotted_key(self):
        """
        Assumes that ``self.key`` is a str.
        Whether the key defined, is a valid python dotted path to one
        of the following:

        - ``'app_label.models'``
        - ``'app_label.models.MyModel'``
        - ``'app_label.models.MyModel.ImageField_field'``

        :return: boolean
        """
        start = f'[{self.key}]:'
        keywords = self.split_key()
        if not self.valid_key_length(keywords):
            err = f'{start} The key must consists of two to four words, ' \
                  f'separated by dot. It must be a path to one of ' \
                  f'the following: the "models" module, ' \
                  f'a Django Model class or a Django ImageField field.'
            raise InvalidKeyError(err)
        if not self.models_in_key(keywords):
            err = f'{start} The second word of the key, should be ' \
                  f'"{MODELS_MODULE_NAME}", not "{keywords[1]}"!'
            raise InvalidKeyError(err)
        app_label = keywords[0]
        try:
            app_config = apps.get_app_config(app_label=app_label)
            models_module = app_config.models_module.__name__  # noqa: F841
        except LookupError:
            err = f'{start} The app "{app_label}" is either not in ' \
                  f'"INSTALLED_APPS" or it does not exist!'
            raise InvalidKeyError(err)
        except AttributeError:
            err = f'{start} The app "{app_label}" has no "models" ' \
                  f'module defined. Are you sure it exists?'
            raise InvalidKeyError(err)
        else:
            # By now the app exists and has a "models" module
            if len(keywords) == 2:
                return
            keywords = keywords[2:]
            # by now keywords should be at least ['<ModelName>']
            model_classes = list(app_config.get_models())
            model_names = [m.__name__ for m in model_classes]
            model_name = keywords.pop(0)
            if model_name not in model_names:
                err = f'{start} The model "{model_name}" does not exist! ' \
                      f'Available model names: "{", ".join(model_names)}".'
                raise InvalidKeyError(err)
            # by now keywords should be just the field's name ['<ImageField>']
            if len(keywords) == 1:
                image_field_names = [
                    field.name
                    for model in model_classes
                    for field in model._meta.get_fields()
                    if isinstance(field, ImageField)
                ]
                field_name = keywords.pop(0)
                if field_name not in image_field_names:
                    err = f'{start} The field "{field_name}" does not ' \
                          f'exist! Available ImageField names: ' \
                          f'"{", ".join(image_field_names)}".'
                    raise InvalidKeyError(err)

    def key_valid_dotted_format(self):
        """
        Whether ``self.key`` is a syntactically correct python dotted path.

        Valid: ``'path.to.a.package.or.module'``

        Invalid: ``'path/to//module', 'path,to,,module', 'path,to..module'``

        :return: boolean
        """
        split_path = self.split_key()
        return all([
            True
            if word.isidentifier() and not iskeyword(word)
            else False
            for word in split_path
        ])

    def validate_key(self):
        if not self.key_valid_dotted_format():
            err = f'The key "{self.key}" is not a valid python dotted path ' \
                  f'(words separated with the "." dot character). ' \
                  f'Please check for any typos!'
            raise InvalidKeyError(err)
        self.validate_dotted_key()

    def get_app_img_fields(self):
        """
        Calculates and returns all the :class:`~django.db.models.ImageField`
        fields of the app.

        :return: list of Django ``ImageField`` objects
        """
        keywords = self.split_key()
        app_config = apps.get_app_config(app_label=keywords[0])
        app_models = app_config.get_models()
        return [
            field
            for model in app_models
            for field in model._meta.get_fields()
            if isinstance(field, ImageField)
        ]

    def get_specific_model_img_fields(self):
        """
        Assumes that ``self.key`` contains, at least, a model name (class).
        Calculates and returns all the :class:`~django.db.models.ImageField`
        fields of the specified Model.

        :return: list of Django ``ImageField`` objects
        """
        keywords = self.split_key()
        model = apps.get_model(app_label=keywords[0], model_name=keywords[-1])
        return [
            field
            for field in model._meta.get_fields()
            if isinstance(field, ImageField)
        ]

    def get_img_field(self):
        """
        Assumes that ``self.key`` contains the
        :class:`~django.db.models.ImageField` field.
        Finds and returns the specified ``ImageField`` field as a list.

        :return: list with one element (``ImageField`` object)
        """
        keywords = self.split_key()
        model = apps.get_model(app_label=keywords[0], model_name=keywords[-2])
        return [model._meta.get_field(keywords[-1])]

    def get_specificity(self):
        """
        Assumes that the ``self.key`` is valid.
        Calculates the specificity of the key.

        The higher the specificity, the higher the precedence it takes over,
        an other, same key.

        ===============================        =====================
        KEY                                    SPECIFICITY
        ===============================        =====================
        ``'app.models'``                          1
        ``'app.models.MyModel'``                  2
        ``'app.models.MyModel.field'``            3
        ===============================        =====================

        :return: int
        """
        keywords_len = len(self.split_key())
        if keywords_len not in range(2, 5):
            return 0
        return keywords_len - 1

    def get_app_label(self):
        """
        Returns the ``app_label`` of this key.

        Example::

            key = 'myapp.models.MyModel'
            self.get_app_label() == 'myapp'

        :return: str, the app label of the key
        """
        return self.split_key()[0]

    def get_fields(self):
        """
        Assumes that ``self.key`` is valid.
        Returns a list of :class:`~django.db.models.ImageField` fields
        this key affects.

        :return: list
        """
        specificity = self.get_specificity()
        if specificity:
            if specificity == 1:
                return self.get_app_img_fields()
            elif specificity == 2:
                return self.get_specific_model_img_fields()
            else:
                return self.get_img_field()
        return []

    def is_valid(self):
        """
        Whether ``self.key`` is valid.

        :return: None or raises ``InvalidKeyError``
        """
        if not self.key_non_empty_str():
            err = f'The key "{self.key}" should be a non-empty string. It ' \
                  f'must be the dotted path to the app\'s "models" module ' \
                  f'or a "Model" class or an "ImageField" field.'
            raise InvalidKeyError(err)
        self.validate_key()


class VimageValue:
    def __init__(self, value):
        """
        Initialize with each value of the ``VIMAGE`` dict setting.

        :param dict value: dict
        """
        if not isinstance(value, dict):
            raise TypeError(f'Each {CONFIG_NAME} dict value should be a '
                            f'<dict> type. Current value: "{value}", is '
                            f'<{type(value).__name__}>!')
        self.value = value
        self.validators = []

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return f'{self.__class__.__name__}({self.value!r})'

    def validation_rule_generator(self):
        """
        Depending on the key:value pair of ``self.value``, returns the
        corresponding class instance of this validation type.

        :return: class instance
        """
        for key, value in self.value.items():
            yield validation_rule_factory(key, value)

    def validate_value(self):
        """
        Whether the value (not the key) of the validation rule is valid.

        :return: None or raises ``InvalidValueError``
        """
        for vr in self.validation_rule_generator():
            vr.is_valid()

    def nonsense_keys_together(self):
        """
        There is no sense of declaring, in the same rule, ``'DIMENSIONS'``
        and ``'ASPECT_RATIO'``. These values are mutually exclusive.

        :return: None or raises ``InvalidValueError``
        """
        set_keys = set(self.value.keys())
        for nonsense_value_together in nonsense_values_together():
            if nonsense_value_together.issubset(set_keys):
                err = f'The value "{self.value}" contains nonsense values ' \
                      f'that together will not work! Use one of these.' \
                      f'Nonsense values together: ' \
                      f'"{", ".join(nonsense_value_together)}"'
                raise InvalidValueError(err)

    def type_validator_mapping(self):
        """
        Given a set of rules (key: value pair), return a key: value entry
        with the name of the validation type as the key and the validator
        itself (callable) as the value.

        Example::

            # if self.value == {'SIZE', 100}
            self.type_validator_mapping() == {
                'SIZE': <validator_function>,
            }

        :return: dict
        """
        return {
            vr.name: vr.generate_validator()
            for vr in self.validation_rule_generator()
        }

    def is_valid(self):
        """
        Whether ``self.value`` is syntactically correct.

        :return: None or raises ``InvalidValueError``
        """
        if self.value == {}:
            err = f'The value "{self.value}" should be a non-empty dict ' \
                  f'with the proper validation rules. ' \
                  f'Please check the documentation for more information.'
            raise InvalidValueError(err)

        # check if nonsense keys (inside the self.value dict) are defined
        self.nonsense_keys_together()

        # keys are valid, proceed with self.value values
        self.validate_value()


class VimageEntry:
    def __init__(self, key, value):
        """
        The "entry" is a wrapper of :class:`~vimage.core.base.VimageKey`
        and :class:`~vimage.core.base.VimageValue` classes.
        It accepts a str (as the ``VimageKey``) and a
        dict (as the ``VimageValue``).

        Example::

            {
                'myapp.models.MyModel': {
                    'SIZE': 50,
                    'DIMENSIONS': (1000, 1000),
                }
            }

        :param str key: the key, str, of the config dictionary
        :param dict value: the value, dict, of the config dictionary
        """
        self.k = key
        self.v = value
        self.key = VimageKey(self.k)
        self.value = VimageValue(self.v)

    def __str__(self):
        return f'{self.key}: {self.value}'

    def __repr__(self):
        return f'{self.__class__.__name__}({self.k!r}, {self.v!r})'

    def is_valid(self):
        """
        Checks if both ``self.key`` and ``self.value`` are
        syntactically correct.

        :return: None or raises ``InvalidKeyError`` or ``InvalidValueError``
        """
        self.key.is_valid()
        self.value.is_valid()

    @property
    def app_label(self):
        """
        Calls :meth:`~vimage.core.base.VimageKey.get_app_label`

        :return: str
        """
        return self.key.get_app_label()

    @property
    def fields(self):
        """
        Calls :meth:`~vimage.core.base.VimageKey.get_fields`

        :return: list
        """
        return self.key.get_fields()

    @property
    def specificity(self):
        """
        Calls :meth:`~vimage.core.base.VimageKey.get_specificity`

        :return: int
        """
        return self.key.get_specificity()

    @property
    def mapping(self):
        """
        Calls :meth:`~vimage.core.base.VimageValue.type_validator_mapping`

        :return: dict
        """
        return self.value.type_validator_mapping()

    @property
    def entry_info(self):
        """
        Provides the ``app_label``, ``specificity``, ``fields`` and
        a ``mapping`` between validator type's name and the validator itself::

            # If "self.entry" is:
            {
                'myapp.models.MyModel': {
                    'SIZE': 120,
                    'DIMENSIONS': (500, 500),
                }
            }
            # the return value from this method, would be:
            {
                'app_label': 'my_app',
                'specificity': 2,
                'fields': [<ImageField1>, <ImageField2>, ...],
                'mapping': {
                    'SIZE': <ValidationRuleSize.validator>,
                    'DIMENSIONS': <ValidationRuleDimensions.validator>,
                }
            }

        :return: dict of valuable information about this entry
        """
        return {
            'app_label': self.app_label,
            'specificity': self.specificity,
            'fields': self.fields,
            'mapping': self.mapping,
        }


class VimageConfig:
    def __init__(self, config):
        """
        Initialize with the ``VIMAGE`` dict, defined in settings.

        :param dict config: the whole configuration VIMAGE dict setting
        """
        self.config = config

    def __str__(self):
        return str(self.config)

    def __repr__(self):
        return f'{self.__class__.__name__}({self.config!r})'

    def vimage_entry_generator(self):
        """
        For each key-value pair in the ``VIMAGE`` dict, yields a
        :class:`~vimage.core.base.VimageEntry` instance.

        :return: generator
        """
        for key, value in self.config.items():
            yield VimageEntry(key, value)

    def build_info(self):
        """
        Given each ``VimageEntry`` object, build a dict with ``app_label`` as
        the key and ``VimageEntry.entry_info`` dict as the value.
        In other words, put entries that belong to the same app, inside a
        single *bucket*. Next step, is to sort, each bucket, by specificity.

        Return example::

            {
                'myapp':
                    [
                        {
                            'app_label': 'myapp',
                            'fields': [<ImageField1>, <ImageField2>, ...],
                            'specificity': 2,
                            'mapping': {
                                'SIZE': <ValidationRuleSize.validator>,
                                'FORMAT': <ValidationRuleFormat.validator>
                            },
                       },
                       {
                            'app_label': 'myapp',
                            'fields': [<ImageField1>, <ImageField2>, ...],
                            'specificity': 1,
                            'mapping': {
                                'SIZE': <ValidationRuleSize.validator>
                            },
                       }
                    ],
                'myapp2':
                    [
                        {
                            'app_label': 'myapp2',
                            'fields': [<ImageField1>],
                            'specificity': 3,
                            'mapping': {
                                'FORMAT': <ValidationRuleFormat.validator>
                            }
                        },
                    ],
                ...
            }

        :return: dict
        """
        info = defaultdict(list)
        for vimage_entry in self.vimage_entry_generator():
            entry_info = vimage_entry.entry_info
            info[entry_info['app_label']].append(entry_info)
        return info

    @staticmethod
    def sort_info(info):
        """
        Sorts the list inside each bucket per specificity.
        Lower specificity comes first.

        :param dict info: dict of useful info about the VimageEntry
        :return: dict
        """
        for value in info.values():
            value.sort(key=lambda d: d['specificity'])
        return info

    @staticmethod
    def build_draft_registry(info):
        """
        Builds the draft registry, dict, in the following pattern::

            {
                <field1>: {'validator_name': <validator>, ...}
                <field2>: {'validator_name': <validator>, ...}
            }

        Think of the ``draft_registry`` as a pre-build of the
        ``self.registry``.
        Because each "info bucket" is sorted by specificity, the first
        "info" element in each "bucket" will always be a subset of the next
        one.
        If all elements inside the bucket have the same specificity then they
        will refer to different fields, thus, different keys inside
        ``self.draft_registry``.
        If a "bucket list" has three different elements with 1, 2, 3
        specificity values, respectively, then the specific ``ImageField``
        of the last element (specificity == 3) will override any given
        validators from the previous elements (specificity in [1, 2]).

        :param dict info: dict of useful info about the VimageEntry
        :return: dict
        """
        draft_registry = {}
        # info is a DefaultDict <str>: <list>
        for values in info.values():
            # values == list of one or more dicts (see "_build_info" docstring)
            for d in values:
                # each d is a dict
                for field in d['fields']:
                    mapping = d['mapping']
                    if field not in draft_registry:
                        # New field for validation. Add it.
                        # Extra caution here due to reference by name.
                        # A new dict (with new id) must be added to each field.
                        draft_registry[field] = {
                            k: v for k, v in mapping.items()
                        }
                    else:
                        # update/insert validator to existing field
                        for k, v in mapping.items():
                            draft_registry[field][k] = v
        return draft_registry

    @staticmethod
    def build_registry(draft_registry):
        """
        Given the ``draft_registry`` dict, construct the main registry which
        is the basis of adding the validators into each ``ImageField``.

        :param dict draft_registry: a helper dict to help build the registry
        :return: dict
        """
        registry = {}
        for field, mapping in draft_registry.items():
            registry[field] = list(mapping.values())
        return registry

    def add_validators(self):
        """
        The entry point where the ``draft_registry`` and the ``registry`` are
        build and, finally, the validators are added to the corresponding
        ``ImageField`` fields.

        :return: None
        """
        info = self.build_info()
        sorted_info = self.sort_info(info)
        draft_registry = self.build_draft_registry(sorted_info)
        registry = self.build_registry(draft_registry)
        for field, validators in registry.items():
            field.validators += validators
