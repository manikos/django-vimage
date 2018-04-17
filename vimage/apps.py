from django.apps import AppConfig


class VimageConfig(AppConfig):
    name = 'vimage'
    verbose_name = 'Django image validation'

    def ready(self):
        from vimage.core.checker import configuration_check
        # check configuration setting before adding any validators
        configuration_check()  # raises Exception or None

        # proceed to validator(s) addition
        from vimage.core import add_validators
        add_validators()  # raises Exception or None
