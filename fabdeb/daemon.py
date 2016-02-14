from fabric.contrib.console import confirm
from fabric.contrib.files import comment, append, exists
from fabric.decorators import task
from fabric.operations import prompt, sudo, put, os
from fabdeb.apt import apt_install
from fabdeb.os import check_sudo, check_os
from fabdeb.tools import print_green, print_red, print_yellow


__all__ = ('install_supervisor', 'install_supervisor_latest', 'install_ntp')


# # # COMMANDS # # #


@task
def install_supervisor():
    """
    Install supervisor daemon
    """
    check_sudo()
    check_os()
    if not confirm('Do you want to install supervisor?'):
        return
    print_green('INFO: Install supervisor...')
    apt_install('supervisor', noconfirm=True)
    print_green('INFO: Install supervisor... OK')


@task
def install_supervisor_latest():
    """
    Install supervisor daemon from python repository.
    """
    check_sudo()
    check_os()
    if not confirm('Do you want to install supervisor?'):
        return
    print_green('INFO: Install supervisor...')
    sudo('pip2.7 install -U supervisor')
    if not exists('/etc/supervisor', use_sudo=True):
        sudo('mkdir /etc/supervisor')
    if not exists('/etc/supervisor/conf.d', use_sudo=True):
        sudo('mkdir /etc/supervisor/conf.d')
    if not exists('/var/log/supervisor', use_sudo=True):
        sudo('mkdir /var/log/supervisor')
    put(os.path.join(os.path.dirname(__file__), 'confs', 'supervisord.conf'),
        '/etc/supervisor/supervisord.conf',
        use_sudo=True)
    put(os.path.join(os.path.dirname(__file__), 'scripts', 'supervisor'),
        '/etc/init.d/supervisor',
        use_sudo=True)
    sudo('chmod 775 /etc/init.d/supervisor')
    sudo('update-rc.d supervisor defaults')
    sudo('service supervisor start')
    print_green('INFO: Install supervisor... OK')


@task
def install_ntp():
    """
    Install ntp daemon
    """
    check_sudo()
    check_os()
    if not confirm('Do you want install NTP client?'):
        return
    print_green('INFO: Install ntp...')
    apt_install('ntp ntpdate', noconfirm=True)
    print_red("Go to http://www.pool.ntp.org/ and select servers in your server's country.\n"
              "For example (Ukraine):\n"
              "    0.ua.pool.ntp.org\n"
              "    1.ua.pool.ntp.org\n"
              "    2.ua.pool.ntp.org\n"
              "    3.ua.pool.ntp.org")

    def read_ntp_servers():
        ntp_server_list = []
        while True:
            t = prompt('Set NTP-server host. (Set empty string to continue)', default='').strip()
            if not t:
                break
            ntp_server_list.append(t)
        return ntp_server_list

    ntp_servers = None
    while True:
        ntp_servers = read_ntp_servers()
        print_yellow('You wrote following NTP-server list:\n    {}'.format(
            '\n    '.join(ntp_servers or ('-empty-',))
        ))
        if confirm('Are you confirm this NTP-server list?'):
            break
    if ntp_servers:
        ntp_conf_fn = '/etc/ntp.conf'
        comment(ntp_conf_fn, r'^server\s', use_sudo=True)
        for ntp_server in ntp_servers:
            append(ntp_conf_fn, 'server {} iburst'.format(ntp_server), use_sudo=True)
    print_green('INFO: Install ntp... OK')
