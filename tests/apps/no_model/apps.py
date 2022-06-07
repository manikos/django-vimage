from django.apps import AppConfig


class NoModelConfig(AppConfig):
    name = "tests.apps.no_model"
    default_auto_field = "django.db.models.BigAutoField"
