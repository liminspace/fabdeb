from StringIO import StringIO
from fabdeb.fab_tools import print_green
from fabric.operations import sudo, put


APT_REPOSITORIES = {
    'Debian GNU/Linux 8': {
        ('8.0',): (
            'deb http://ftp.us.debian.org/debian jessie main contrib non-free\n'
            'deb-src http://ftp.us.debian.org/debian jessie main contrib non-free\n'
            '\n'
            'deb http://ftp.debian.org/debian/ jessie-updates main contrib non-free\n'
            'deb-src http://ftp.debian.org/debian/ jessie-updates main contrib non-free\n'
            '\n'
            'deb http://security.debian.org/ jessie/updates main contrib non-free\n'
            'deb-src http://security.debian.org/ jessie/updates main contrib non-free\n'
            '\n'
            'deb http://apt.postgresql.org/pub/repos/apt/ jessie-pgdg main\n'
            '\n'
            'deb http://nginx.org/packages/debian/ jessie nginx\n'
            'deb-src http://nginx.org/packages/debian/ jessie nginx\n'),
    },
}


APT_REPO_INSTALL_KEYS_COMMANDS = {
    'Debian GNU/Linux 8': {
        ('8.0',): (
            'wget -q -O - http://nginx.org/keys/nginx_signing.key | apt-key add -',
            'wget -q -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -',
        ),
    },
}


def get_apt_repositories_text(os_issue, os_ver):
    t = APT_REPOSITORIES.get(os_issue)
    if t:
        for versions, text in t.iteritems():
            if os_ver in versions:
                return text
    raise RuntimeError('Does not exists apt repositories for "{}" version "{}"'.format(os_issue, os_ver))


def get_apt_repo_install_keys_commands(os_issue, os_ver):
    t = APT_REPO_INSTALL_KEYS_COMMANDS.get(os_issue)
    if t:
        for versions, commands in t.iteritems():
            if os_ver in versions:
                return commands
    return ()


# # # COMMANDS # # #


def set_apt_repositories(os_issue, os_ver):
    print_green('INFO: Set apt repositories...')
    sudo('mv /etc/apt/sources.list /etc/apt/sources.list.bak', warn_only=True)
    put(StringIO(get_apt_repositories_text(os_issue, os_ver)), '/etc/apt/sources.list', mode=0644, use_sudo=True)
    for command in get_apt_repo_install_keys_commands(os_issue, os_ver):
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


def apt_install(pkgs):
    assert isinstance(pkgs, (list, tuple, set, frozenset))
    pkgs_str = ' '.join(pkgs)
    print_green('INFO: Apt install {}...'.format(pkgs_str))
    sudo('aptitude install {} -q -y'.format(pkgs_str))
    print_green('INFO: Apt install {}... OK'.format(pkgs_str))
