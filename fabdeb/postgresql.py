import re
from StringIO import StringIO
from fabric.context_managers import hide, settings
from fabric.contrib.console import confirm
from fabric.contrib.files import sed, append
from fabric.operations import sudo, prompt, get, put
from fabdeb.apt import set_apt_repositories, apt_update, apt_install
from fabdeb.os import service_restart
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
    la = prompt('Set listen_addresses (hostname or ip, comma separated; set * for all)', default='localhost',
                validate='[\w\.\-\*]+').strip()
    t = StringIO()
    postgresql_conf = '/etc/postgresql/{}/main/postgresql.conf'.format(ver)
    get(postgresql_conf, local_path=t, use_sudo=True)
    t = StringIO(re.sub(r"#listen_addresses = 'localhost'", r"listen_addresses = '{}'".format(la), t.getvalue()))
    put(t, postgresql_conf, use_sudo=True)
    sudo('chown postgres:postgres {}'.format(postgresql_conf))
    sudo('chmod 644 {}'.format(postgresql_conf))
    hba = '/etc/postgresql/{}/main/pg_hba.conf'.format(ver)
    sed(hba, r'(local\s+all\s+all\s+)peer', r'\1md5', use_sudo=True)
    if confirm('Do you wand to allow connect to PostgreSQL from out?'):
        append(hba, 'host     all             all             0.0.0.0/0               md5', use_sudo=True)
    if confirm('Do you want to restart PostgreSQL?'):
        service_restart('postgresql')
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
