from unittest.mock import patch
from types import GeneratorType

from django.test import TestCase

from vimage.core.base import VimageEntry, VimageConfig

from tests.apps.myapp import models as my_app_models
from .const import dotted_path


class VimageConfigTestCase(TestCase):
    def test_entry(self):
        vc = VimageConfig({})
        self.assertEqual(vc.config, {})

    def test_str(self):
        vc = VimageConfig({})
        self.assertEqual(str(vc), '{}')

    def test_repr(self):
        vc = VimageConfig({})
        self.assertEqual(repr(vc), 'VimageConfig({})')
        self.assertIsInstance(eval(repr(vc)), VimageConfig)

    def test_vimage_entry_generator(self):
        vc = VimageConfig({
            'myapp.models': {
                'SIZE': 900
            },
        })
        gen = vc.vimage_entry_generator()

        # Returned value is a generator
        self.assertIsInstance(gen, GeneratorType)
        # First value is a VimageEntry object
        self.assertIsInstance(next(gen), VimageEntry)
        # No more values!
        with self.assertRaises(StopIteration):
            next(gen)

    def test_build_info(self):
        vc = VimageConfig({
            'myapp.models': {
                'SIZE': 900,
            },
            'myapp.models.MyModel': {
                'SIZE': 500,
            },
            'myapp2.models': {
                'DIMENSIONS': (100, 100),
            },
        })
        info = vc.build_info()
        # "info" is a dict
        self.assertIsInstance(info, dict)
        # "info" has keys equal to the number of the app_labels declared
        self.assertEqual(sorted(info.keys()), ['myapp', 'myapp2'])
        # each value of "info" is a list
        self.assertIsInstance(info['myapp'], list)
        self.assertIsInstance(info['myapp2'], list)
        # The value of the key "myapp" contains 2 elements
        self.assertEqual(len(info['myapp']), 2)
        # Each of those elements is a dict with the following keys
        self.assertEqual(
            sorted(info['myapp'][0].keys()),
            ['app_label', 'fields', 'mapping', 'specificity']
        )

    def test_sort_info(self):
        orig_info = {
            'myapp':
                [
                    {
                        'app_label': 'myapp',
                        'fields': ['img3'],
                        'specificity': 3,
                        'mapping': {},
                    },
                    {
                        'app_label': 'myapp',
                        'fields': ['img1', 'img3'],
                        'specificity': 2,
                        'mapping': {},
                    },
                    {
                        'app_label': 'myapp',
                        'fields': ['img1', 'img2', 'img3'],
                        'specificity': 1,
                        'mapping': {},
                    },
                ],
        }
        expected_info = {
            'myapp':
                [
                    {
                        'app_label': 'myapp',
                        'fields': ['img1', 'img2', 'img3'],
                        'specificity': 1,
                        'mapping': {},
                    },
                    {
                        'app_label': 'myapp',
                        'fields': ['img1', 'img3'],
                        'specificity': 2,
                        'mapping': {},
                    },
                    {
                        'app_label': 'myapp',
                        'fields': ['img3'],
                        'specificity': 3,
                        'mapping': {},
                    },
                ],
        }
        sorted_info = VimageConfig.sort_info(orig_info)
        self.assertDictEqual(sorted_info, expected_info)

    def test_build_draft_registry_1(self):
        info = {
            'myapp':
                [
                    {
                        'app_label': 'myapp',
                        'fields': ['img1', 'img2', 'img3'],
                        'specificity': 1,
                        'mapping': {
                            'SIZE': '100',
                            'DIMENSIONS': '100x100',
                        }
                    },
                    {
                        'app_label': 'myapp',
                        'fields': ['img1', 'img3'],
                        'specificity': 2,
                        'mapping': {
                            'FORMAT': 'png',
                        }
                    },
                    {
                        'app_label': 'myapp',
                        'fields': ['img3'],
                        'specificity': 3,
                        'mapping': {
                            'SIZE': '500',
                            'DIMENSIONS': '500x640',
                            'FORMAT': 'jpeg',
                        }
                    },
                ],
        }
        expected_draft_registry = {
            'img1': {'SIZE': '100', 'DIMENSIONS': '100x100', 'FORMAT': 'png'},
            'img2': {'SIZE': '100', 'DIMENSIONS': '100x100'},
            'img3': {'SIZE': '500', 'DIMENSIONS': '500x640', 'FORMAT': 'jpeg'},
        }
        draft_registry = VimageConfig.build_draft_registry(info)
        self.assertDictEqual(draft_registry, expected_draft_registry)

    def test_build_draft_registry_2(self):
        info = {
            'myapp':
                [
                    {
                        'app_label': 'myapp',
                        'fields': ['img1', 'img2', 'img3'],
                        'specificity': 1,
                        'mapping': {
                            'SIZE': '100',
                            'DIMENSIONS': '100x100',
                        }
                    },
                    {
                        'app_label': 'myapp',
                        'fields': ['img3'],
                        'specificity': 3,
                        'mapping': {
                            'SIZE': '500',
                            'DIMENSIONS': '500x640',
                            'FORMAT': 'jpeg',
                        }
                    },
                ],
        }
        expected_draft_registry = {
            'img1': {'SIZE': '100', 'DIMENSIONS': '100x100'},
            'img2': {'SIZE': '100', 'DIMENSIONS': '100x100'},
            'img3': {'SIZE': '500', 'DIMENSIONS': '500x640', 'FORMAT': 'jpeg'},
        }
        draft_registry = VimageConfig.build_draft_registry(info)
        self.assertDictEqual(draft_registry, expected_draft_registry)

    def test_build_draft_registry_3(self):
        info = {
            'myapp':
                [
                    {
                        'app_label': 'myapp',
                        'fields': ['img1', 'img2'],
                        'specificity': 2,
                        'mapping': {
                            'FORMAT': 'png',
                        }
                    },
                    {
                        'app_label': 'myapp',
                        'fields': ['img3', 'img4'],
                        'specificity': 2,
                        'mapping': {
                            'SIZE': '500',
                            'DIMENSIONS': '500x640',
                            'FORMAT': 'jpeg',
                        }
                    },
                ],
        }
        expected_draft_registry = {
            'img1': {'FORMAT': 'png'},
            'img2': {'FORMAT': 'png'},
            'img3': {'SIZE': '500', 'DIMENSIONS': '500x640', 'FORMAT': 'jpeg'},
            'img4': {'SIZE': '500', 'DIMENSIONS': '500x640', 'FORMAT': 'jpeg'},
        }
        draft_registry = VimageConfig.build_draft_registry(info)
        self.assertDictEqual(draft_registry, expected_draft_registry)

    def test_build_draft_registry_4(self):
        info = {
            'myapp1':
                [
                    {
                        'app_label': 'myapp',
                        'fields': ['img1', 'img2', 'img3'],
                        'specificity': 1,
                        'mapping': {
                            'SIZE': '100',
                            'DIMENSIONS': '100x100',
                        }
                    },
                ],
            'myapp2':
                [
                    {
                        'app_label': 'myapp',
                        'fields': ['img4', 'img5', 'img6'],
                        'specificity': 1,
                        'mapping': {
                            'DIMENSIONS': '666x666',  # :)
                        }
                    },
                ],
        }
        expected_draft_registry = {
            'img1': {'SIZE': '100', 'DIMENSIONS': '100x100'},
            'img2': {'SIZE': '100', 'DIMENSIONS': '100x100'},
            'img3': {'SIZE': '100', 'DIMENSIONS': '100x100'},
            'img4': {'DIMENSIONS': '666x666'},
            'img5': {'DIMENSIONS': '666x666'},
            'img6': {'DIMENSIONS': '666x666'},
        }
        draft_registry = VimageConfig.build_draft_registry(info)
        self.assertDictEqual(draft_registry, expected_draft_registry)

    def test_build_registry_1(self):
        draft_registry = {
            'img1': {'SIZE': '100', 'DIMENSIONS': '100x100'},
            'img2': {'SIZE': '100', 'DIMENSIONS': '100x100'},
            'img3': {'SIZE': '100', 'DIMENSIONS': '100x100'},
            'img4': {'DIMENSIONS': '666x666'},
            'img5': {'DIMENSIONS': '666x666'},
            'img6': {'DIMENSIONS': '666x666'},
        }
        expected_registry = {
            'img1': ['100', '100x100'],
            'img2': ['100', '100x100'],
            'img3': ['100', '100x100'],
            'img4': ['666x666'],
            'img5': ['666x666'],
            'img6': ['666x666'],
        }
        registry = VimageConfig.build_registry(draft_registry)
        self.assertDictEqual(registry, expected_registry)

    def test_build_registry_2(self):
        draft_registry = {
            'img1': {'SIZE': '100', 'DIMENSIONS': '100x100', 'FORMAT': 'png'},
            'img2': {'SIZE': '100', 'DIMENSIONS': '100x100'},
            'img3': {'SIZE': '500', 'DIMENSIONS': '500x640', 'FORMAT': 'jpeg'},
        }
        expected_registry = {
            'img1': ['100', '100x100', 'png'],
            'img2': ['100', '100x100'],
            'img3': ['500', '500x640', 'jpeg'],
        }
        registry = VimageConfig.build_registry(draft_registry)
        self.assertDictEqual(registry, expected_registry)

    def test_add_validators_methods_called(self):
        m_path = dotted_path('base', 'VimageConfig', 'build_info')
        with patch(m_path) as m:
            VimageConfig({'myapp': {}}).add_validators()
            self.assertTrue(m.called)

        m_path = dotted_path('base', 'VimageConfig', 'sort_info')
        with patch(m_path) as m:
            VimageConfig({'myapp': {}}).add_validators()
            self.assertTrue(m.called)

        m_path = dotted_path('base', 'VimageConfig', 'build_draft_registry')
        with patch(m_path) as m:
            VimageConfig({'myapp': {}}).add_validators()
            self.assertTrue(m.called)

        m_path = dotted_path('base', 'VimageConfig', 'build_registry')
        with patch(m_path) as m:
            VimageConfig({'myapp': {}}).add_validators()
            self.assertTrue(m.called)


