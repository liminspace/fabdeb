# coding=utf-8
import os
from distutils.core import setup
from setuptools import find_packages
import fabdeb


setup(
    name='fabdeb',
    version=fabdeb.__version__,
    description='Fabfile solutions for Debian Linux',
    long_description=open(os.path.join(os.path.dirname(__file__), 'README.md')).read(),
    license='BSD',
    author='liminspace',
    author_email='liminspace@gmail.com',
    url='https://github.com/liminspace/fabdeb',
    packages=find_packages(exclude=('tests',)),
    include_package_data=True,
    zip_safe=False,  # тому, що вкладаємо статику
    requires=[
        'fabric',
    ],
)
