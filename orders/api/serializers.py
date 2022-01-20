from rest_framework import serializers

from api.models import Shop


class UploadSerializer(serializers.ModelSerializer):

    class Meta:
        model = Shop
        fields = ['name', 'url', 'filename']

