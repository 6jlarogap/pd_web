#!/usr/bin/env python
import os
import sys

activate_this = os.path.join(os.path.dirname(__file__), 'ENV', 'bin', 'activate_this.py')
if os.path.exists(activate_this):
    print 'Activating', activate_this
    execfile(activate_this, dict(__file__=activate_this))
else:
    activate_this = os.path.join(os.path.dirname(__file__), '..', 'ENV', 'bin', 'activate_this.py')
    if os.path.exists(activate_this):
        print 'Activating', activate_this
        execfile(activate_this, dict(__file__=activate_this))

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pd.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
