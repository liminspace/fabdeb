from fabric.decorators import task
from fabdeb.apt import apt_install, set_apt_repositories, apt_update, apt_upgrade
from fabdeb.db import install_redis, install_postgresql
from fabdeb.os import (check_sudo, check_os, setup_swap, configure_timezone, OS_REPOSITORIES,
                       OS_REPOS_INSTALL_KEYS_COMMANDS, install_exim4)
from fabdeb.python import install_python_pkgs_managers, install_python_venv, configure_virtualenvwrapper_for_user
from fabdeb.tools import install_pngquant, install_supervisor, reboot, install_proftpd
from fabdeb.webserver import install_nginx


__version__ = '0.1.3'


@task
def prepare_server():
    check_sudo()
    os_issue, os_ver = check_os()
    set_apt_repositories(OS_REPOSITORIES, OS_REPOS_INSTALL_KEYS_COMMANDS, os_issue, os_ver)
    apt_update()
    apt_upgrade()
    apt_install(('mc', 'htop', 'tmux', 'gettext', 'curl', 'tcl-dev' 'build-essential', 'git-core'))
    # python common
    apt_install(('python2.7-dev', 'python-dev', 'libpcre3', 'libpcre3-dev'))
    # for python pillow
    apt_install(('tk-dev', 'python-tk', 'python-imaging', 'libjpeg-dev', 'zlib1g-dev',
                 'libtiff-dev', 'libfreetype6-dev', 'liblcms1-dev', 'liblcms2-dev', 'libwebp-dev',
                 'libopenjpeg-dev', 'openjpeg-tools'))
    # for python lxml
    apt_install(('libxml2-dev', 'libxslt-dev'))
    # for python wand
    apt_install(('libmagickwand-dev',))
    configure_timezone()
    setup_swap()
    install_python_pkgs_managers()
    install_python_venv()
    install_nginx(os_issue, os_ver)
    install_redis()
    install_postgresql(os_issue, os_ver)
    install_supervisor()
    install_exim4()
    install_pngquant()
    install_proftpd()
    reboot()
