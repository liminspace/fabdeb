import re
from fabdeb.apt import set_apt_repositories, apt_update, apt_install
from fabdeb.fab_tools import print_green
from fabric.context_managers import cd, hide, settings
from fabric.contrib.console import confirm
from fabric.contrib.files import sed, append
from fabric.operations import sudo, prompt


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


def bind_validate(s):
    ips = s.strip().split(' ')
    ipv4_regex = r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    err_msg = ('Invalid value. Set IP or several ones separated by space:\n'
               '  127.0.0.1\n  127.0.0.1 192.168.56.111')
    if not ips:
        raise ValueError(err_msg)
    for ip in ips:
        if not re.match(ipv4_regex, ip):
            raise ValueError(err_msg)
    return ' '.join(ips)


# # # COMMANDS # # #


def install_redis():
    if not confirm('Do you want to install Redis?'):
        return
    print_green('INFO: Install Redis...')
    with cd('/tmp'):
        sudo('wget -q http://download.redis.io/redis-stable.tar.gz')
        sudo('tar xzf redis-stable.tar.gz')
        sudo('rm redis-stable.tar.gz')
    with cd('/tmp/redis-stable'):
        sudo('make')
        sudo('make test')
        sudo('make install')
        conf_fn = None
        while True:
            out = sudo('utils/install_server.sh', warn_only=True)
            if out.failed:
                if confirm('Do you want to repeat run install_server.sh?'):
                    continue
            else:
                conf_fn = re.search(r'Config file\s+:\s(.+?)\n', out).group(1).strip()
            break
    if conf_fn:
        bind = prompt('Set bind IP address (or addresses separated by space)', default='127.0.0.1',
                      validate=bind_validate)
        dbs = prompt('Set dadabases count', default='20', validate='\d+')
        sed(conf_fn, r'(# bind 127.0.0.1)', r'\1\nbind {}'.format(bind), use_sudo=True)
        sed(conf_fn, r'(databases [0-9]+)', r'# \1\ndatabases {}'.format(dbs), use_sudo=True)
    with cd('/tmp'):
        sudo('rm -rf redis-stable')
        if confirm('Do you want to set parameter vm.overcommit_memory=1 to /etc/sysctl.conf? (Recommended)'):
            append('/etc/sysctl.conf', 'vm.overcommit_memory=1', use_sudo=True)
    print_green('INFO: Install Redis... OK')


def install_postgresql(os_issue, os_ver, ver='9.4'):
    assert ver in ('9.4',)
    if not confirm('Do you want to install PostreSQL {}?'.format(ver)):
        return
    print_green('INFO: Install PostreSQL {}...'.format(ver))
    set_apt_repositories(POSTGRESQL_REPOSITORIES, POSTGRESQL_REPOS_INSTALL_KEYS_COMMANDS, os_issue, os_ver,
                         subconf_name='postgresql')
    apt_update()
    apt_install(('postgresql-{}'.format(ver), 'postgresql-server-dev-{}'.format(ver), 'libpq-dev'))
    from fabdeb.tools import password_prompt
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
    from fabdeb.tools import password_prompt
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
