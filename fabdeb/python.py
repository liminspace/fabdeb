from fabric.context_managers import cd
from fabric.contrib.console import confirm
from fabric.contrib.files import exists, append
from fabric.decorators import task
from fabric.operations import sudo, run
from fabric.utils import abort
from fabdeb.os import check_sudo, check_os
from fabdeb.tools import print_green, print_red


__all__ = ('install_python_pkgs_managers', 'install_python_venv', 'configure_virtualenvwrapper_for_user')


def get_python3_version(parts=2):
    assert 1 <= parts <= 3
    return '.'.join(run('python3 --version').split()[1].split('.')[:parts])


# # # COMMANDS # # #


@task
def install_python_pkgs_managers(python_ver='2'):
    """
    Install setuptools & pip for python
    """
    assert python_ver in ('2', '3')
    python_ver = int(python_ver)
    check_sudo()
    check_os()
    print_green('INFO: Install python {} setuptools & pip...'.format(python_ver))
    with cd('/tmp'):
        # there is problem. maybe aptitude install python-setuptools is better way
        if python_ver == 3:
            sudo('wget -q https://bootstrap.pypa.io/ez_setup.py -O - | python3')
        else:
            sudo('wget -q https://bootstrap.pypa.io/ez_setup.py -O - | python')
        sudo('rm setuptools-*.zip')
        if python_ver == 3:
            sudo('easy_install-{} -q pip'.format(get_python3_version()))
        else:
            sudo('easy_install -q pip')
    print_green('INFO: Install python {} setuptools & pip... OK'.format(python_ver))


@task
def install_python_venv(python_ver='2'):
    """
    Install virtualenv & virtualenvwrapper for python
    """
    assert python_ver in ('2', '3')
    python_ver = int(python_ver)
    check_sudo()
    check_os()
    print_green('INFO: Install python {} virtualenv & virtualenvwrapper...'.format(python_ver))
    sudo('pip{} install -q virtualenv'.format(python_ver))
    sudo('pip{} install -q virtualenvwrapper'.format(python_ver))
    print_green('INFO: Install python {} virtualenv & virtualenvwrapper... OK'.format(python_ver))


@task
def configure_virtualenvwrapper_for_user(username, python_ver='2'):
    """
    Configure virtualenvwrapper for user
    """
    assert python_ver in ('2', '3')
    python_ver = int(python_ver)
    check_sudo()
    check_os()
    if not confirm('Do you want to configure python {} virtualenvwrapper to user "{}"?'.format(python_ver, username)):
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
        python_path = '/usr/bin/python2.7'
        if python_ver == 3:
            python_path = '/usr/bin/python{}'.format(get_python3_version())
        append(bashrc, 'export WORKON_HOME=$HOME/.virtualenvs', use_sudo=True)
        append(bashrc, 'export VIRTUALENVWRAPPER_HOOK_DIR=$WORKON_HOME', use_sudo=True)
        append(bashrc, 'export export VIRTUALENVWRAPPER_PYTHON={}'.format(python_path), use_sudo=True)
        append(bashrc, 'source /usr/local/bin/virtualenvwrapper.sh', use_sudo=True)
    print_green('INFO: Configure python {} virtualenvwrapper to user {}... OK'.format(python_ver, username))
