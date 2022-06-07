.. _configuration:

Configuration
=============

Each of the following strings are valid as a dict ``key`` of the |config_name| dict ``value``.
Confused? Take a look at a :ref:`definition example <vimage_example_definition>` of |config_name|.

.. note:: The developer may provide a custom error which will be automatically HTML escaped.
   The string may also be :ref:`translated <extend-translations>`.
   In order to do that, the value of the validation string must be a ``dict`` and the key of the custom error should be ``'err'``. Example:
   :name: custom_error_note

   .. code-block:: python
      :name: custom_error_message

      from django.utils.translation import gettext_lazy as _

      VIMAGE = {
          'myapp.models': {
              'SIZE': {
                  'lt': 200,
                  'err': _('Size should be less than <strong>200KB!</strong>'),
              },
          }
      }

.. note:: If ``'err'`` is not defined then a well-looking default error will appear.
   :name: default_error_note

   **[IMAGE {rule_name}]** Validation error: **{value}** does not meet validation rule: **{rule}**.

   1. ``{rule_name}`` is replaced by the corresponding validation string
   2. ``{value}`` is replaced by the corresponding image value under test
   3. ``{rule}`` is replaced by the corresponding rule in a *humanized* form


.. _validation_string_size:

----------
``'SIZE'``
----------

The ``'SIZE'`` key corresponds to the image's file size (measured in ``KB``). It accepts two kind of value types: ``int`` or ``dict``.

- If it's an ``int`` (must be a positive integer) then it is assumed that the file size of the uploaded image will be **equal** to the value defined.

    .. code-block:: python
       :caption: 'SIZE' with ``int`` as value
       :name: size_w_int

       VIMAGE = {
           'myapp.models': {
               # uploaded image file size should be equal to 100KB
               'SIZE': 100,
           }
       }

- If it's a ``dict``, then any ``str`` from :ref:`operator strings table <operator_strings>` will be valid as long as it's value is an ``int`` (positive integer).
  Also, take a look at this :ref:`note <operator_strings_note>`.

    .. code-block:: python
       :caption: 'SIZE' with ``dict`` as value
       :name: size_w_dict

       VIMAGE = {
           'myapp.models': {
               # uploaded image file size should be less than 200KB
               # and greater than 20KB
               'SIZE': {
                   'lt': 200,
                   'gt': 20,
                   'err': 'custom error here'  # optional
               },
           }
       }


.. _validation_string_dimensions:

----------------
``'DIMENSIONS'``
----------------

The ``'DIMENSIONS'`` key corresponds to the image's dimensions, width and height (measured in ``px``). It accepts three kind of value types: ``tuple``, ``list`` or ``dict``.

- If it's a ``tuple`` (two-length tuple with positive integers) then it is assumed that the dimensions of the uploaded image will be **equal** to
  the value (tuple) defined (``(width, height)``).

    .. code-block:: python
       :caption: 'DIMENSIONS' with ``tuple`` as value
       :name: dimensions_w_tuple

       VIMAGE = {
           'myapp.models': {
               # uploaded image dimensions should be equal to 800 x 600px
               # width == 800 and height == 600px
               'DIMENSIONS': (800, 600),
           }
       }

- If it's a ``list`` (one or more two-length tuples with positive integers) then it is assumed that the dimensions of the uploaded image will be **equal** to
  one of the values defined in the list.

    .. code-block:: python
       :caption: 'DIMENSIONS' with ``list`` as value
       :name: dimensions_w_list

       VIMAGE = {
           'myapp.models': {
               # uploaded image dimensions should be equal to one of the
               # following: 800x600px, 500x640px or 100x100px.
               'DIMENSIONS': [(800, 600), (500, 640), (100, 100)],
           }
       }

- If it's a ``dict``, then there are two cases. Either use :ref:`operator strings table <operator_strings>` for keys and a two-length tuple of positive integers for values or
  use the strings ``'w'`` and/or ``'h'`` for keys and (another) ``dict`` for the value of each one using :ref:`operator strings table <operator_strings>` for keys and
  a positive integer for values. Confused? Below are two examples that cover each case.

    .. code-block:: python
       :caption: 'DIMENSIONS' with ``dict`` as value and tuples as sub-values
       :name: dimensions_w_dict_tuple

       VIMAGE = {
           'myapp.models': {
               # uploaded image dimensions should be less than 1920x1080px
               # and greater than 800x768px.
               'DIMENSIONS': {
                   'lt': (1920, 1080),
                   'gt': (800, 768),
                   'err': 'custom error here', # optional
               },
           }
       }

    .. code-block:: python
       :caption: 'DIMENSIONS' with ``dict`` as value and ``'w'``, ``'h'`` as sub-keys
       :name: dimensions_w_dict_width_height

       VIMAGE = {
           'myapp.models': {
               # uploaded image width should not be equal to 800px and
               # height should be greater than 600px.
               'DIMENSIONS': {
                   'w': {
                       'ne': 800,  # set rule just for width
                       'err': 'custom error here', # optional
                   },
                   'h': {
                       'gt': 600,  # set rule just for height
                       'err': 'custom error here', # optional
                   }
               },
           }
       }

  .. note:: For custom error to work when defining both ``'w'`` and ``'h'``, the ``'err'`` entry should be placed to both ``'w'`` and ``'h'`` dicts.

.. _validation_string_format:

------------
``'FORMAT'``
------------

