from .models import Note
from rest_framework import serializers

class SerializerNote(serializers.ModelSerializer):
    class Meta:
        model=Note
        fields='__all__'
        read_only_fields=['user']

