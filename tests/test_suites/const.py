import os

from django.core.files.uploadedfile import SimpleUploadedFile

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ROOT = 'vimage'
CORE = f'{ROOT}.core'
IMAGES_PATH = os.path.join(BASE_DIR, 'images')


def dotted_path(module, class_name, method_name):
    keywords = [CORE, module, class_name, method_name]
    return f'{".".join(keywords)}'


def image(name, path):
    return SimpleUploadedFile(
        name=name,
        content=open(path, 'rb').read(),
        content_type='image/jpeg'
    )
