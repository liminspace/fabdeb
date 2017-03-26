from fabric.contrib.console import confirm
from fabric.decorators import task
from fabric.operations import prompt
from fabdeb.apt import apt_install, set_apt_repositories, apt_update, apt_upgrade, apt_cleanup, apt_dist_upgrade
from fabdeb.daemon import install_ntp, install_supervisor_latest
from fabdeb.ftp import install_proftpd
from fabdeb.image import install_pngquant_jpegtran
from fabdeb.mail import install_exim4
from fabdeb.node import install_nodejs
from fabdeb.os import (OS_REPOSITORIES, OS_REPOS_INSTALL_KEYS_COMMANDS, configure_hostname,
                       configure_timezone, setup_swap, server_reboot, update_locale, check_sudo, check_os)
from fabdeb.postgresql import install_postgresql
from fabdeb.python import install_python_pkgs_managers, install_python_venv
from fabdeb.redis import install_redis
from fabdeb.webserver import install_nginx


__all__ = ()


@task
def prepare_server():
    """
    Prepare server before a project deploy
    """
    check_sudo()
    check_os()
    set_apt_repositories(OS_REPOSITORIES, OS_REPOS_INSTALL_KEYS_COMMANDS)
    update_locale()
    configure_hostname()
    for_python = confirm('Do you want to install all things for python projects?')
    install_python3 = confirm('Do you want to install Python3?')
    apt_update()
    apt_upgrade()
    apt_dist_upgrade()
    apt_install(
        'mc htop tmux pv gettext curl tcl-dev build-essential cmake git pigz libxml2-dev libxslt-dev '
        'lsb-release libcurl4-openssl-dev libffi-dev ca-certificates libssl-dev sysstat',
        noconfirm=True
    )
    apt_install('python2.7-dev python-dev libpcre3 libpcre3-dev', comment='For Python', noconfirm=for_python)
    if install_python3:
        apt_install('python3 python3-dev', comment='For Python3', noconfirm=for_python)
    apt_install(
        'tk-dev python-tk python-imaging libjpeg-dev zlib1g-dev libtiff-dev libfreetype6-dev '
        'libtiff5-dev liblcms1-dev liblcms2-dev libwebp-dev libopenjpeg-dev openjpeg-tools '
        'tcl8.6-dev tk8.6-dev libturbojpeg-dev libtiff-tools',
        comment='For Python Pillow or other image libraries',
        noconfirm=for_python
    )
    if install_python3:
        apt_install(
            'python3-tk',
            comment='For Python3 Pillow or other image libraries',
            noconfirm=for_python
        )
    apt_install('libmagickwand-dev', comment='For Python wand', noconfirm=for_python)
    apt_install('imagemagick', noconfirm=for_python)
    configure_timezone()
    install_ntp()
    setup_swap()
    if for_python or confirm('Do you want to install python setuptools & pip?'):
        install_python_pkgs_managers()
        if install_python3:
            install_python_pkgs_managers(python_ver='3')
    if for_python or confirm('Do you want to install python virtualenv & virtualenvwrapper?'):
        if install_python3:
            ver = ''
            while ver not in ('2', '3'):
                ver = prompt('Which Python version do you want to use? (2, 3):', default='2')
        else:
            ver = '2'
        install_python_venv(python_ver=ver)
    install_nodejs()
    install_nginx()
    install_redis()
    install_postgresql()
    install_supervisor_latest()
    install_exim4()
    install_pngquant_jpegtran()
    install_proftpd()
    apt_cleanup()
    server_reboot()
