.. _usage:

Usage
=====

To use django-vimage in a project, add it to your ``INSTALLED_APPS``
::

    INSTALLED_APPS = (
        ...
        'vimage.apps.VimageConfig',
        ...
    )

And then define a |config_name| dictionary with the appropriate key:value pairs.
Every :ref:`key <vimage-key>` should be a ``str`` while every :ref:`value <vimage-value>` should be a ``dict``.
::

    VIMAGE = {
        # key:value pairs
    }


.. _vimage-key:

|config_name| key
-----------------

Each |config_name| key should be a ``str``, the dotted path to one of the following:

- :mod:`~django.db.models` module (i.e ``myapp.models``). This is the global setting. The rule will apply to all ``ImageField`` fields defined in this ``models`` module.

- Django :class:`~django.db.models.Model` (i.e ``myapp.models.MyModel``). This is a model-specific setting. The rule will apply to all ``ImageField`` fields defined under this model.

- Django :class:`~django.db.models.ImageField` field (i.e ``myapp.models.MyModel.img``). This is a field-specific setting. The rule will apply to just this ``ImageField``.

It is allowed to have multiple keys refer to the same app. Keep in mind, though, that
keys referring to specific ``ImageField``'s have higher precedence to those referring to
a specific ``Model`` and any common rules will be overridden while new ones will be added.

For example, suppose you have a project structure like the following:
::

    my_project/
      my_app/
        models.py
        views.py
      my_project/
        settings.py
        urls.py
      manage.py

and ``my_app.models`` defines the following models:
::

    from django.db import models

    class Planet(models.Model):
        # ... other model fields here
        large_photo = models.ImageField(upload_to='planets')
        small_photo = models.ImageField(upload_to='planets')

    class Satellite(models.Model):
        # ... other model fields here
        outer_photo = models.ImageField(upload_to='satellite')
        inner_photo = models.ImageField(upload_to='satellite')

and the keys defined are the following:
::

    VIMAGE = {
        'my_app.models': {# rules here},
        'my_app.models.Planet': {# rules here},
        'my_app.models.Satellite': {# rules here},
        'my_app.models.Satellite.inner_photo': {# rules here},
    }

Then, all ``ImageField``'s of ``my_app`` app (``large_photo``, ``small_photo``, ``outer_photo`` and ``inner_photo``)
will have the rules defined in ``my_app.models`` dict value.
However, the rules defined in ``my_app.models.Planet`` (affecting ``ImageField``'s of the ``Planet`` model) will override
the previous ones and any new will be added. The same principle applies to the ``Satellite`` ``ImageField``'s.

In general, rules have specificity, just like CSS. This is a good thing because you can apply some rules globally and then
become more particular on a per ``ImageField`` level.

The specificity is shown below:

+-----------------------------------------+-------------+
| Key                                     | Specificity |
+=========================================+=============+
| ``<myapp>.models``                      | 1           |
+-----------------------------------------+-------------+
| ``<myapp>.models.<Model>``              | 2           |
+-----------------------------------------+-------------+
| ``<myapp>.models.<Model>.<ImageField>`` | 3           |
+-----------------------------------------+-------------+

The higher the specificity, the higher the precedence of the rule.


.. _vimage-value:

|config_name| value
-------------------

Each |config_name| value should be a dictionary. The structure must be:
::

    {
        '<validation_string>': <validation_rule>,
    }

Each key of the dictionary should be one of the following validation strings:

-  :ref:`'SIZE' <validation_string_size>`, image file size
-  :ref:`'DIMENSIONS' <validation_string_dimensions>`, image dimensions
-  :ref:`'FORMAT' <validation_string_format>`, image format (i.e JPEG, PNG etc)
-  :ref:`'ASPECT_RATIO' <validation_string_aspect_ratio>` image width / image height ratio

Depending on the validation string, the corresponding value type (and unit) varies. The table below
shows the valid key:value pair types:

+---------------------------------------+-------------------------------------------+----------------------+
| Key (always ``str``)                  | Value type                                | Unit                 |
+=======================================+===========================================+======================+
| ``'SIZE'``                            | ``<int>`` | ``<dict>``                    | ``KB``               |
+---------------------------------------+-------------------------------------------+----------------------+
| ``'DIMENSIONS'``                      | ``<tuple>`` | ``<list>`` | ``<dict>``     | ``px``               |
+---------------------------------------+-------------------------------------------+----------------------+
| ``'FORMAT'``                          | ``<str>`` | ``<list>`` | ``<dict>``       | no unit              |
+---------------------------------------+-------------------------------------------+----------------------+
| ``'ASPECT_RATIO'``                    | ``<float>`` | ``<dict>``                  | no unit              |
+---------------------------------------+-------------------------------------------+----------------------+

For example, the following (full example) rule states that the uploaded image (via the Django Admin) must be, for some reason, equal to 100KB:
::

    VIMAGE = {
        'my_app.models.MyModel.img': {
            'SIZE': 100,
        }
    }

The following rule states that the uploaded image must be either a JPEG or a PNG format:
::

    VIMAGE = {
        'my_app.models.MyModel.img': {
            'FORMAT': ['jpeg', 'png'],
        }
    }

When the value is a dict, |config_name| uses the :py:mod:`operator` module to apply the rules.
All keys accept the ``<dict>`` value type with the following strings as keys:

.. code-block:: bash
   :caption: valid operator strings
   :name: operator_strings

    +-------------------------+-----------------------------+
    | Operator string         | Meaning                     |
    +=========================+=============================+
    | 'gte'                   | greater than or equal to    |
    +-------------------------+-----------------------------+
    | 'lte'                   | less than or equal to       |
    +-------------------------+-----------------------------+
    | 'gt'                    | greater than                |
    +-------------------------+-----------------------------+
    | 'lt'                    | less than                   |
    +-------------------------+-----------------------------+
    | 'eq'                    | equal to                    |
    +-------------------------+-----------------------------+
    | 'ne'                    | not equal to                |
    +-------------------------+-----------------------------+

However, the ``'FORMAT'`` validation rule accepts a *minimal* set of operators that may be applied only to string values (not numbers).
That is, ``'eq'`` and ``'ne'``.

.. note:: Keep in mind that an error is raised if some specific operator pairs are used, for example, ``'gte'`` and ``'eq'``.
   This is because it makes no sense for an image to be ``greater than or equal to something`` and at the same time ``equal to something``!
   :name: operator_strings_note

Confused? Take a look at the :ref:`examples <examples>`.
