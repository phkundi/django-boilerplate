from core.models import Country, EntityThirdPartyId, DataProvider
from rest_framework import serializers


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ("name", "ioc", "iso", "icon")


class EntityThirdPartyIdSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntityThirdPartyId
        fields = ("provider", "value")


class DataProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataProvider
        fields = ("name", "url", "logo", "id")
