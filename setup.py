#!/usr/bin/env python
import os
import re
import sys

from setuptools import setup, find_packages


def get_version(*file_paths):
    """Retrieves the version from vimage/__init__.py"""
    filename = os.path.join(os.path.dirname(__file__), *file_paths)
    version_file = open(filename).read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError('Unable to find version string.')


version = get_version("vimage", "__init__.py")

if sys.argv[-1] == 'pypi':
    try:
        import twine
        print(f'Twine version: {twine.__version__}')
    except ImportError:
        print('"twine" library is missing. Please run "pip install twine"')
        sys.exit()
    test = sys.argv[-2] == '--test'
    repo_url = '--repository-url https://test.pypi.org/legacy/' if test else ''
    # upon new release, create new source distribution and a
    # new wheel distribution
    print(f'[Step 1/3] creating source and wheel distributions '
          f'for version {version}{"." * 10}')
    os.system('python setup.py sdist bdist_wheel')
    print('[Step 1/3] DONE!')
    # # upon creation of the above two files, upload to pypi.org only
    # # the newest version. First the source distribution
    print(f'[Step 2/3] uploading source distribution{"." * 10}')
    os.system(f'twine upload {repo_url} dist/django-vimage-{version}.tar.gz')
    print('[Step 2/3] DONE!')
    # # and then the wheel one.
    print(f'[Step 3/3] uploading wheel distribution to pypi.org{"." * 10}')
    os.system(f'twine upload {repo_url} '
              f'dist/django_vimage-{version}-py3-none-any.whl')
    print('[Step 3/3] DONE!')
    print("Everything's done, congratulations!")
    sys.exit()

readme = open('README.md').read()

setup(
    name='django-vimage',
    packages=find_packages(
        include=('vimage', 'vimage.*'),
    ),
    version='1.0.1',
    description="""
    Image validation (for the Django Admin) as a breeze. 
    Validations on: Size, Dimensions, Format and Aspect Ratio.
    """,
    long_description=readme,
    long_description_content_type='text/markdown',
    author='Nick Mavrakis',
    author_email='mavrakis.n@gmail.com',
    url='https://github.com/manikos/django-vimage',
    include_package_data=True,  # anything referred under MANIFEST.in
    python_requires='>=3.6',
    install_requires=['Django>=1.11', 'Pillow>=4.0.0'],
    license='MIT',
    zip_safe=False,
    keywords='django image-validation django-admin easy-to-use',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.11',
        'Framework :: Django :: 2.0',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
