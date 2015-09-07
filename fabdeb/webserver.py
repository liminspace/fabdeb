from fabric.contrib.files import sed
from fabric.contrib.console import confirm
from fabric.decorators import task
from fabric.operations import prompt
from fabdeb.apt import apt_install, set_apt_repositories, apt_update
from fabdeb.os import check_sudo
from fabdeb.os import check_os
from fabdeb.tools import print_green


__all__ = ('install_nginx',)


NGINX_REPOSITORIES = {
    'Debian GNU/Linux 8': {
        ('8.0', '8.1', '8.2'): (
            'deb http://nginx.org/packages/debian/ jessie nginx\n'
            'deb-src http://nginx.org/packages/debian/ jessie nginx\n'
        ),
    },
}


NGINX_REPOS_INSTALL_KEYS_COMMANDS = {
    'Debian GNU/Linux 8': {
        ('8.0', '8.1', '8.2'): (
            'wget -q -O - http://nginx.org/keys/nginx_signing.key | apt-key add -',
        ),
    },
}


# # # COMMANDS # # #


@task
def install_nginx():
    """
    Install Nginx web-server
    """
    check_sudo()
    check_os()
    if not confirm('Do you want to install nginx?'):
        return
    print_green('INFO: Install nginx...')
    set_apt_repositories(NGINX_REPOSITORIES, NGINX_REPOS_INSTALL_KEYS_COMMANDS, subconf_name='nginx')
    apt_update()
    apt_install('nginx', noconfirm=True)
    user = prompt('Set user to nginx', default='www-data', validate='[\w\-]+')
    workers = prompt('Set worker_processes', default='1', validate='\d+')
    cmbs = prompt('Set client_max_body_size (MB)', default='32', validate='\d+')
    gzl = prompt('Set gzip_comp_level (set 0 to disable gzip)', default='1', validate='\d+')
    cfn = '/etc/nginx/nginx.conf'
    sed(cfn, r'user\s+nginx;', r'user  {};'.format(user), use_sudo=True)
    sed(cfn, r'worker_processes\s+[0-9]+;', r'worker_processes  {};'.format(workers), use_sudo=True, backup='')
    sed(cfn, r'http \{', (r'http \{\n\n'
                          r'    server_names_hash_bucket_size  64;\n'
                          r'    client_max_body_size           {cmbs}m;\n\n').replace('{cmbs}', cmbs),
        use_sudo=True, backup='')
    if gzl != '0':
        sed(cfn, r'\s+#\s*gzip  on;',
            (r'    gzip             on;\n'
             r'    gzip_proxied     any;\n'
             r'    gzip_comp_level  {gzl};\n'
             r'    gzip_min_length  1000;\n'
             r'    gzip_proxied     expired no-cache no-store private auth;\n'
             r'    gzip_types       text/plain text/javascript text/xml text/css application/x-javascript '
             r'application/javascript application/xml image/svg+xml;\n'
             r'    gzip_disable     "msie6";\n'
             r'    gzip_vary        on;\n').format(gzl=gzl), use_sudo=True, backup='')
    print_green('INFO: Install nginx... OK')
