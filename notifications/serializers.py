from rest_framework import serializers
from notifications.models import PushSubscription, Notification


class PushSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PushSubscription
        fields = ["id", "fcm_token", "platform", "created_at"]
        read_only_fields = ["id", "created_at"]


class NotificationSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    body = serializers.SerializerMethodField()
    cta = serializers.SerializerMethodField()
    target = serializers.SerializerMethodField()
    additional_data = serializers.SerializerMethodField()
    channels = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "type",
            "channels",
            "category",
            "title",
            "body",
            "created_at",
            "is_read",
            "cta",
            "target",
            "additional_data",
        ]

    def get_channels(self, obj):
        template = self.context["template"]
        return template.get_channels()

    def get_title(self, obj):
        template = self.context["template"]
        return template.get_title()

    def get_category(self, obj):
        template = self.context["template"]
        return template.get_category()

    def get_body(self, obj):
        template = self.context["template"]
        return template.get_body()

    def get_cta(self, obj):
        template = self.context["template"]
        return template.get_cta()

    def get_target(self, obj):
        template = self.context["template"]
        return template.get_target_url()

    def get_additional_data(self, obj):
        """Return any additional template-specific data"""
        return {}