class VimageConfigAddValidatorsTestCase(TestCase):
    def setUp(self):
        self.img = my_app_models.MyModel._meta.get_field('img')
        self.img.validators = []

    def test_add_validators_size(self):
        vc = VimageConfig({
            'myapp.models.MyModel.img': {
                'SIZE': 1000,
            }
        })
        vc.add_validators()
        self.assertEqual(len(self.img.validators), 1)
        self.assertIn(
            'ValidationRuleSize.generate_validator',
            str(self.img.validators[0])
        )

    def test_add_validators_dimensions(self):
        vc = VimageConfig({
            'myapp.models.MyModel.img': {
                'DIMENSIONS': (1000, 1000),
            }
        })
        vc.add_validators()
        self.assertEqual(len(self.img.validators), 1)
        self.assertIn(
            'ValidationRuleDimensions.generate_validator',
            str(self.img.validators[0])
        )

    def test_add_validators_format(self):
        vc = VimageConfig({
            'myapp.models.MyModel.img': {
                'FORMAT': 'png',
            }
        })
        vc.add_validators()
        self.assertEqual(len(self.img.validators), 1)
        self.assertIn(
            'ValidationRuleFormat.generate_validator',
            str(self.img.validators[0])
        )

    def test_add_validators_aspect_ratio(self):
        vc = VimageConfig({
            'myapp.models.MyModel.img': {
                'ASPECT_RATIO': 1,
            }
        })
        vc.add_validators()
        self.assertEqual(len(self.img.validators), 1)
        self.assertIn(
            'ValidationRuleAspectRatio.generate_validator',
            str(self.img.validators[0])
        )

    def test_add_validators_multiple(self):
        vc = VimageConfig({
            'myapp.models.MyModel.img': {
                'SIZE': 1000,
                'DIMENSIONS': (1000, 1000),
                'FORMAT': 'jpeg',
            }
        })
        vc.add_validators()
        self.assertEqual(len(self.img.validators), 3)
