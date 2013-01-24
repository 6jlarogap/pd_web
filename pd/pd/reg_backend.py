from django.contrib.sites.models import Site, RequestSite
from django.shortcuts import redirect, render

from registration.backends.default import DefaultBackend

from pd.forms import OrgRegForm
from registration.models import RegistrationProfile
from registration.signals import user_registered


class OrgRegBackend(DefaultBackend):
    """
    Registration backend for creating an Organization of provided type
    """
    def get_form_class(self, request):
        return OrgRegForm

    def register(self, request, **kwargs):
        form_class = self.get_form_class(request)
        form = form_class(data=request.POST, files=request.FILES)
        org = form.save(commit=False)

        username, email, password = kwargs['username'], kwargs['email'], kwargs['password1']
        if Site._meta.installed:
            site = Site.objects.get_current()
        else:
            site = RequestSite(request)
        new_user = RegistrationProfile.objects.create_inactive_user(username, email, password, site)
        user_registered.send(sender=self.__class__, user=new_user, request=request)

        org.creator = new_user
        org.save()

        if org.is_loru():
            new_user.is_staff = True
            new_user.add_perm('orgs:add_organization')
            new_user.add_perm('persons:add_person')

        return new_user
