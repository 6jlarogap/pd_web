#!/bin/env python

# sudo easy_install fabric

from fabric.api import *

env.hosts = ['youmemory.org']

def sshagent_run(cmd):
    """
    Helper function.
    Runs a command with SSH agent forwarding enabled.

    Note:: Fabric (and paramiko) can't forward your SSH agent.
    This helper uses your system's ssh to do so.
    """

    for h in env.hosts:
        try:
            # catch the port number to pass to ssh
            host, port = h.split(':')
            try:
                # catch username too
                user, real_host = host.split('@')
                cmd_line = 'ssh -p %s -A %s -l %s "%s"' % (port, real_host, user, cmd)
            except ValueError:
                cmd_line = 'ssh -p %s -A %s "%s"' % (port, host, cmd)
        except ValueError:
            cmd_line = 'ssh -A %s "%s"' % (h, cmd)
        print 'Running', cmd_line
        local(cmd_line)

def deploy_docs():
    local('git pull')
    local('git push')

    try:
        local('cd wiki && git commit -a -m "docs update"')
    except:
        pass
    local('cd wiki && git pull')
    local('cd wiki && git push')

    local('ssh-add')
    sshagent_run('cd /home/www-data/django/pd_web/ && sudo -u www-data git pull')
    run('sudo /etc/init.d/apache2 reload')

def deploy():
    local('git push')

    local('ssh-add')
    sshagent_run('cd /home/www-data/django/pd_web/ && sudo -u www-data git pull')
    run('sudo /etc/init.d/apache2 reload')

def deploy_full():
    local('git pull')
    local('git push')

    local('ssh-add')
    sshagent_run('cd /home/www-data/django/pd_web/ && sudo -u www-data git pull')

    run('cd /home/www-data/django/pd_web/pd/ && ../ENV/bin/python ./manage.py migrate --noinput')
    run('cd /home/www-data/django/pd_web/pd/ && ../ENV/bin/python ./manage.py collectstatic --noinput')
    run('sudo /etc/init.d/apache2 reload')

