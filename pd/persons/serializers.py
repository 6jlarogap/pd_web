from django.contrib.auth.models import Group, Permission
from rest_framework import serializers


from persons.models import AlivePerson, DeadPerson

from rest_api.fields import UnclearDateFieldSerializer


class AlivePersonSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = AlivePerson
        fields = ('id', 'first_name', 'last_name', 'middle_name', 'phones')


class DeadPersonSerializer(serializers.HyperlinkedModelSerializer):
    birth_date = UnclearDateFieldSerializer()
    death_date = UnclearDateFieldSerializer()
    class Meta:
        model = DeadPerson
        fields = ('id', 'first_name', 'last_name', 'middle_name', 'birth_date', 'death_date' )


