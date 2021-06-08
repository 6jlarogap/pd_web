from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from django.db import models

class Report(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    user = models.ForeignKey('auth.User', editable=False, on_delete=models.CASCADE)
    dt = models.DateTimeField(auto_now_add=True)

    description = models.TextField(_("Название отчета"))
    html = models.TextField(editable=False)

def make_report(user, msg, obj, template, context):
    ct = ContentType.objects.get_for_model(obj)
    return Report.objects.create(
        user=user,
        description=msg,
        content_type=ct,
        object_id=obj.pk,
        html=render_to_string(template, context),
    )

