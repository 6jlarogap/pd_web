from django.contrib.auth.models import Group, Permission
from rest_framework import serializers
from rest_framework.fields import Field

from rest_api.fields import HyperlinkedFileField
from orders.models import ProductCategory


class ProductCategorySerializer(serializers.HyperlinkedModelSerializer):
    icon = HyperlinkedFileField()
    
    class Meta:
        model = ProductCategory
        fields = ('id', 'name', 'icon', )


#class DeadPersonSerializer(serializers.HyperlinkedModelSerializer):
    #birth_date = UnclearDateFieldSerializer()
    #death_date = UnclearDateFieldSerializer()
    #class Meta:
        #model = DeadPerson
        #fields = ('id', 'first_name', 'last_name', 'middle_name', 'birth_date', 'death_date')

