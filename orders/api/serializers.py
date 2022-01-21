from rest_framework import serializers

from api.models import Shop


class UploadSerializer(serializers.ModelSerializer):
    filename = serializers.FileField(max_length=None, use_url=True)

    class Meta:
        model = Shop
        fields = ['name', 'url', 'filename']