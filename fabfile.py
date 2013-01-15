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
                local('ssh -p %s -A %s -l %s "%s"' % (port, real_host, user, cmd))
            except ValueError:
                local('ssh -p %s -A %s "%s"' % (port, host, cmd))
        except ValueError:
            local('ssh -A %s "%s"' % (h, cmd))

def deploy():
    local('git pull')
    local('git push')

    local('cd wiki && git commit -a -m "docs update"')
    local('cd wiki && git pull')
    local('cd wiki && git push')

    local('ssh-add')
    sshagent_run('cd /home/www-data/django/pd_web/ && sudo -u www-data git pull')
    run('sudo /etc/init.d/apache2 reload')
