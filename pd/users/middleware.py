# coding=utf-8
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _

from users.models import Profile


class ProfileMiddleware():
    def process_request(self, request):
        if request.user.is_authenticated():
            try:
                request.user.profile
            except Profile.DoesNotExist:
                Profile.objects.create(user=request.user)

            if not request.user.profile.org and request.path != reverse('profile') and not request.path.startswith('/admin/'):
                messages.error(request, _(u"Пожалуйста, для продолжения работы создайте организацию"))
                return redirect('profile')
