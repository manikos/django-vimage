from django.core.exceptions import ImproperlyConfigured


class MissingConfigError(ImproperlyConfigured):
    """
    Configuration dict is missing from settings module
    """
    pass


class InvalidConfigValueError(ImproperlyConfigured):
    """
    Configuration dict is not a dictionary
    """
    pass


class EmptyConfigError(ImproperlyConfigured):
    """
    Configuration dict is an empty dict
    """
    pass


class InvalidKeyError(ImproperlyConfigured):
    """ Configuration dict has invalid key """
    pass


class InvalidValueError(ImproperlyConfigured):
    """ Configuration dict has invalid value """
    pass
