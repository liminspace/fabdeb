from fabric.context_managers import cd
from fabric.contrib.console import confirm
from fabric.decorators import task
from fabric.operations import sudo
from fabdeb.apt import apt_install
from fabdeb.os import check_sudo
from fabdeb.os import check_os
from fabdeb.tools import print_green


__all__ = ('install_pngquant_jpegtran',)


# # # COMMANDS # # #


@task
def install_pngquant_jpegtran():
    """
    Install pngquant and jpegtran -- console utility for compress PNG- and JPEG-images
    """
    check_sudo()
    check_os()
    if not confirm('Do you want to install pngquant and jpegtran?'):
        return
    print_green('INFO: Install pngquant and jpegtran...')
    apt_install('libpng-dev liblcms2-dev libjpeg-progs', noconfirm=True)
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
    print_green('INFO: Install pngquant and jpegtran...  OK')
