from django.contrib.sites.models import Site
from django.shortcuts import redirect, render

from organizations.backends.defaults import RegistrationBackend
from organizations.backends.forms import OrganizationRegistrationForm
from organizations.utils import create_organization


class OrgRegBackend(RegistrationBackend):
    def create_view(self, request):
        """
        Initiates the organization and user account creation process
        """
        if request.user.is_authenticated():
            return redirect("organization_add")
        form = OrganizationRegistrationForm(request.POST or None)
        if form.is_valid():
            try:
                self.user_model.objects.get(email=form.cleaned_data['email'])
            except self.user_model.DoesNotExist:
                user = self.user_model.objects.create(username=self.get_username(),
                                                      email=form.cleaned_data['email'],
                                                      password=self.user_model.objects.make_random_password())
                user.is_active = False
                user.save()
                self.send_activation(user, sender=None, site=Site.objects.get_current())
            else:
                return redirect("organization_add")
            organization = create_organization(user, form.cleaned_data['name'], form.cleaned_data['slug'], is_active=False)
            return render(request, 'organizations/register_success.html', {'user': user, 'organization': organization})
        return render(request, 'organizations/register_form.html', {'form': form})

