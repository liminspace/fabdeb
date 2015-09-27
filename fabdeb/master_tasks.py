from fabric.contrib.console import confirm
from fabric.decorators import task
from fabdeb.apt import apt_install, set_apt_repositories, apt_update, apt_upgrade, apt_cleanup, apt_dist_upgrade
from fabdeb.daemon import install_ntp, install_supervisor
from fabdeb.ftp import install_proftpd
from fabdeb.image import install_pngquant
from fabdeb.mail import install_exim4
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
    apt_update()
    apt_upgrade()
    apt_dist_upgrade()
    apt_install(
        'mc htop tmux gettext curl tcl-dev build-essential git pigz lsb-release libcurl4-openssl-dev libffi-dev',
        noconfirm=True
    )
    apt_install('python2.7-dev python-dev libpcre3 libpcre3-dev', comment='For Python', noconfirm=for_python)
    apt_install(
        'tk-dev python-tk python-imaging libjpeg-dev zlib1g-dev libtiff-dev libfreetype6-dev '
        'liblcms1-dev liblcms2-dev libwebp-dev libopenjpeg-dev openjpeg-tools',
        comment='For Python Pillow or other image libraries',
        noconfirm=for_python
    )
    apt_install('libxml2-dev libxslt-dev', comment='For Python lxml', noconfirm=for_python)
    apt_install('libmagickwand-dev', comment='For Python wand', noconfirm=for_python)
    apt_install('imagemagick', noconfirm=for_python)
    configure_timezone()
    install_ntp()
    setup_swap()
    if for_python or confirm('Do you want to install python setuptools & pip?'):
        install_python_pkgs_managers()
    if for_python or confirm('Do you want to install python virtualenv & virtualenvwrapper?'):
        install_python_venv()
    install_nginx()
    install_redis()
    install_postgresql()
    install_supervisor()
    install_exim4()
    install_pngquant()
    install_proftpd()
    apt_cleanup()
    server_reboot()
