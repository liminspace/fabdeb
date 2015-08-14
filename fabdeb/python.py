from fabric.context_managers import cd
from fabric.contrib.console import confirm
from fabric.contrib.files import exists, append
from fabric.decorators import task
from fabric.operations import sudo
from fabric.utils import abort
from fabdeb.os import check_sudo, check_os
from fabdeb.tools import print_green, print_red


__all__ = ('install_python_pkgs_managers', 'install_python_venv', 'configure_virtualenvwrapper_for_user')


# # # COMMANDS # # #


@task
def install_python_pkgs_managers():
    """
    Install setuptools & pip for python
    """
    check_sudo()
    check_os()
    print_green('INFO: Install python setuptools & pip...')
    with cd('/tmp'):
        sudo('wget -q https://bootstrap.pypa.io/ez_setup.py -O - | python')
        sudo('rm setuptools-*.zip')
        sudo('easy_install -q pip')
    print_green('INFO: Install python setuptools & pip... OK')


@task
def install_python_venv():
    """
    Install virtualenv & virtualenvwrapper for python
    """
    check_sudo()
    check_os()
    print_green('INFO: Install python virtualenv & virtualenvwrapper...')
    sudo('pip install -q virtualenv')
    sudo('pip install -q virtualenvwrapper')
    print_green('INFO: Install python virtualenv & virtualenvwrapper... OK')


@task
def configure_virtualenvwrapper_for_user(username):
    """
    Configure virtualenvwrapper for user
    """
    check_sudo()
    check_os()
    if not confirm('Do you want to configure virtualenvwrapper to user "{}"?'.format(username)):
        return
    if not exists('/usr/local/bin/virtualenvwrapper.sh', use_sudo=True):
        abort('virtualenvwrapper is not installed.')
    print_green('INFO: Configure virtualenvwrapper to user {}...'.format(username))
    user_dir = '/home/{}'.format(username)
    if not exists(user_dir, use_sudo=True):
        print_red("Directory {} doesn't exists :(".format(user_dir))
        if not confirm('Do you want to ignore this error and continue? (else will be abort)', default=False):
            abort("Directory {} doesn't exists :(".format(user_dir))
    else:
        bashrc = '{}/.bashrc'.format(user_dir)
        append(bashrc, 'export WORKON_HOME=$HOME/.virtualenvs', use_sudo=True)
        append(bashrc, 'export VIRTUALENVWRAPPER_HOOK_DIR=$WORKON_HOME', use_sudo=True)
        append(bashrc, 'export export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python2.7', use_sudo=True)
        append(bashrc, 'source /usr/local/bin/virtualenvwrapper.sh', use_sudo=True)
    print_green('INFO: Configure virtualenvwrapper to user {}... OK'.format(username))
