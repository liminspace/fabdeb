from fabric.context_managers import hide, settings
from fabric.contrib.console import confirm
from fabric.operations import sudo
from fabdeb.apt import set_apt_repositories, apt_update, apt_install
from fabdeb.tools import print_green, password_prompt

POSTGRESQL_REPOSITORIES = {
    'Debian GNU/Linux 8': {
        ('8.0', '8.1'): 'deb http://apt.postgresql.org/pub/repos/apt/ jessie-pgdg main\n',
    },
}


POSTGRESQL_REPOS_INSTALL_KEYS_COMMANDS = {
    'Debian GNU/Linux 8': {
        ('8.0', '8.1'): ('wget -q -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -',),
    },
}



# # # COMMANDS # # #


def install_postgresql(os_issue, os_ver, ver='9.4'):
    assert ver in ('9.4',)
    if not confirm('Do you want to install PostreSQL {}?'.format(ver)):
        return
    print_green('INFO: Install PostreSQL {}...'.format(ver))
    set_apt_repositories(POSTGRESQL_REPOSITORIES, POSTGRESQL_REPOS_INSTALL_KEYS_COMMANDS, os_issue, os_ver,
                         subconf_name='postgresql')
    apt_update()
    apt_install(('postgresql-{}'.format(ver), 'postgresql-server-dev-{}'.format(ver), 'libpq-dev'), noconfirm=True)
    set_postgresql_user_password('postgres', password_prompt('Set password to superuser postgres'))
    # listen_addresses = '*' > /etc/postgresql/9.4/main/postgresql.conf
    # host all all 0.0.0.0/0 md5 > /etc/postgresql/9.4/main/pg_hba.conf
    # local all all peer > local all all md5 > /etc/postgresql/9.4/main/pg_hba.conf
    # service postgresql restart
    print_green('INFO: Install PostreSQL {}... OK'.format(ver))


def set_postgresql_user_password(username, password):
    with hide('running'):
        sudo('sudo -u postgres psql -c "ALTER USER {} PASSWORD \'{}\';"'.format(username, password))


def add_user_to_postgresql(username, return_pwd=False):
    print_green('INFO: Adding user "{}" to PostreSQL...'.format(username))
    pwd = password_prompt('Set password to new postgresql user "{}"'.format(username))
    with settings(sudo_user='postgres'):
        sudo('createuser {}'.format(username))
    set_postgresql_user_password(username, pwd)
    print_green('INFO: Adding user "{}" to PostreSQL... OK'.format(username))
    return pwd if return_pwd else None


def add_db_to_postgresql(dbname, owner=None):
    print_green('INFO: Adding DB "{}" to PostreSQL...'.format(dbname))
    with settings(sudo_user='postgres'):
        if owner:
            sudo('createdb -O {} {}'.format(owner, dbname))
        else:
            sudo('createdb {}'.format(dbname))
    print_green('INFO: Adding DB "{}" to PostreSQL...'.format(dbname))
