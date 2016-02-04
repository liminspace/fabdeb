# coding=utf-8
from __future__ import absolute_import
import os
import sys
import subprocess
import shutil


COMMANDS_LIST = ('register', 'release')
COMMANDS_INFO = {
    'register': 'register package to pypi (setup.py register)',
    'release': 'make distributive and upload to pypi (setup.py sdist upload)',
}


def register(*args):
    subprocess.call(['python', 'setup.py', 'register'])


def release(*args):
    root_dir = os.path.dirname(os.path.abspath(__file__))
    shutil.rmtree(os.path.join(root_dir, 'build'), ignore_errors=True)
    shutil.rmtree(os.path.join(root_dir, 'fabdeb.egg-info'), ignore_errors=True)
    subprocess.call(['python', 'setup.py', 'bdist_wheel', 'upload'])


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] in COMMANDS_LIST:
        locals()[sys.argv[1]](*sys.argv[2:])
    else:
        print 'Available commands:'
        for c in COMMANDS_LIST:
            print c + ' - ' + COMMANDS_INFO[c]
