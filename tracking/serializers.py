from rest_framework import serializers
from tracking.events import ALL_EVENTS


class TrackingEventSerializer(serializers.Serializer):
    event = serializers.CharField(max_length=100)
    label = serializers.CharField(max_length=200, required=False, allow_blank=True)
    value = serializers.IntegerField(required=False, allow_null=True)
    session_id = serializers.CharField(max_length=100, required=False, allow_blank=True)
    properties = serializers.JSONField(required=False, default=dict)

    def validate_event(self, value):
        """Validate that the event exists in our defined events"""
        if value not in ALL_EVENTS:
            raise serializers.ValidationError(
                f"Unknown event '{value}'. Valid events: {sorted(list(ALL_EVENTS))}"
            )
        return value

    def validate_properties(self, value):
        """Ensure properties is a dictionary"""
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise serializers.ValidationError("Properties must be a JSON object")
        return value
