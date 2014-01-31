# coding=utf-8
from rest_framework import serializers

from rest_framework.fields import Field
from users.models import Org


class UghPublishCostSerializer(serializers.HyperlinkedModelSerializer):
    cost = Field(source='publish_cost')
    currency = serializers.RelatedField(source='currency')
    
    class Meta:
        model = Org
        fields = ('id', 'name', 'cost', 'currency' )
