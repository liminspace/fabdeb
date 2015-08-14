from StringIO import StringIO
from fabric.contrib.console import confirm
from fabric.decorators import task
from fabric.operations import sudo, put
from fabdeb.os import check_os, check_sudo
from fabdeb.tools import print_green


__all__ = ('apt_update', 'apt_upgrade', 'apt_dist_upgrade' 'apt_install', 'apt_cleanup')


def get_apt_repositories_text(repos):
    os_issue, os_ver = check_os()
    t = repos.get(os_issue)
    if t:
        for versions, text in t.iteritems():
            if os_ver in versions:
                return text
    raise RuntimeError('Does not exists apt repositories for "{}" version "{}"'.format(os_issue, os_ver))


def get_apt_repo_install_keys_commands(repos_install_keys_commands):
    os_issue, os_ver = check_os()
    t = repos_install_keys_commands.get(os_issue)
    if t:
        for versions, commands in t.iteritems():
            if os_ver in versions:
                return commands
    return ()


def set_apt_repositories(repos, repos_install_keys_commands, subconf_name=None):
    check_sudo()
    check_os()
    print_green('INFO: Set apt repositories...')
    repositories_f = StringIO(get_apt_repositories_text(repos))
    if subconf_name:
        put(repositories_f,
            '/etc/apt/sources.list.d/{}.list'.format(subconf_name.strip()),
            mode=0644, use_sudo=True)
    else:
        sudo('mv /etc/apt/sources.list /etc/apt/sources.list.bak', warn_only=True)
        put(repositories_f, '/etc/apt/sources.list',
            mode=0644, use_sudo=True)
    for command in get_apt_repo_install_keys_commands(repos_install_keys_commands):
        sudo(command)
    print_green('INFO: Set apt repositories... OK')


# # # COMMANDS # # #


@task
def apt_update():
    """
    aptitude update
    """
    check_sudo()
    check_os()
    print_green('INFO: Apt update...')
    sudo('aptitude update -q -y')
    print_green('INFO: Apt update... OK')


@task
def apt_upgrade():
    """
    aptitude upgrade
    """
    check_sudo()
    check_os()
    print_green('INFO: APT upgrade...')
    sudo('aptitude upgrade -q -y')
    print_green('INFO: APT upgrade... OK')


@task
def apt_dist_upgrade():
    """
    aptitude dist-upgrade
    """
    check_sudo()
    check_os()
    print_green('INFO: APT dist upgrade...')
    sudo('aptitude dist-upgrade -q -y')
    print_green('INFO: APT dist upgrade... OK')


@task
def apt_install(pkgs, comment=None, noconfirm=False):
    """
    aptitude install ...
    """
    check_sudo()
    check_os()
    assert isinstance(pkgs, basestring)
    pkgs = ' '.join(pkgs.split())
    comment = ' {}'.format(comment) if comment else ''
    if not noconfirm and not confirm('Do you want to apt install {}?{}'.format(pkgs, comment)):
        return
    print_green('INFO: Apt install {}...'.format(pkgs))
    sudo('aptitude install {} -q -y'.format(pkgs))
    print_green('INFO: Apt install {}... OK'.format(pkgs))


@task
def apt_cleanup():
    """
    aptitude autoclean and clean
    """
    check_sudo()
    check_os()
    if not confirm('Do you want to apt clean up?'):
        return
    print_green('INFO: Apt clean up...')
    sudo('aptitude autoclean -q -y')
    sudo('aptitude clean -q -y')
    print_green('INFO: Apt clean up... OK')
