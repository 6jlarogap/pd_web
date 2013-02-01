from django import forms

from burials.models import BurialRequest, Cemetery
from django.db.models.query_utils import Q


class BurialRequestCreateForm(forms.ModelForm):
    class Meta:
        model = BurialRequest
        exclude = ['loru', ]

    def __init__(self, request, *args, **kwargs):
        super(BurialRequestCreateForm, self).__init__(*args, **kwargs)
        self.fields['cemetery'].queryset = Cemetery.objects.filter(
            Q(ugh__isnull=True) | Q(ugh__loru_list__loru=request.user.profile.org)
        ).distinct()

class CemeteryForm(forms.ModelForm):
    class Meta:
        model = Cemetery
        exclude = ['ugh', ]