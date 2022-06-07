import operator

from django.utils.translation import gettext_lazy as _

from vimage.apps import VimageConfig


APP_NAME = VimageConfig.name
CONFIG_NAME = 'VIMAGE'

type_size = 'SIZE'
type_dimensions = 'DIMENSIONS'
type_format = 'FORMAT'
type_aspect_ratio = 'ASPECT_RATIO'
type_mode = 'MODE'  # TODO: Add a MODE validation?

valid_types_strings = [
    type_size, type_dimensions, type_format, type_aspect_ratio,  # type_mode
]

trans_type = {
    type_size: _('SIZE'),
    type_dimensions: _('DIMENSIONS'),
    type_format: _('FORMAT'),
    type_aspect_ratio: _('ASPECT RATIO'),
    type_mode: _('MODE'),
}

trans_and = _('and')
trans_or = _('or')

err = 'err'

w = 'w'
h = 'h'
width_height_operators = {w, h}

trans_wh = {
    w: _('width'),
    h: _('height'),
}

lt = 'lt'
lte = 'lte'
gt = 'gt'
gte = 'gte'
ne = 'ne'
eq = 'eq'

comparison_operators = {
    lt: operator.lt,
    lte: operator.le,
    gt: operator.gt,
    gte: operator.ge,
    ne: operator.ne,
    eq: operator.eq,
}
valid_operators_strings = list(comparison_operators.keys())

human_opr = {
    lt: _('less than'),
    lte: _('less than or equal to'),
    gt: _('greater than'),
    gte: _('greater than or equal to'),
    ne: _('not equal to'),
    eq: _('equal to'),
}

allowable_web_image_extensions = ['jpeg', 'png', 'gif', 'bmp', 'webp']


errors = {
    'empty_dict': 'The value of the rule "{name}", "{rule}", should be a '
                  'non-empty dict.',
}


def nonsense_operators():
    """
    A list of sets which makes no sense to appear together in a single
    validation rule. For example, there is no sense to apply to an image,
    a validation rule for, i.e, ``'SIZE'``, that's gonna be ``less than 1000px
    AND less than or equal 1100px``.
    Or, ``greater than 500px and equal to 785px``!

    :return: list of 2-length sets
    """
    return [
        {lt, lte},  # "less than" and "less than or equal"? Nonsense
        {gt, gte},  # "greater than" and "greater than or equal"? Nonsense
        {lt, eq},  # "less than" and "equal"? Nonsense
        {gt, eq},  # "greater than" and "equal"? Nonsense
        {lte, eq},  # "less than or equal" and "equal"? Nonsense
        {gte, eq},  # "greater than" and "equal"? Nonsense
        {ne, eq},  # "equal" and "non equal"? Nonsense
    ]


def nonsense_values_together():
    """
    This list represents nonsense pairs of value keys of a
    :class:`~vimage.core.base.VimageValue` instance.

    For example, a ``VimageValue`` instance may not have set both
    ``'DIMENSIONS'`` and ``'ASPECT_RATIO'`` validation strings.
    Every pair inside this list is mutual exclusive.

    :return: list of 2-length sets
    """
    return [
        {type_dimensions, type_aspect_ratio},
    ]


def docstring_parameter(*args, **kwargs):
    """
    A decorator that overrides the docstring of a method.

    :param args: any args passed to the function
    :param kwargs: any kwargs passed to the function
    :return: function
    """
    def decor(func):
        func.__doc__ = func.__doc__.format(*args, **kwargs)
        return func
    return decor
