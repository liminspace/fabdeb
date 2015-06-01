from fabdeb.apt import apt_install, set_apt_repositories, apt_update
from fabdeb.fab_tools import print_green
from fabric.contrib.console import confirm
from fabric.operations import sudo


NGINX_REPOSITORIES = {
    'Debian GNU/Linux 8': {
        ('8.0',): ('deb http://nginx.org/packages/debian/ jessie nginx\n'
                   'deb-src http://nginx.org/packages/debian/ jessie nginx\n'),
    },
}


NGINX_REPOS_INSTALL_KEYS_COMMANDS = {
    'Debian GNU/Linux 8': {
        ('8.0',): (
            'wget -q -O - http://nginx.org/keys/nginx_signing.key | apt-key add -',
        ),
    },
}


# # # COMMANDS # # #


def install_nginx(os_issue, os_ver):
    if not confirm('Do you want to install nginx?'):
        return
    print_green('INFO: Install nginx...')
    set_apt_repositories(NGINX_REPOSITORIES, NGINX_REPOS_INSTALL_KEYS_COMMANDS, os_issue, os_ver, subconf_name='nginx')
    apt_update()
    apt_install(('nginx',))
    sudo('usermod -a -G www-data nginx')
    # todo set base configuration
    print_green('INFO: Install nginx... OK')
