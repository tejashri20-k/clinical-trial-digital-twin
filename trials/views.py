from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ClinicalTrial, ResearchCenter, Participant, ClinicalData
from .serializers import (
    ClinicalTrialSerializer,
    ResearchCenterSerializer,
    ParticipantSerializer,
    ClinicalDataSerializer
)


class ClinicalTrialViewSet(viewsets.ModelViewSet):
    queryset = ClinicalTrial.objects.all()
    serializer_class = ClinicalTrialSerializer


class ResearchCenterViewSet(viewsets.ModelViewSet):
    queryset = ResearchCenter.objects.all()
    serializer_class = ResearchCenterSerializer


class ParticipantViewSet(viewsets.ModelViewSet):
    queryset = Participant.objects.all()
    serializer_class = ParticipantSerializer


class ClinicalDataViewSet(viewsets.ModelViewSet):
    queryset = ClinicalData.objects.all()
    serializer_class = ClinicalDataSerializer

    def perform_create(self, serializer):
        clinical_data = serializer.save()

        from .blockchain import store_hash_on_blockchain

        store_hash_on_blockchain(
            clinical_data.record_id,
            clinical_data.data_hash
        )
    @action(detail=True, methods=['get'])    
    def verify_integrity(self, request, pk=None):
        clinical_data = self.get_object()

        from .blockchain import contract

        blockchain_hash = contract.functions.getHash(
            clinical_data.record_id
        ).call()

        from .hash_utils import generate_hash

        current_data = (
            f"{clinical_data.record_id}|"
            f"{clinical_data.blood_pressure}|"
            f"{clinical_data.blood_glucose:g}|"
            f"{clinical_data.treatment}"
        )
        print("DATA BEING HASHED:", repr(current_data))

        print("DATABASE HASH:", generate_hash(current_data))

        database_hash = generate_hash(current_data)

        if database_hash == blockchain_hash:
            status = "VERIFIED"
        else:
            status = "TAMPERED"

        return Response({
            "record_id": clinical_data.record_id,
            "database_hash": database_hash,
            "blockchain_hash": blockchain_hash,
            "status": status
        })  
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import ClinicalTrial, Participant, ResearchCenter, ClinicalData

@api_view(['GET'])
def digital_twin(request, trial_id):

    trial = ClinicalTrial.objects.get(id=trial_id)

    participants = Participant.objects.filter(trial=trial)
    centers = ResearchCenter.objects.all()
    clinical_data = ClinicalData.objects.filter(trial=trial)

    verified_count = 0
    tampered_count = 0

    from .blockchain import contract
    from .hash_utils import generate_hash

    for record in clinical_data:

        current_data = (
            f"{record.record_id}|"
            f"{record.blood_pressure}|"
            f"{record.blood_glucose:g}|"
            f"{record.treatment}"
        )

        current_hash = generate_hash(current_data)

        blockchain_hash = contract.functions.getHash(
            record.record_id
        ).call()

        if current_hash == blockchain_hash:
            verified_count += 1
        else:
            tampered_count += 1

    return Response({
        "trial_id": trial.trial_id,
        "trial_name": trial.trial_name,
        "status": trial.status,
        "participants": participants.count(),
        "research_centers": centers.count(),
        "clinical_records": clinical_data.count(),
        "verified_records": verified_count,
        "tampered_records": tampered_count
    })      