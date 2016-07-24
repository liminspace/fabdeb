from fabric.contrib.console import confirm
from fabric.decorators import task
from fabric.operations import sudo, prompt
from fabdeb.apt import apt_install
from fabdeb.os import check_sudo, check_os
from fabdeb.tools import print_green


__all__ = ('install_nodejs',)


SUPPORT_NODEJS_VERSIONS = ('4', '6')


# # # COMMANDS # # #


@task
def install_nodejs(ver=None):
    """
    Install nodejs
    """
    assert ver in SUPPORT_NODEJS_VERSIONS or ver is None
    check_sudo()
    check_os()
    if not confirm('Do you want to install Node.js{}?'.format(' {}'.format(ver) if ver else '')):
        return
    allow_versions = ', '.join(SUPPORT_NODEJS_VERSIONS)
    while ver not in SUPPORT_NODEJS_VERSIONS:
        ver = prompt('Write Node.js version you need ({}):'.format(allow_versions),
                     default=SUPPORT_NODEJS_VERSIONS[0])
    print_green('INFO: Install Node.js {}...'.format(ver))
    sudo('wget -q -O - https://deb.nodesource.com/setup_{v}.x | bash -'.format(v=ver))
    apt_install('nodejs', noconfirm=True)
    print_green('INFO: Install Node.js {}... OK'.format(ver))
