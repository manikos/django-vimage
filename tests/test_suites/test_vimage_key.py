from django.test import TestCase

from tests.apps.myapp import models as my_app_models

from vimage.core.base import VimageKey
from vimage.core.exceptions import InvalidKeyError


def all_image_fields():
    return [
        my_app_models.MyModel._meta.get_field('img'),
        my_app_models.AnotherModel._meta.get_field('thumb'),
        my_app_models.AnotherModel._meta.get_field('image'),
        my_app_models.GreatModel._meta.get_field('picture'),
        my_app_models.GreatModel._meta.get_field('large_img')
    ]


def another_model_image_fields():
    return [
        my_app_models.AnotherModel._meta.get_field('thumb'),
        my_app_models.AnotherModel._meta.get_field('image')
    ]


def specific_image():
    return [my_app_models.MyModel._meta.get_field('img')]


class VimageKeyTestCase(TestCase):
    def test_key(self):
        vk = VimageKey('app')
        self.assertEqual(vk.key, 'app')
        err = f'Each VIMAGE dict key should be a ' \
              f'<str> type. Current key: "1", is <int>!'
        with self.assertRaisesMessage(TypeError, err):
            VimageKey(1)

    def test_str(self):
        vk = VimageKey('app')
        self.assertEqual(str(vk), 'app')

    def test_repr(self):
        vk = VimageKey('app')
        self.assertEqual(repr(vk), "VimageKey('app')")
        self.assertIsInstance(eval(repr(vk)), VimageKey)

    def test_split_key(self):
        vk = VimageKey('myapp.models.MyModel')
        self.assertListEqual(vk.split_key(), ['myapp', 'models', 'MyModel'])
        vk = VimageKey('')
        self.assertListEqual(vk.split_key(), [''])

    def test_models_in_key(self):
        vk = VimageKey('myapp.models')
        self.assertTrue(vk.models_in_key(vk.split_key()))
        vk = VimageKey('myapp.models.MyModel')
        self.assertTrue(vk.models_in_key(vk.split_key()))
        vk = VimageKey('myapp')
        self.assertFalse(vk.models_in_key(vk.split_key()))

    def test_valid_key_length(self):
        valid_keys = [
            VimageKey('.'.join(['a'] * 2)),  # 'a.a',
            VimageKey('.'.join(['a'] * 3)),  # 'a.a.a'
            VimageKey('.'.join(['a'] * 4)),  # 'a.a.a.a'
        ]
        for vk in valid_keys:
            with self.subTest(vk=vk):
                self.assertTrue(vk.valid_key_length(vk.split_key()))

        invalid_keys = [
            VimageKey(''),
            VimageKey('a'),
            VimageKey('.'.join(['a'] * 5)),  # 'a.a.a.a.a',
        ]
        for vk in invalid_keys:
            with self.subTest(vk=vk):
                self.assertFalse(vk.valid_key_length(vk.split_key()))

    def test_key_non_empty_str(self):
        vk = VimageKey('')
        self.assertFalse(vk.key_non_empty_str())
        vk = VimageKey('myapp')
        self.assertTrue(vk.key_non_empty_str())

    def test_validate_dotted_key(self):
        # At least the "models" word is required
        vk = VimageKey('myapp')
        err = f'[myapp]: The key must consists of two to four words, ' \
              f'separated by dot. It must be a path to one of ' \
              f'the following: the "models" module, ' \
              f'a Django Model class or a Django ImageField field.'
        with self.assertRaisesMessage(InvalidKeyError, err):
            vk.validate_dotted_key()

        vk = VimageKey('myapp.MyModel')
        err = f'[myapp.MyModel]: The second word of the key, should be ' \
              f'"models", not "MyModel"!'
        with self.assertRaisesMessage(InvalidKeyError, err):
            vk.validate_dotted_key()

        # Non-valid app label
        vk = VimageKey('nonexistapp.models.MyModel')
        err = f'[nonexistapp.models.MyModel]: The app "nonexistapp" is ' \
              f'either not in "INSTALLED_APPS" or it does not exist!'
        with self.assertRaisesMessage(InvalidKeyError, err):
            vk.validate_dotted_key()

        # App without a "models" module
        vk = VimageKey('no_model.models.MyModel')
        err = f'[no_model.models.MyModel]: The app "no_model" has no ' \
              f'"models" module defined. Are you sure it exists?'
        with self.assertRaisesMessage(InvalidKeyError, err):
            vk.validate_dotted_key()

        # A valid app with "models" module
        vk = VimageKey('myapp.models')
        self.assertIsNone(vk.validate_dotted_key())

        # A valid app with a non-valid model
        vk = VimageKey('myapp.models.NonExistModel')
        err = f'[myapp.models.NonExistModel]: The model "NonExistModel" ' \
              f'does not exist! ' \
              f'Available model names: "MyModel, AnotherModel, GreatModel".'
        with self.assertRaisesMessage(InvalidKeyError, err):
            vk.validate_dotted_key()

        # A valid app, with "models" module, but non-valid ImageField
        vk = VimageKey('myapp2.models.Hello.image')
        err = f'[myapp2.models.Hello.image]: The field "image" does not ' \
              f'exist! Available ImageField names: "img".'
        with self.assertRaisesMessage(InvalidKeyError, err):
            vk.validate_dotted_key()

        # A perfectly valid app!
        vk = VimageKey('myapp.models.MyModel.img')
        self.assertIsNone(vk.validate_dotted_key())

    def test_key_valid_dotted_format(self):
        invalid_keys = [
            VimageKey(''),
            VimageKey('myapp.class'),
            VimageKey('myapp.def'),
        ]
        for vk in invalid_keys:
            with self.subTest(vk=vk):
                self.assertFalse(vk.key_valid_dotted_format())

        valid_keys = [
            VimageKey('myapp'),
            VimageKey('myapp.something.other'),
        ]
        for vk in valid_keys:
            with self.subTest(vk=vk):
                self.assertTrue(vk.key_valid_dotted_format())

    def test_validate_key(self):
        vk = VimageKey('myapp.models.MyModel')
        self.assertIsNone(vk.validate_key())

        invalid_keys = [
            VimageKey('just plain text!'),
            VimageKey('myapp,models,MyModel'),
            VimageKey('myapp.MyModel,img'),
            VimageKey('myapp.MyModel..img'),
            VimageKey('.myapp.MyModel.img'),  # leading dot
            VimageKey('myapp.MyModel.img.'),  # trailing dot
        ]
        for vk in invalid_keys:
            with self.subTest(vk=vk):
                err = f'The key "{vk.key}" is not a valid python dotted ' \
                      f'path (words separated with the "." dot character). ' \
                      f'Please check for any typos!'
                with self.assertRaisesMessage(InvalidKeyError, err):
                    vk.validate_key()

    def test_get_app_img_fields(self):
        vk = VimageKey('myapp.models')
        self.assertListEqual(vk.get_app_img_fields(), all_image_fields())

    def test_get_specific_model_img_fields(self):
        vk = VimageKey('myapp.models.AnotherModel')

        self.assertListEqual(
            vk.get_specific_model_img_fields(),
            another_model_image_fields()
        )

    def test_get_img_field(self):
        vk = VimageKey('myapp.models.MyModel.img')
        self.assertListEqual(vk.get_img_field(), specific_image())

    def test_get_specificity(self):
        vk = VimageKey('myapp')
        self.assertEqual(vk.get_specificity(), 0)

        vk = VimageKey('myapp.models')
        self.assertEqual(vk.get_specificity(), 1)

        vk = VimageKey('myapp.models.MyModel')
        self.assertEqual(vk.get_specificity(), 2)

        vk = VimageKey('myapp.models.MyModel.img')
        self.assertEqual(vk.get_specificity(), 3)

    def test_get_app_label(self):
        vk = VimageKey('myapp.models')
        self.assertEqual(vk.get_app_label(), 'myapp')

    def test_get_fields(self):
        vk1 = VimageKey('myapp')
        vk2 = VimageKey('myapp.models.MyModel.img.other')

        vk3 = VimageKey('myapp.models')
        vk4 = VimageKey('myapp.models.AnotherModel')
        vk5 = VimageKey('myapp.models.MyModel.img')
        self.assertListEqual(vk1.get_fields(), [])
        self.assertListEqual(vk2.get_fields(), [])

        self.assertListEqual(vk3.get_fields(), all_image_fields())
        self.assertListEqual(vk4.get_fields(), another_model_image_fields())
        self.assertListEqual(vk5.get_fields(), specific_image())

    def test_is_valid(self):
        vk = VimageKey('')
        err = f'The key "" should be a non-empty string. It ' \
              f'must be the dotted path to the app\'s "models" module ' \
              f'or a "Model" class or an "ImageField" field.'
        with self.assertRaisesMessage(InvalidKeyError, err):
            vk.is_valid()

        valid_keys = [
            VimageKey('myapp.models'),
            VimageKey('myapp.models.MyModel'),
            VimageKey('myapp.models.MyModel.img'),
        ]
        for vk in valid_keys:
            with self.subTest(vk=vk):
                self.assertIsNone(vk.is_valid())
