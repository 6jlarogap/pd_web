#! /usr/bin/env python
#
# coding=utf-8

# check_disk_space.py
# -------------------

import subprocess
from smtplib import SMTP

from check_disk_space_conf import *

def email_(partition, usage, size, used, avail):
    # --rfc-2822
    datestr = subprocess.check_output(
        'date --rfc-2822',
        stderr=subprocess.STDOUT,
        shell=True
    ).strip()

    smtp = SMTP()
    host = CDS_EMAIL_HOST if CDS_EMAIL_HOST else 'localhost'
    port = CDS_EMAIL_PORT if CDS_EMAIL_PORT else 25
    smtp.connect(host, port)

    username = CDS_EMAIL_HOST_USER if CDS_EMAIL_HOST_USER else None
    password = CDS_EMAIL_HOST_PASSWORD if CDS_EMAIL_HOST_PASSWORD else None
    if username:
        smtp.login(username, password)

    from_addr = CDS_EMAIL_FROM
    to_addr = "\n".join([ "To: %s" % addr for addr in CDS_MANAGERS ])

    subj = "Disk usage threshold is reached at %s" % CDS_HOSTNAME

    message_text = "\nPartition %s.\n" \
                   "Disk usage: %s%%, more than %s%%\n\n" \
                   "Size:       %s\n" \
                   "Used:       %s\n" \
                   "Available:  %s\n" % \
                    (partition, usage, CDS_THRESHOLD,
                     size, used, avail)

    msg = "From: %s\n%s\nSubject: %s\nDate: %s\n\n%s" \
            % ( from_addr, to_addr, subj, datestr, message_text )

    smtp.sendmail(from_addr, to_addr, msg)
    smtp.quit()

for partition in CDS_PARTITIONS:
    outp = subprocess.check_output(
        r"df -H | egrep ' %s'$" % partition,
        stderr=subprocess.STDOUT,
        shell=True
    )
    print "Checking %s" % partition
    splitted = outp.split()
    usage = int(splitted[4].rstrip('%'))
    size = splitted[1]
    avail = splitted[2]
    used = splitted[3]
    if usage >= CDS_THRESHOLD:
        print " - reached the threshold! Sending mail"
        email_(partition, usage, size, used, avail)
    else:
        print " - OK: not more than the threshold yet"