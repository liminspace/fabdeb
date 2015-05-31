import re
from fabdeb.apt import apt_install
from fabdeb.fab_tools import print_green, print_red, print_yellow
from fabric.contrib.console import confirm
from fabric.contrib.files import exists, comment, append
from fabric.operations import sudo, prompt
from fabric.utils import abort


SUPPORT_OS = {
    'Debian GNU/Linux 8': ('8.0',)
}


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
    print_green('INFO: OK')


def check_os():
    print_green('INFO: Check your os...')
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
    print_green('INFO: Check your os... OK')
    return os_issue, remote_os_ver


def setup_swap():
    print_green('INFO: Setup SWAP...')
    t = sudo('swapon -s', quiet=True)
    if not re.search(r'\s\d+\s', t):
        swap_size = int(prompt("Server doesn't have SWAP. Write size in MB to create SWAP. Keep 0 to skip.",
                               default='0', validate=r'\d+'))
        if swap_size:
            sudo('fallocate -l {}M /swapfile'.format(swap_size))
            command_defrag = 'e4defrag /swapfile'
            print_green('Defragmenting swap file: {}...'.format(command_defrag))
            sudo(command_defrag, quiet=True)
            sudo('chown root:root /swapfile')
            sudo('chmod 600 /swapfile')
            sudo('mkswap /swapfile')
            sudo('swapon /swapfile')
            append('/etc/fstab', '/swapfile swap swap defaults 0 0', use_sudo=True)
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
