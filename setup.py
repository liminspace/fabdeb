import os
from distutils.core import setup
from setuptools import find_packages
import fabdeb


setup(
    name='fabdeb',
    version=fabdeb.__version__,
    description='Fabfile solutions for Debian Linux',
    long_description=open(os.path.join(os.path.dirname(__file__), 'README.md')).read(),
    license='MIT',
    author='Igor Melnyk',
    author_email='liminspace@gmail.com',
    url='https://github.com/liminspace/fabdeb',
    packages=find_packages(exclude=('tests', 'tests.*')),
    include_package_data=True,
    zip_safe=False,  # because include static
    keywords=[
        'fabric', 'tools', 'tool', 'deloy', 'devops',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'License :: OSI Approved :: MIT License',
    ],
)
