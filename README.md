![image](docs/source/_static/logo.png) django-vimage
====================================================

[![Latest PyPI version badge](https://img.shields.io/pypi/v/django-vimage.svg?style=flat-square)](https://pypi.org/project/django-vimage/)
[![Travis CI build status badge](https://img.shields.io/travis/manikos/django-vimage/master.svg?style=flat-square)](https://travis-ci.org/manikos/django-vimage)
[![Codecov status badge](https://img.shields.io/codecov/c/github/manikos/django-vimage.svg?style=flat-square)](https://codecov.io/gh/manikos/django-vimage)
[![ReadTheDocs documentation status badge](https://img.shields.io/readthedocs/django-vimage.svg?style=flat-square)](https://readthedocs.org/projects/django-vimage/)
[![Supported python versions badge](https://img.shields.io/pypi/pyversions/django-vimage.svg?style=flat-square)](https://pypi.org/project/django-vimage/)
[![Supported Django versions badge](https://img.shields.io/pypi/djversions/django-vimage.svg?style=flat-square)](https://pypi.org/project/django-vimage/)
[![License badge](https://img.shields.io/github/license/manikos/django-vimage.svg?style=flat-square)](https://github.com/manikos/django-vimage/bolb/master/LICENSE)

Django Image validation for the [Django Admin](https://docs.djangoproject.com/en/dev/ref/contrib/admin/) as a breeze. 
Validations on: Size, Dimensions, Format and Aspect Ratio.

Because, I love to look for the origin of a word/band/place/something,
this package name comes from the word *validate* and (you guessed it)
*image*. Thus, `django-vimage`. Nothing more, nothing less :)

This package was created due to lack of similar Django packages that do
image validation. I searched for this but found nothing. So, I decided
to create a reusable Django package that will do image validation in a
simple manner. Just declare some `ImageField`s and the rules to apply to
them in a simple Python dictionary. Firstly, I wrote the blueprint on a
piece of paper and then I, gradually, ported it to Django/Python code.

Documentation
-------------

The full documentation is at [https://django-vimage.readthedocs.io](https://django-vimage.readthedocs.io).

Quickstart
----------

Install django-vimage :

    pip install django-vimage

Add it to your `INSTALLED_APPS` :

    INSTALLED_APPS = (
        ...
        'vimage.apps.VimageConfig',
        ...
    )

Finally, add the `VIMAGE` dict configuration somewhere in your `settings` file :

    VIMAGE = {
        'my_app.models': {
            'DIMENSIONS': (200, 200),
            'SIZE': {'lt': 100},
        }
    }

The above `VIMAGE` setting sets the rules for all Django
`ImageField` fields under the `my_app` app. More particular, all
`ImageField`s should be 200 x 200px **and** less than 100KB. Any image
than violates any of the above rules, a nice-looking error message will
be shown (translated accordingly) in the Django admin page.

A full example of possible key:value pairs is shown below. Note that the
following code block is not suitable for copy-paste into your `settings`
file since it contains duplicate dict keys. It's just for demonstration.

```python
VIMAGE = {
    # Possible keys are:
    # 'app.models'  # to all ImageFields inside this app
    # 'app.models.MyModel'  # to all ImageFields inside MyModel
    # 'app.models.MyModel.field'  # only to this ImageField

    # Example of applying validation rules to all images across
    # all models of myapp app
    'myapp.models': {
        # rules
    },

    # Example of applying validation rules to all images across
    # a specific model
    'myapp.models.MyModel': {
        # rules
    },

    # Example of applying validation rules to a
    # specific ImageField field
    'myapp.models.MyModel.img': {
        # rules
    },

    # RULES
    'myapp.models': {

        # By size (measured in KB)

        # Should equal to 100KB
        'SIZE': 100,  # defaults to eq (==)

        # (100KB <= image_size <= 200KB) AND not equal to 150KB
        'SIZE': {
            'gte': 100,
            'lte': 200,
            'ne': 150,
        },

        # Custom error message
        'SIZE': {
            'gte': 100,
            'lte': 200,
            'err': 'Your own error message instead of the default.'
                   'Supports <strong>html</strong> tags too!',
        },


        # By dimensions (measured in px)
        # Should equal to 1200x700px (width x height)
        'DIMENSIONS': (1200, 700),  # defaults to eq (==)

        # Should equal to one of these sizes 1000x300px or 1500x350px
        'DIMENSIONS': [(1000, 300), (1500, 350)],

        # Should be 1000x300 <= image_dimensions <= 2000x500px
        'DIMENSIONS': {
            'gte': (1000, 300),
            'lte': (2000, 500),
        },

        # width must be >= 30px and less than 60px
        # height must be less than 90px and not equal to 40px
        'DIMENSIONS': {
            'w': {
                'gt': 30,
                'lt': 60,
            },
            'h': {
                'lt': 90,
                'ne': 40,
            }
        },


        # By format (jpeg, png, tiff etc)
        # Uploaded image should be JPEG
        'FORMAT': 'jpeg',

        # Uploaded image should be one of the following
        'FORMAT': ['jpeg', 'png', 'gif'],

        # Uploaded image should not be a GIF
        'FORMAT': {
            'ne': 'gif',
        },

        # Uploaded image should be neither a GIF nor a PNG
        'FORMAT': {
            'ne': ['gif', 'png'],
            'err': 'Wrong image <em>format</em>!'
        },
    }
}
```

Features
--------

-   An image may be validated against it's size (KB), dimensions (px),
    format (jpeg, png etc) and aspect ratio (width/height ratio).
    
-   Well formatted error messages. They have the form of:

    **[IMAGE RULE\_NAME]** Validation error: **image_value** does not meet validation rule: **rule**.

-   Humanized error messages. All rules and image values are *humanized*:

    - `'SIZE': {'gte': 100}` becomes `greater than or equal to 100KB` when rendered
    
    - `'DIMENSIONS': {'ne': (100, 100)}` becomes `not equal to 100 x 100px` when rendered

-   Overridable error messages. The default error messages may be overridden by defining an `err` key inside the validation rules:

    `'SIZE': {'gte': 100, 'err': 'Custom error'}` becomes
    `Custom error` when rendered

-   HTML-safe (custom) error messages. All error messages (the default or your own) are passed through the function [mark_safe](https://docs.djangoproject.com/en/dev/ref/utils/#django.utils.safestring.mark_safe).
    
-   Cascading validation rules. It's possible to define a generic rule
    to some `ImageField` fields of an app and then define another set of
    rules to a specific `ImageField` field. Common rules will override
    the generic ones and any new rules will be added to the specific
    `ImageField` field:

        myapp.models: {
            'SIZE': {
                'lt': 120,
            },
            'FORMAT': 'jpeg',
            'DIMENSIONS': {
                'lt': (500, 600),
            }
         },
         myapp.models.MyModel.img: {
            'DIMENSIONS': (1000, 500),
         },

    In the example above (the order does not matter), all `ImageField`s
    should be `less than 120KB`, `JPEG` images **and** `less than 500 x 600px`. 
    However, the `myapp.models.MyModel.img` field should be `less than 120KB`, `JPEG` image **and** `equal to 1000 x 500px`.

Running Tests
-------------

Does the code actually work?

    source <YOURVIRTUALENV>/bin/activate
    (myenv) $ pip install tox
    (myenv) $ tox

Future additions
----------------

-   Validation of image mode (whether the uploaded image is in indexed
    mode, greyscale mode etc) based on [image's mode](http://pillow.readthedocs.io/en/latest/handbook/concepts.html#modes).
    This is quite easy to implement but rather a *rare* validation
    requirement. Thus, it'll be implemented if users want to validate
    the mode of the image (which again, it's rare for the web).
-   If you think of any other validation (apart from svg) that may be
    applied to an image and it's not included in this package, please
    feel free to submit an issue or a PR.

Credits
-------

Tools used in rendering this package:

-   [Cookiecutter](https://github.com/audreyr/cookiecutter)
-   [cookiecutter-djangopackage](https://github.com/pydanny/cookiecutter-djangopackage)
