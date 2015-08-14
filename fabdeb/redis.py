import re
from fabric.context_managers import cd
from fabric.contrib.console import confirm
from fabric.contrib.files import sed, append
from fabric.decorators import task
from fabric.operations import sudo, prompt
from fabdeb.os import check_sudo
from fabdeb.os import check_os
from fabdeb.tools import print_green


__all__ = ('install_redis',)


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


@task
def install_redis():
    """
    Install Redis-server
    """
    check_sudo()
    check_os()
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
