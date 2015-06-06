import re
import socket
from StringIO import StringIO
from fabric.context_managers import settings
from fabric.state import env
from fabdeb.apt import apt_install
from fabdeb.fab_tools import print_green, print_red, print_yellow
from fabric.contrib.console import confirm
from fabric.contrib.files import exists, comment, append
from fabric.operations import sudo, prompt, get, put, os
from fabric.utils import abort


SUPPORT_OS = {
    'Debian GNU/Linux 8': ('8.0',)
}


OS_REPOSITORIES = {
    'Debian GNU/Linux 8': {
        ('8.0',): ('deb http://http.debian.net/debian jessie main contrib non-free\n'
                   'deb-src http://http.debian.net/debian jessie main contrib non-free\n'
                   '\n'
                   'deb http://http.debian.net/debian jessie-updates main contrib non-free\n'
                   'deb-src http://http.debian.net/debian jessie-updates main contrib non-free\n'
                   '\n'
                   'deb http://security.debian.org/ jessie/updates main contrib non-free\n'
                   'deb-src http://security.debian.org/ jessie/updates main contrib non-free\n'),
    },
}


OS_REPOS_INSTALL_KEYS_COMMANDS = {}


# # # COMMANDS # # #


def check_sudo():
    print_green('INFO: Check sudo...')
    t = sudo('whoami', quiet=True)
    if t.failed:
        print_red('NOTE: For using this fabfile you need to install sudo:\n'
                  '  # aptitude install sudo\n'
                  'and add your non-root user to group sudo:\n'
                  '  # adduser YourNonRootUserName sudo')
        abort(t)
    print_green('INFO: Check sudo... OK')


def check_os():
    print_green('INFO: Check your OS...')
    remote_os_issue = sudo('cat /etc/issue', quiet=True)
    os_issue = os_ver = ok = None
    for os_issue, os_ver in SUPPORT_OS.iteritems():
        if os_issue in remote_os_issue:
            ok = True
            break
    if not ok:
        abort('Your OS "{}" is not supported :('.format(remote_os_issue))
    remote_os_ver = sudo('cat /etc/debian_version', quiet=True).strip()
    if remote_os_ver not in os_ver:
        abort('Your OS "{}" version "{}" is not supported :('.format(remote_os_issue, remote_os_ver))
    print_green('INFO: Check your OS... OK')
    return os_issue, remote_os_ver


def setup_swap():
    print_green('INFO: Setup SWAP...')
    t = sudo('swapon -s', quiet=True)
    if not re.search(r'\s\d+\s', t):
        swap_size = int(prompt("Server doesn't have SWAP. Set size in MB to create SWAP. Keep 0 to skip.",
                               default='0', validate=r'\d+'))
        if swap_size:
            swap_fn = '/swapfile'
            sudo('fallocate -l {size}M {sfn}'.format(size=swap_size, sfn=swap_fn))
            command_defrag = 'e4defrag {sfn}'.format(sfn=swap_fn)
            print_green('Defragmenting swap file: {}...'.format(command_defrag))
            sudo(command_defrag, quiet=True)
            sudo('chown root:root {sfn} && chmod 600 {sfn}'.format(sfn=swap_fn))
            sudo('mkswap {sfn}'.format(sfn=swap_fn))
            sudo('swapon {sfn}'.format(sfn=swap_fn))
            append('/etc/fstab', '{sfn} swap swap defaults 0 0'.format(sfn=swap_fn), use_sudo=True)
            swappiness_size = int(prompt("Set vm.swappiness parameter to /etc/sysctl.conf",
                                         default='10', validate=r'\d+'))
            append('/etc/sysctl.conf', 'vm.swappiness={}'.format(swappiness_size), use_sudo=True)
            sudo('sysctl -p')
    print_green('INFO: Setup SWAP... OK')


