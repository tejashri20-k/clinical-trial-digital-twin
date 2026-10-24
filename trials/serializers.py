from rest_framework import serializers
from .models import ClinicalTrial, ResearchCenter, Participant, ClinicalData


class ClinicalTrialSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicalTrial
        fields = '__all__'


class ResearchCenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResearchCenter
        fields = '__all__'


class ParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Participant
        fields = '__all__'


class ClinicalDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicalData
        fields = '__all__'