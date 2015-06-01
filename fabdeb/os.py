import re
from StringIO import StringIO
from fabdeb.apt import apt_install
from fabdeb.fab_tools import print_green, print_red, print_yellow
from fabric.contrib.console import confirm
from fabric.contrib.files import exists, comment, append
from fabric.operations import sudo, prompt, get, put
from fabric.utils import abort


SUPPORT_OS = {
    'Debian GNU/Linux 8': ('8.0',)
}


OS_REPOSITORIES = {
    'Debian GNU/Linux 8': {
        ('8.0',): ('deb http://ftp.us.debian.org/debian jessie main contrib non-free\n'
                   'deb-src http://ftp.us.debian.org/debian jessie main contrib non-free\n'
                   '\n'
                   'deb http://ftp.debian.org/debian/ jessie-updates main contrib non-free\n'
                   'deb-src http://ftp.debian.org/debian/ jessie-updates main contrib non-free\n'
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
        swap_size = int(prompt("Server doesn't have SWAP. Write size in MB to create SWAP. Keep 0 to skip.",
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
            t = prompt('Write NTP-server host. (Set empty string to continue)', default='').strip()
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
        dkim_selector = prompt('Set DKIM selector name', default='mail', validate='[\w]+')
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
        sudo('service exim4 restart')
    print_green('INFO: Install exim4... OK')
