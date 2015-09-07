import re
import socket
from fabric.context_managers import settings
from fabric.decorators import task
from fabric.network import disconnect_all
from fabric.state import env
from fabric.contrib.console import confirm
from fabric.contrib.files import exists, comment, append, uncomment
from fabric.operations import sudo, prompt, put, os, reboot
from fabric.utils import abort
from fabdeb.tools import print_green, print_yellow, print_red


__all__ = ('check_sudo', 'setup_swap', 'configure_hostname', 'configure_timezone', 'add_user', 'install_user_rsa_key',
           'service_restart', 'server_reboot', 'update_locale')


SUPPORT_OS = {
    'Debian GNU/Linux 8': ('8.0', '8.1', '8.2')
}


OS_REPOSITORIES = {
    'Debian GNU/Linux 8': {
        ('8.0', '8.1', '8.2'): (
            'deb http://http.debian.net/debian jessie main contrib non-free\n'
            'deb-src http://http.debian.net/debian jessie main contrib non-free\n'
            '\n'
            'deb http://http.debian.net/debian jessie-updates main contrib non-free\n'
            'deb-src http://http.debian.net/debian jessie-updates main contrib non-free\n'
            '\n'
            'deb http://security.debian.org/ jessie/updates main contrib non-free\n'
            'deb-src http://security.debian.org/ jessie/updates main contrib non-free\n'
        ),
    },
}


OS_REPOS_INSTALL_KEYS_COMMANDS = {}


def user_exists(username):
    return exists('/home/{}'.format(username), use_sudo=True)


# # # COMMANDS # # #


@task
def check_os():
    """
    Check OS supported by fabdeb
    """
    if '_fd_checked_os_' in env:
        return env._fd_checked_os_
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
    env._fd_checked_os_ = os_issue, remote_os_ver
    return env._fd_checked_os_


@task
def check_sudo():
    """
    Check available sudo command
    """
    if '_fd_checked_sudo_' in env:
        return
    print_green('INFO: Check sudo...')
    t = sudo('whoami', quiet=True)
    if t.failed:
        print_red('NOTE: For using this fabfile you need to install sudo:\n'
                  '  # aptitude install sudo\n'
                  'and add your non-root user to group sudo:\n'
                  '  # adduser YourNonRootUserName sudo')
        abort(t)
    print_green('INFO: Check sudo... OK')
    env._fd_checked_sudo_ = True


@task
def setup_swap():
    """
    Setup SWAP and configure swappiness
    """
    check_sudo()
    check_os()
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


@task
def configure_hostname():
    """
    Configure hostname, host ip, /etc/hosts
    """
    check_sudo()
    check_os()
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


@task
def configure_timezone():
    """
    Configure timezone
    """
    check_sudo()
    check_os()
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


@task
def add_user(username, skip_confirm=False):
    """
    Add new system user
    """
    check_sudo()
    check_os()
    if user_exists(username):
        abort('User {} exists'.format(username))
    if not skip_confirm:
        if not confirm('Do you want to create new user?'):
            return
    print_green('INFO: Add system user "{}"...'.format(username))
    sudo('adduser {}'.format(username))
    uncomment('/home/{}/.bashrc'.format(username), r'#\s*force_color_prompt=yes', use_sudo=True)
    from fabdeb.python import configure_virtualenvwrapper_for_user
    configure_virtualenvwrapper_for_user(username)
    from fabdeb.ftp import add_user_to_proftpd
    add_user_to_proftpd(username)
    print_green('INFO: Add system user "{}"... OK'.format(username))


@task
def install_user_rsa_key(username):
    """
    Install RSA/SSH key for user
    """
    check_sudo()
    check_os()
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


@task
def service_restart(service_name, attempt=5):
    """
    service ... stop; service ... start
    """
    check_sudo()
    check_os()
    n = 1
    while True:
        r = sudo('service {s} stop; service {s} start'.format(s=service_name), warn_only=True)
        if r.succeeded:
            break
        if n >= attempt:
            abort('')
        n += 1


@task
def server_reboot():
    """
    Reboot host
    """
    check_sudo()
    check_os()
    if not confirm('Do you want to reboot server?'):
        return
    reboot(wait=180)


@task
def update_locale():
    """
    Setup en_US.UTF-8 system locale
    """
    check_sudo()
    check_os()
    comment('/etc/locale.gen', r'^[^#]', use_sudo=True)
    uncomment('/etc/locale.gen', r'en_US\.UTF\-8', use_sudo=True, backup='')
    sudo('locale-gen')
    sudo('echo \'LANGUAGE="en_US.UTF-8"\' > /etc/default/locale')  # will be locale warning. it's ok
    sudo('echo \'LANG="en_US.UTF-8"\' >> /etc/default/locale')
    sudo('echo \'LC_ALL="en_US.UTF-8"\' >> /etc/default/locale')
    disconnect_all()
