# -*- coding: utf-8 -*-

from rest_framework import serializers
from billing.models import Currency

class ArchCurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = ('id', 'name', 'short_name', 'code', 'rounding', 'icon', )

