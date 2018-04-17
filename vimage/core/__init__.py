from django.conf import settings

from .base import VimageConfig
from .const import CONFIG_NAME


def add_validators():
    """
    Assumes that the VIMAGE setting has been checked for any errors.
    This is the main function that will initiate validation rules addition
    to each ImageField's 'validators' attribute.
    :return: None
    """
    vc = VimageConfig(getattr(settings, CONFIG_NAME))
    vc.add_validators()
