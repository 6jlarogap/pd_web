import datetime
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import ugettext_lazy as _
from pd.models import UnclearDateModelField

import os
import pytils

from persons.models import DeadPerson
from reports.models import Report
from users.models import Org, Profile, Dover
from logs.models import Log

from django.db import models
from burials.models import Cemetery, Area, Place, Burial