The ``'FORMAT'`` key corresponds to the image's format (it doesn't have a measure unit since it's just a string), i.e ``'jpeg'``, ``'png'``, ``'webp'`` etc.
Taking into account `what image formats the browsers support <https://en.wikipedia.org/wiki/Comparison_of_web_browsers#Image_format_support>`_
|config_name| allows the most used formats for the web, which are: ``'jpeg'``, ``'png'``, ``'gif'``, ``'bmp'`` and ``'webp'``.
It accepts three kind of value types: ``str``, ``list`` or ``dict``.

- If it's a ``str`` then it is assumed that the format of the uploaded image will be **equal** to the value (``str``) defined.

    .. code-block:: python
       :caption: 'FORMAT' with ``str`` as value
       :name: format_w_str

       VIMAGE = {
           'myapp.models': {
               # uploaded image format should be 'jpeg'
               'FORMAT': 'jpeg',
           }
       }

- If it's a ``list`` (list of strings) then it is assumed that the format of the uploaded image will be **equal** to one of the values defined in the list.

    .. code-block:: python
       :caption: 'FORMAT' with ``list`` as value
       :name: format_w_list

       VIMAGE = {
           'myapp.models': {
               # uploaded image format should be one of the following:
               # 'jpeg', 'png' or 'webp'.
               'FORMAT': ['jpeg', 'png', 'webp']
           }
       }

- If it's a ``dict``, then the keys must be either ``'eq'`` or ``'ne'`` (since the other operators cannot apply to ``str`` values) and as for the values they may
  be either a ``list`` or a ``str``.

    .. code-block:: python
       :caption: 'FORMAT' with ``dict`` as value and str as sub-value
       :name: format_w_dict_str

       VIMAGE = {
           'myapp.models': {
               # uploaded image format should not be 'png'.
               'FORMAT': {
                   'ne': 'png',
                   'err': 'custom error here', # optional
               },
           }
       }

    .. code-block:: python
       :caption: 'FORMAT' with ``dict`` as value and list as sub-value
       :name: format_w_dict_list

       VIMAGE = {
           'myapp.models': {
               # uploaded image format should not be equal to
               # neither `webp` nor 'bmp'.
               'FORMAT': {
                   'ne': ['webp', 'bmp'],
                   'err': 'custom error here', # optional
               },
           }
       }


.. _validation_string_aspect_ratio:

------------------
``'ASPECT_RATIO'``
------------------

The ``'ASPECT_RATIO'`` key corresponds to the image's width to height ratio (it doesn't have a measure unit since it's just a decimal number).
It accepts two kind of value types: ``float`` or ``dict``.

- If it's a ``float`` (positive) then it is assumed that the aspect ratio of the uploaded image will be **equal** to the value (``float``) defined.

    .. code-block:: python
       :caption: 'ASPECT_RATIO' with ``float`` as value
       :name: aspect_ratio_w_float

       VIMAGE = {
           'myapp.models': {
               # uploaded image aspect ratio should be equal to 1.2
               'ASPECT_RATIO': 1.2,
           }
       }

- If it's a ``dict``, then any ``str`` from :ref:`operator strings table <operator_strings>` will be valid as long as it's value is a positive ``float``.
  Also, take a look at this :ref:`note <operator_strings_note>`.

    .. code-block:: python
       :caption: 'ASPECT_RATIO' with ``dict`` as value
       :name: aspect_ratio_w_dict

       VIMAGE = {
           'myapp.models': {
               # uploaded image aspect ratio should be less than 1.2
               'ASPECT_RATIO': {
                   'lt': 2.1,
                   'err': 'custom error here', # optional
               },
           }
       }


If you are a *table-person* maybe this will help you:

.. table:: Summarized table between validation strings and their dict values
   :name: validation_string_summarized_table

   +----------------------+-----------------------------------------------------------------------------------------------------+
   | Key                  | Value type                                                                                          |
   +======================+=====================================================================================================+
   | ``'SIZE'``           | ``<int>`` - image's file size should be equal to this number                                        |
   |                      | ``<dict>`` - <operator_str>: ``<int>``                                                              |
   +----------------------+-----------------------------------------------------------------------------------------------------+
   | ``'DIMENSIONS'``     | ``<tuple>`` - a two-length tuple of positive integers                                               |
   |                      |                                                                                                     |
   |                      | ``<list>`` - a list of two-length tuples of positive integers                                       |
   |                      |                                                                                                     |
   |                      | ``<dict>`` - <operator_str>: ``<tuple>``                                                            |
   |                      |                                                                                                     |
   |                      | ``<dict>`` - ``'w'`` and/or ``'h'``: ``<dict>`` - <operator_str>: ``<int>``                         |
   |                      |                                                                                                     |
   +----------------------+-----------------------------------------------------------------------------------------------------+
   | ``'FORMAT'``         | ``<str>`` - one of ``'jpeg'``, ``'png'``, ``'gif'``, ``'bmp'``, ``'webp'``                          |
   |                      |                                                                                                     |
   |                      | ``<list>`` - a list with one or more of the valid formats                                           |
   |                      |                                                                                                     |
   |                      | ``<dict>`` - ``'ne'`` or ``'eq'``: ``<str>`` (one of the valid formats)                             |
   |                      |                                                                                                     |
   |                      | ``<dict>`` - ``'ne'`` or ``'eq'``: ``<list>`` (a list with one or more of the valid formats)        |
   |                      |                                                                                                     |
   +----------------------+-----------------------------------------------------------------------------------------------------+
   | ``'ASPECT_RATIO'``   | ``<float>`` - a float number                                                                        |
   |                      |                                                                                                     |
   |                      | ``<dict>`` - <operator_str>: ``<int>``                                                              |
   |                      |                                                                                                     |
   +----------------------+-----------------------------------------------------------------------------------------------------+
