from StringIO import StringIO
from fabric.contrib.console import confirm
from fabric.operations import sudo, put
from fabdeb.tools import print_green


def get_apt_repositories_text(repos, os_issue, os_ver):
    t = repos.get(os_issue)
    if t:
        for versions, text in t.iteritems():
            if os_ver in versions:
                return text
    raise RuntimeError('Does not exists apt repositories for "{}" version "{}"'.format(os_issue, os_ver))


def get_apt_repo_install_keys_commands(repos_install_keys_commands, os_issue, os_ver):
    t = repos_install_keys_commands.get(os_issue)
    if t:
        for versions, commands in t.iteritems():
            if os_ver in versions:
                return commands
    return ()


# # # COMMANDS # # #


def set_apt_repositories(repos, repos_install_keys_commands, os_issue, os_ver, subconf_name=None):
    print_green('INFO: Set apt repositories...')
    repositories_f = StringIO(get_apt_repositories_text(repos, os_issue, os_ver))
    if subconf_name:
        put(repositories_f,
            '/etc/apt/sources.list.d/{}.list'.format(subconf_name.strip()),
            mode=0644, use_sudo=True)
    else:
        sudo('mv /etc/apt/sources.list /etc/apt/sources.list.bak', warn_only=True)
        put(repositories_f, '/etc/apt/sources.list',
            mode=0644, use_sudo=True)
    for command in get_apt_repo_install_keys_commands(repos_install_keys_commands, os_issue, os_ver):
        sudo(command)
    print_green('INFO: Set apt repositories... OK')


def apt_update():
    print_green('INFO: Apt update...')
    sudo('aptitude update -q -y')
    print_green('INFO: Apt update... OK')


def apt_upgrade():
    print_green('INFO: APT upgrade...')
    sudo('aptitude upgrade -q -y')
    print_green('INFO: APT upgrade... OK')


def apt_install(pkgs, comment=None, noconfirm=False):
    assert isinstance(pkgs, (list, tuple, set, frozenset, basestring))
    if isinstance(pkgs, basestring):
        pkgs = (pkgs,)
    pkgs_str = ' '.join(pkgs)
    comment = ' {}'.format(comment) if comment else ''
    if not noconfirm and not confirm('Do you want to apt install {}?{}'.format(pkgs_str, comment)):
        return
    print_green('INFO: Apt install {}...'.format(pkgs_str))
    sudo('aptitude install {} -q -y'.format(pkgs_str))
    print_green('INFO: Apt install {}... OK'.format(pkgs_str))


def apt_cleanup():
    if not confirm('Do you want to apt clean up?'):
        return
    print_green('INFO: Apt clean up...')
    sudo('aptitude autoclean -q -y')
    sudo('aptitude clean -q -y')
    print_green('INFO: Apt clean up... OK')
