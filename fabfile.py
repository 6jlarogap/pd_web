#!/bin/env python

# sudo easy_install fabric

from fabric.api import *

env.hosts = ['youmemory.org']

def deploy():
    local('git push')
    with cd('/home/www-data/django/pd_web/'):
        run('sudo -u www-data git pull && sudo /etc/init.d/apache2 reload')
