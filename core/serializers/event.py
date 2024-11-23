from rest_framework import serializers
from .item import ItemSerializer
from .user import UserSerializer


class EventSerializer(serializers.Serializer):
    user = UserSerializer()
    item = ItemSerializer()
    event_type = serializers.CharField()
    timestamp = serializers.DateTimeField()  # This will validate the ISO 8601 format

    def create(self, validated_data):
        return validated_data
