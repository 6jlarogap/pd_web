from django import forms

from burials.models import BurialRequest, Cemetery
from django.db.models.query_utils import Q


class BurialRequestCreateForm(forms.ModelForm):
    class Meta:
        model = BurialRequest
        exclude = ['number']
        
    def __init__(self, request, *args, **kwargs):
        super(BurialRequestCreateForm, self).__init__(*args, **kwargs)
        self.fields['cemetery'].queryset = Cemetery.objects.filter(
            Q(creator__isnull=True) | Q(creator__profile__org__loru_list__loru=request.user.profile.org)
        ).distinct()