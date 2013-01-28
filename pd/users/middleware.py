from users.models import Profile


class ProfileMiddleware():
    def process_request(self, request):
        if request.user.is_authenticated():
            try:
                request.user.profile
            except Profile.DoesNotExist:
                Profile.objects.create(user=request.user, type=Profile.PROFILE_USER)
