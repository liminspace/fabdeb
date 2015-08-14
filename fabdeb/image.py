from fabric.context_managers import cd
from fabric.contrib.console import confirm
from fabric.decorators import task
from fabric.operations import sudo
from fabdeb.apt import apt_install
from fabdeb.os import check_sudo
from fabdeb.os import check_os
from fabdeb.tools import print_green


__all__ = ('install_pngquant',)


# # # COMMANDS # # #


@task
def install_pngquant():
    """
    Install pngquant -- console utility for compress PNG-images
    """
    check_sudo()
    check_os()
    if not confirm('Do you want to install pngquant?'):
        return
    print_green('INFO: Install pngquant...')
    apt_install('libpng-dev liblcms2-dev', noconfirm=True)
    with cd('/tmp'):
        sudo('wget -q https://github.com/pornel/pngquant/archive/master.zip')
        sudo('unzip master.zip')
        sudo('rm master.zip')
    with cd('/tmp/pngquant-master'):
        sudo('./configure --with-lcms2 && make')
        sudo('make install')
        if confirm('Do you want make symlink /usr/local/bin/pngquant to /bin/pngquant?'):
            sudo('ln -s /usr/local/bin/pngquant /bin/pngquant')
    with cd('/tmp'):
        sudo('rm -rf pngquant-master')
    print_green('INFO: Install pngquant...  OK')
