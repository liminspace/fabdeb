import re
from StringIO import StringIO
from fabric.contrib.files import exists, sed, uncomment
from fabric.utils import abort
from fabdeb.apt import apt_install
from fabdeb.fab_tools import print_green
from fabric.context_managers import cd
from fabric.contrib.console import confirm
from fabric.operations import sudo, put, prompt


# # # COMMANDS # # #


def install_pngquant():
    if not confirm('Do you want to install pngquant?'):
        return
    print_green('INFO: Install pngquant...')
    apt_install(('libpng-dev', 'liblcms2-dev'))
    with cd('/tmp'):
        sudo('wget -q https://github.com/pornel/pngquant/archive/master.zip')
        sudo('unzip master.zip')
        sudo('rm master.zip')
    with cd('/tmp/pngquant-master'):
        sudo('./configure --with-lcms2 && make')
        sudo('make install')
        if confirm('Do you want make symlink /usr/local/bin/pngquant to /bin/pngquant?'):
            sudo('ln -s /usr/local/bin/pngquant /bin/pngquant')
    with cd('/tmp'):
        sudo('rm -rf pngquant-master')
    print_green('INFO: Install pngquant...  OK')


def install_supervisor():
    if not confirm('Do you want to install supervisor?'):
        return
    print_green('INFO: Install supervisor...')
    apt_install(('supervisor',))
    print_green('INFO: Install supervisor... OK')


def reboot():
    if not confirm('Do you want to reboot server?'):
        return
    sudo('shutdown -r now')


def install_proftpd():
    if not confirm('Do you want to install proftpd?'):
        return
    print_green('INFO: Install proftpd...')
    apt_install(('proftpd',))
    conf_fn = '/etc/proftpd/proftpd.conf'
    sudo('cp {fn} {fn}.bak'.format(fn=conf_fn), warn_only=True)
    sed(conf_fn, r'UseIPv6\s+on', r'UseIPv6\t\t\t\toff\nUseReverseDNS\t\t\toff', use_sudo=True, backup='')
    sn = prompt('Set ftp server name', default='MyFTPServer', validate=r'[\w\- ]+')
    sed(conf_fn, r'ServerName\s+".+"', r'ServerName\t\t\t"{}"'.format(sn), use_sudo=True, backup='')
    sed(conf_fn, r'TimeoutNoTransfer.+', r'TimeoutNoTransfer\t\t3600', use_sudo=True, backup='')
    sed(conf_fn, r'TimeoutStalled.+', r'TimeoutStalled\t\t\t3600', use_sudo=True, backup='')
    sed(conf_fn, r'TimeoutIdle.+', r'TimeoutIdle\t\t\t7200', use_sudo=True, backup='')
    uncomment(conf_fn, r'#\s*DefaultRoot', use_sudo=True, backup='')
    uncomment(conf_fn, r'#\s*RequireValidShell', use_sudo=True, backup='')
    uncomment(conf_fn, r'#\s*PassivePorts', use_sudo=True, backup='')
    t = (r'<Global>\n'
         r'    RootLogin off\n'
         r'</Global>\n'
         r'AuthUserFile /etc/proftpd/ftpd.passwd\n'
         r'<Directory ~/>\n'
         r'    HideFiles "(\\\\.ftpaccess)$"\n'
         r'</Directory>\n')
    sed(conf_fn, r'(# Include other custom configuration files)', r'{}\n\1'.format(t), use_sudo=True, backup='')
    print_green('INFO: Install proftpd... OK')


def add_user_to_proftpd(username):
    if not confirm('Do you want to setup proftpd for user "{}"?'.format(username)):
        return
    if not exists('/usr/sbin/proftpd'):
        abort('proftpd is not installed')
    print_green('INFO: Add user "{}" to proftpd...'.format(username))
    from fabdeb.os import user_exists
    if not user_exists(username):
        abort('User {} does not exists'.format(username))
    t = sudo('id {}'.format(username))
    uid, gid = re.search(r'uid=(\d+)\(.+gid=(\d+)\(', t).groups()
    passwd_fn = '/etc/proftpd/ftpd.passwd'
    sudo('ftpasswd --passwd --file={passwd} --name={user} --shell=/bin/false '
         '--home=/home/{user} --uid={uid} --gid={gid}'.format(passwd=passwd_fn, user=username, uid=uid, gid=gid))
    ftpaccess = ('<Limit READ WRITE DIRS>\n'
                 '    Order deny,allow\n'
                 '    Allowuser {user}\n'
                 '</Limit>\n').format(user=username)
    put(StringIO(ftpaccess), '/home/{}/.ftpaccess'.format(username), use_sudo=True)
    if confirm('Do you want to restart proftpd?'):
        sudo('service proftpd restart', warn_only=True)
    print_green('INFO: Add user "{}" to proftpd... OK'.format(username))
