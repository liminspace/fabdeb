from fabdeb.apt import apt_install
from fabdeb.fab_tools import print_green
from fabric.contrib.console import confirm
from fabric.operations import sudo


# # # COMMANDS # # #


def install_nginx():
    if not confirm('Do you want to install nginx?'):
        return
    print_green('INFO: Install nginx...')
    apt_install(('nginx',))
    sudo('usermod -a -G www-data nginx')
    # todo set base configuration
    print_green('INFO: Install nginx... OK')
