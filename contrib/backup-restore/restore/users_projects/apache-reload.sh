#! /bin/bash
sudo service apache2 stop 2> /dev/null
sudo rm -f /var/run/apache2.pid 2> /dev/null
sudo killall apache2 2> /dev/null
sleep 5
sudo service apache2 restart
