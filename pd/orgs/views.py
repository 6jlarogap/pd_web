# Create your views here.

def get_user_org(user):
    try:
        return user.organization_set.all()[0]
    except IndexError:
        return None
