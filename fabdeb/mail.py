import re
from StringIO import StringIO
from fabric.contrib.console import confirm
from fabric.decorators import task
from fabric.operations import sudo, prompt, get, put
from fabdeb.apt import apt_install
from fabdeb.os import service_restart, check_sudo, check_os
from fabdeb.tools import print_green, print_red


__all__ = ('install_exim4',)


# # # COMMANDS # # #


@task
def install_exim4():
    """
    Install email-server exim4, configure DKIM and generate DKIM-keys
    """
    check_sudo()
    check_os()
    if not confirm('Do you want install exim4?'):
        return
    print_green('INFO: Install exim4...')
    apt_install('exim4', noconfirm=True)
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
              '    Split configuration into small files: No\n'
              '    Root and postmaster mail recipient: <allow empty>\n')
    if confirm('Do you want install opendkim and setup dkim in exim4?'):
        apt_install('opendkim opendkim-tools', noconfirm=True)
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
        service_restart('exim4')
    print_green('INFO: Install exim4... OK')
