from django.conf import settings

from .const import APP_NAME, CONFIG_NAME
from .base import VimageEntry
from . import exceptions


def configuration_check():
    """
    Scans the ``VIMAGE`` dict setting for syntactic errors.

    :return: None or raises an exception from .exceptions
    """

    # 1. Is configuration defined?
    if not hasattr(settings, CONFIG_NAME):
        err = f'"{APP_NAME}" is in INSTALLED_APPS but has not been ' \
              f'configured! Either add "{CONFIG_NAME}" dict to your ' \
              f'settings or remove "{APP_NAME}" from INSTALLED_APPS.'
        raise exceptions.MissingConfigError(err)

    config = getattr(settings, CONFIG_NAME)

    # 2. Is configuration a dict?
    if not isinstance(config, dict):
        error = f'"{CONFIG_NAME}" type is not a dictionary. The value ' \
                f'should be a non-empty dict!'
        raise exceptions.InvalidConfigValueError(error)

    # 3. Is configuration a non-empty dict?
    if config == {}:
        error = f'"{CONFIG_NAME}" configuration is an empty dict! ' \
                f'Add validation rules inside the "{CONFIG_NAME}" dict.'
        raise exceptions.EmptyConfigError(error)

    # 4. Is each key-value pair valid?
    for key, value in config.items():
        VimageEntry(key, value).is_valid()
