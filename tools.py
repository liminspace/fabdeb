# coding=utf-8
from __future__ import absolute_import
import sys
import subprocess


COMMANDS_LIST = ('release',)
COMMANDS_INFO = {
    'release': 'make distributive and upload to pypi (setup.py sdist upload)'
}


def release(*args):
    subprocess.call(['python', 'setup.py', 'sdist', 'upload'])


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] in COMMANDS_LIST:
        locals()[sys.argv[1]](*sys.argv[2:])
    else:
        print 'Available commands:'
        for c in COMMANDS_LIST:
            print c + ' - ' + COMMANDS_INFO[c]
