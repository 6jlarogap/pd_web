# -*- coding: utf-8 -*-

from rest_framework import serializers
from pd.models import Files

class ArchFilesSerializer(serializers.ModelSerializer):
    creator_id = serializers.Field('creator.id')

    class Meta:
        model = Files
        fields = ('id', 'bfile', 'comment', 'original_name', 'comment', 'creator_id', 'date_of_creation', )
