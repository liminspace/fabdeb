import re
from StringIO import StringIO
from fabric.context_managers import hide, settings
from fabric.contrib.console import confirm
from fabric.contrib.files import sed, append
from fabric.decorators import task
from fabric.operations import sudo, prompt, get, put
from fabdeb.apt import set_apt_repositories, apt_update, apt_install
from fabdeb.os import service_restart, check_sudo, check_os
from fabdeb.tools import print_green, password_prompt


__all__ = ('install_postgresql', 'install_postgis', 'set_postgresql_user_password', 'add_user_to_postgresql',
           'add_db_to_postgresql', 'create_postgres_extensions_in_db')


POSTGRESQL_REPOSITORIES = {
    'Debian GNU/Linux 8': {
        ('8.0', '8.1', '8.2'): 'deb http://apt.postgresql.org/pub/repos/apt/ jessie-pgdg main\n',
    },
}


POSTGRESQL_REPOS_INSTALL_KEYS_COMMANDS = {
    'Debian GNU/Linux 8': {
        ('8.0', '8.1', '8.2'): ('wget -q -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -',),
    },
}


# # # COMMANDS # # #


@task
def install_postgresql(ver='9.4'):
    """
    Install PostgreSQL server
    """
    # simple settings helper http://pgtune.leopard.in.ua/
    assert ver in ('9.4',)
    check_sudo()
    check_os()
    if not confirm('Do you want to install PostreSQL {}?'.format(ver)):
        return
    print_green('INFO: Install PostreSQL {}...'.format(ver))
    set_apt_repositories(POSTGRESQL_REPOSITORIES, POSTGRESQL_REPOS_INSTALL_KEYS_COMMANDS, subconf_name='postgres')
    apt_update()
    apt_install('postgresql-{ver} postgresql-server-dev-{ver} libpq-dev'.format(ver=ver), noconfirm=True)
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
    install_postgis(postgres_ver=ver)
    if confirm('Do you want to restart PostgreSQL?'):
        service_restart('postgresql')
    print_green('INFO: Install PostreSQL {}... OK'.format(ver))


@task
def install_postgis(postgres_ver='9.4', postgis_ver='2.1'):
    """
    Install PostGIS for PostgreSQL
    """
    assert postgres_ver in ('9.4',)
    assert postgis_ver in ('2.1',)
    check_sudo()
    check_os()
    if not confirm('Do you want to install GEOS, GDAL, PROJ.4 and PostGIS?'):
        return
    print_green('INFO: Install GEOS, GDAL, PROJ.4 and PostGIS {} for PostgreSQL {}...'.format(postgis_ver,
                                                                                              postgres_ver))
    apt_install('libgeos-dev libgeos-c1 libgeos++-dev libgeos-3.4.2', noconfirm=True)
    apt_install('gdal-bin python-gdal libgdal-dev libgdal1-dev', noconfirm=True)
    apt_install('libproj-dev libproj0', noconfirm=True)
    apt_install('postgresql-{}-postgis-{} postgis'.format(postgres_ver, postgis_ver), noconfirm=True)
    apt_install('libgeoip1', noconfirm=True)
    apt_install('spatialite-bin', noconfirm=True)
    print_green('INFO: Install GEOS, GDAL, PROJ.4 and PostGIS {} for PostgreSQL {}... OK'.format(postgis_ver,
                                                                                                 postgres_ver))


@task
def set_postgresql_user_password(username, password):
    """
    Set password to PosgtreSQL-user
    """
    check_sudo()
    check_os()
    with hide('running'):
        sudo('sudo -u postgres psql -c "ALTER USER {} PASSWORD \'{}\';"'.format(username, password))


@task
def add_user_to_postgresql(username, return_pwd=False):
    """
    Add new PostgreSQL user
    """
    check_sudo()
    check_os()
    print_green('INFO: Adding user "{}" to PostreSQL...'.format(username))
    pwd = password_prompt('Set password to new postgresql user "{}"'.format(username))
    with settings(sudo_user='postgres'):
        sudo('createuser {}'.format(username))
    set_postgresql_user_password(username, pwd)
    print_green('INFO: Adding user "{}" to PostreSQL... OK'.format(username))
    return pwd if return_pwd else None


@task
def add_db_to_postgresql(dbname, owner=None):
    """
    Create new PostgreSQL database
    """
    check_sudo()
    check_os()
    print_green('INFO: Adding DB "{}" to PostreSQL...'.format(dbname))
    with settings(sudo_user='postgres'):
        if owner:
            sudo('createdb -O {} {}'.format(owner, dbname))
        else:
            sudo('createdb {}'.format(dbname))
    print_green('INFO: Adding DB "{}" to PostreSQL... OK'.format(dbname))


@task
def create_postgres_extensions_in_db(dbname, extensions):
    """
    Create PostGIS extension in PostgreSQL database
    """
    check_sudo()
    check_os()
    if isinstance(extensions, basestring):
        extensions = (extensions,)
    if not extensions:
        return
    for extension in extensions:
        if extension not in ('postgis', 'hstore'):
            raise AssertionError
    print_green('INFO: Create PostgreSQL extensions in DB "{}": {}...'.format(dbname, ', '.join(extensions)))
    for extension in extensions:
        sudo('sudo -u postgres psql -d {} -c "CREATE EXTENSION IF NOT EXISTS {};"'.format(dbname, extension))
    print_green('INFO: Create PostgreSQL extensions in DB "{}": {}... OK'.format(dbname, ', '.join(extensions)))
