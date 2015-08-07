from fabric.decorators import task
from fabdeb.apt import apt_install, set_apt_repositories, apt_update, apt_upgrade, apt_cleanup
from fabdeb.daemon import install_ntp, install_supervisor
from fabdeb.ftp import install_proftpd
from fabdeb.image import install_pngquant
from fabdeb.mail import install_exim4
from fabdeb.os import (check_sudo, check_os, OS_REPOSITORIES, OS_REPOS_INSTALL_KEYS_COMMANDS, configure_hostname,
                       configure_timezone, setup_swap, server_reboot, update_locale)
from fabdeb.postgresql import install_postgresql
from fabdeb.python import install_python_pkgs_managers, install_python_venv
from fabdeb.redis import install_redis
from fabdeb.webserver import install_nginx


@task
def prepare_server():
    check_sudo()
    os_issue, os_ver = check_os()
    set_apt_repositories(OS_REPOSITORIES, OS_REPOS_INSTALL_KEYS_COMMANDS, os_issue, os_ver)
    update_locale()
    apt_update()
    apt_upgrade()
    configure_hostname()
    apt_install(('mc', 'htop', 'tmux', 'gettext', 'curl', 'tcl-dev' 'build-essential', 'git-core', 'pigz',
                 'lsb_release', 'libcurl4-openssl-dev', 'libffi-dev'), noconfirm=True)
    apt_install(('python2.7-dev', 'python-dev', 'libpcre3', 'libpcre3-dev'), comment='For Python')
    apt_install(('tk-dev', 'python-tk', 'python-imaging', 'libjpeg-dev', 'zlib1g-dev',
                 'libtiff-dev', 'libfreetype6-dev', 'liblcms1-dev', 'liblcms2-dev', 'libwebp-dev',
                 'libopenjpeg-dev', 'openjpeg-tools'), comment='For Python Pillow or other image libraries')
    apt_install(('libxml2-dev', 'libxslt-dev'), comment='For Python lxml')
    apt_install('libmagickwand-dev', comment='For Python wand')
    apt_install('imagemagick')
    configure_timezone()
    install_ntp()
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
    apt_cleanup()
    server_reboot()
