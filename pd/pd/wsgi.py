"""
WSGI config for pd project.

This module contains the WSGI application used by Django's development server
and any production WSGI deployments. It should expose a module-level variable
named ``application``. Django's ``runserver`` and ``runfcgi`` commands discover
this application via the ``WSGI_APPLICATION`` setting.

Usually you will have the standard Django WSGI application here, but it also
might make sense to replace the whole Django WSGI application with a custom one
that later delegates to the Django one. For example, you could introduce WSGI
middleware here, or combine a Django application with an application of another
framework.

"""
import os
import sys

# An old python bug concerning multi-threading and strptime. Refer to
# a workaround: https://modwsgi.readthedocs.org/en/latest/application-issues/index.html
# ...
# The only work around for the problem is to ensure that all module imports
# related to modules on which the PyImport_ImportModuleNoBlock() function
# is used be done explicitly or indirectly when the WSGI script file is loaded.
# Thus, to get around the specific case above, add the following into the WSGI script file:
# ...
import _strptime

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pd.settings")

activate_this = os.path.join(os.path.dirname(__file__), '..', '..', 'ENV', 'bin', 'activate_this.py')
if os.path.exists(activate_this):
    with open(activate_this) as acivate_this_file:
        exec(compile(acivate_this_file.read(), activate_this, 'exec'), dict(__file__=activate_this))

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# This application object is used by any WSGI server configured to use this
# file. This includes Django's development server, if the WSGI_APPLICATION
# setting points here.
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# Apply WSGI middleware here.
# from helloworld.wsgi import HelloWorldApplication
# application = HelloWorldApplication(application)