def configure_hostname():
    print_green('INFO: Configure hostname...')
    chn = sudo('cat /etc/hostname').strip()
    nhn = prompt('Set hostname', default=chn, validate=r'[\w\.\-]+')
    ip = prompt('Set host ip', default=socket.gethostbyname(env.host),
                validate=r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
    sudo('echo "{}" > /etc/hostname'.format(nhn))
    comment('/etc/hosts', r'127.0.0.1', use_sudo=True)
    comment('/etc/hosts', r'127.0.1.1', use_sudo=True, backup='')
    append('/etc/hosts', '\n127.0.0.1\tlocalhost', use_sudo=True)
    append('/etc/hosts', '127.0.1.1\t{}'.format(nhn.split('.')[0]), use_sudo=True)
    append('/etc/hosts', '{}\t{}'.format(ip, nhn), use_sudo=True)
    sudo('/etc/init.d/hostname.sh start')
    sudo('hostname {}'.format(nhn))
    print_green('INFO: Configure hostname... OK')


def configure_timezone():
    print_green('INFO: Configure timezone...')
    current_tz = sudo('cat /etc/timezone', quiet=True).strip()

    def validate_tz(tz):
        tz = tz.strip()
        fn = '/usr/share/zoneinfo/{}'.format(tz)
        if ('.' not in tz and exists(fn, use_sudo=True) and
                sudo('cat {}'.format(fn), quiet=True)[:4] == 'TZif'):
            return tz
        raise ValueError('Invalid timezone. See http://twiki.org/cgi-bin/xtra/tzdatepick.html')

    new_timezone = prompt('Set timezone', default=current_tz, validate=validate_tz)
    if current_tz != new_timezone:
        sudo('echo "{}" > /etc/timezone'.format(new_timezone))
    print_green('INFO: Configure timezone... OK')


def user_exists(username):
    return exists('/home/{}'.format(username), use_sudo=True)


def add_user(username, skip_confirm=False):
    if user_exists(username):
        abort('User {} exists'.format(username))
    if not skip_confirm:
        if not confirm('Do you want to create new user?'):
            return
    print_green('INFO: Add system user "{}"...'.format(username))
    sudo('adduser {}'.format(username))
    from fabdeb.python import configure_virtualenvwrapper_for_user
    configure_virtualenvwrapper_for_user(username)
    from fabdeb.tools import add_user_to_proftpd
    add_user_to_proftpd(username)
    print_green('INFO: Add system user "{}"... OK'.format(username))


def install_ntp():
    if not confirm('Do you want install NTP client?'):
        return
    print_green('INFO: Install ntp...')
    apt_install(('ntp', 'ntpdate'))
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


def install_exim4():
    if not confirm('Do you want install exim4?'):
        return
    print_green('INFO: Install exim4...')
    apt_install(('exim4',))
    dkim_keys_path = '/etc/exim4/dkim'
    print_red('You need run exim4 configure:\n'
              '    # dpkg-reconfigure exim4-config\n'
              'and set options:\n'
              '    General type of mail configuration: internet site; ...using SMTP\n'
              '    System mail name: your-real-domain.com\n'
              '    IP-address to listen on for incoming SMTP connectins: 127.0.0.1; ::1\n'
              '    Other destinations for which mail is accepted: <allow empty>\n'
              '    Domains to relay mail for: <allow empty>\n'
              '    Machines to relay mail for: <allow empty>\n'
              '    Keep number of DNS-queries minimal: No\n'
              '    Delivery method for local mail: mbox format\n'
              '    Split configuration into small files: No\n')
    if confirm('Do you want install opendkim and setup dkim in exim4?'):
        apt_install(('opendkim', 'opendkim-tools'))
        sudo('mkdir {}'.format(dkim_keys_path), warn_only=True)
        sudo('chown Debian-exim:Debian-exim {dkp} && chmod 700 {dkp}'.format(dkp=dkim_keys_path))
        dkim_selector = prompt('Set DKIM selector name', default='mail', validate=r'[\w]+')
        sudo('cp /etc/exim4/exim4.conf.template /etc/exim4/exim4.conf.template.bak')
        t = StringIO()
        get('/etc/exim4/exim4.conf.template', local_path=t, use_sudo=True)
        t = StringIO(re.sub(
            r'(# This transport is used for delivering messages over SMTP connections\.\n).*?'
            r'(remote_smtp:.+?driver = smtp\n).+?(\.ifdef)',
            r'\1\n'
            r'DKIM_DOMAIN_NAME = ${{lc:${{domain:$h_from:}}}}\n'
            r'DKIM_FILE = {dkp}/${{lc:${{domain:$h_from:}}}}.key\n'
            r'DKIM_PRIV_KEY = ${{if exists{{DKIM_FILE}}{{DKIM_FILE}}{{0}}}}\n\n'
            r'\2\n'
            r'  dkim_domain = DKIM_DOMAIN_NAME\n'
            r'  dkim_selector = {dsn}\n'
            r'  dkim_private_key = DKIM_PRIV_KEY\n\n'
            r'\3'.format(dkp=dkim_keys_path, dsn=dkim_selector),
            t.getvalue(),
            flags=(re.M | re.S)
        ))
        put(t, '/etc/exim4/exim4.conf.template', use_sudo=True)
        sudo('chown root:root {cfn} && chmod 644 {cfn}'.format(cfn='/etc/exim4/exim4.conf.template'))
        print_red('You need to have DKIM keys.:\n'
                  'You can generate their:\n'
                  '    # opendkim-genkey -D {dkp} -d your-real-domain.com -s {dsn}\n'
                  '    # mv {dkp}/{dsn}.private {dkp}/your-real-domain.com.key\n'
                  '    # mv {dkp}/{dsn}.txt {dkp}/your-real-domain.com.txt\n'
                  '    # chown Debian-exim:Debian-exim {dkp}/*\n'
                  '    # chmod 600 {dkp}/*\n'
                  'Set DNS record for your your-real-domain.com from {dkp}/your-real-domain.com.txt\n'
                  'And may set DNS ADSP record:\n'
                  '    _adsp._domainkey IN TXT "dkim=all"\n'
                  'For test sending mail run:\n'
                  '    # echo testmail | /usr/sbin/sendmail you.real.email@maildomain.com\n'
                  ''.format(dkp=dkim_keys_path, dsn=dkim_selector))
        sudo('service exim4 restart', warn_only=True)
    print_green('INFO: Install exim4... OK')


def install_user_rsa_key(username):
    if not user_exists:
        abort('User {} noes not exist'.format(username))
    if not confirm('Do you want set SSH key?'):
        return
    print_green('INFO: Set SSH key...')
    print_yellow('Setup SSH key methods:\n'
                 '1: Generate new ~/.ssh/id_rsa key and manually add public key to remote servers.\n'
                 '2: Copy exists SSH RSA key from local to ~/.ssh/id_rsa.\n'
                 '3: Copy exists SSH RSA key from local to ~/.ssh/{keyname}.rsa and configure ~/.ssh/config.')
    n = prompt('Select method', default='1', validate='[1-3]')

    def file_exists_validator(fn):
        fn = fn.replace('\\', '/')
        if not os.path.exists(fn):
            raise ValueError('File {} does not exist.'.format(fn))
        return fn

    with settings(sudo_user=username, user=username, group=username):
        sudo('mkdir ~/.ssh', warn_only=True)
    if n == '1':
        with settings(sudo_user=username, user=username, group=username):
            sudo('ssh-keygen -t rsa -b 2048 -f ~/.ssh/id_rsa')
            sudo('chmod 600 ~/.ssh/id_rsa', warn_only=True)
            pub = sudo('cat ~/.ssh/id_rsa.pub', quiet=True)
            print_red('Add this public key to remote host:\n\n{}\n\n'.format(pub))
        while not confirm('Did you do it?'):
            pass
    elif n == '2':
        local_key_fn = prompt('Set path to RSA key in local (in windows skip part "C:")',
                              default='/home/yourusername/.ssh/id_rsa', validate=file_exists_validator)
        put(local_key_fn, '/home/{}/.ssh/id_rsa'.format(username), use_sudo=True, mode=0600)
        sudo('chown {u}:{u} /home/{u}/.ssh/id_rsa'.format(u=username))
    elif n == '3':
        local_key_fn = prompt('Set path to RSA key in local (in windows skip part "C:")',
                              default='/home/yourusername/.ssh/id_rsa', validate=file_exists_validator)
        kn = prompt('Set key name which will be saved as ~/.ssh/{keyname}.rsa', default='key', validate='\w+')
        put(local_key_fn, '/home/{u}/.ssh/{kn}.rsa'.format(u=username, kn=kn), use_sudo=True, mode=0600)
        sudo('chown {u}:{u} /home/{u}/.ssh/{kn}.rsa'.format(u=username, kn=kn))
        h = p = u = None
        while True:
            h = prompt('Set hostname for which will be used ~/.ssh/{}.rsa key (without port!)'.format(kn),
                       default='github.com', validate='.+')
            p = prompt('Set port for which will be used ~/.ssh/{}.rsa key e.g. "22" (not requirement)'.format(kn),
                       default='', validate='|\d+')
            u = prompt('Set user for which will be used ~/.ssh/{}.rsa key e.g. "git" (not requirement)'.format(kn),
                       validate='|\w+')
            print_yellow(('HostHame: {h}\n'
                          'Port: {p}\n'
                          'User: {u}').format(h=h, p=(p or '-NONE-'), u=(u or '-NONE-')))
            if confirm('Are you confirm it?'):
                break
        cf = '~/.ssh/config'
        with settings(sudo_user=username, user=username, group=username):
            append(cf, '\nHost {}'.format(h), use_sudo=True)
            append(cf, '\tHostName  {}'.format(h), use_sudo=True)
            append(cf, '\tIdentityFile ~/.ssh/{}.rsa'.format(kn), use_sudo=True)
            if p:
                append(cf, '\tPort {}'.format(p), use_sudo=True)
            if u:
                append(cf, '\tUser {}'.format(u), use_sudo=True)
    else:
        abort('Unknown method')
    print_green('INFO: Set SSH key... OK')
