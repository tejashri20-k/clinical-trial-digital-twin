from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response

from . import blockchain
from .hash_utils import compute_record_hash
from .models import ClinicalTrial, ResearchCenter, Participant, ClinicalData
from .serializers import (
    ClinicalTrialSerializer,
    ResearchCenterSerializer,
    ParticipantSerializer,
    ClinicalDataSerializer
)

VERIFIED = "VERIFIED"
TAMPERED = "TAMPERED"
NOT_ON_CHAIN = "NOT_ON_CHAIN"


def check_record(record):
    """Compare a record's current database hash with its blockchain hash.

    VERIFIED     - the two hashes match
    TAMPERED     - a hash is on the blockchain but it differs from the data
    NOT_ON_CHAIN - no hash has been stored on the blockchain for it (yet)
    """
    database_hash = compute_record_hash(record)
    blockchain_hash = blockchain.get_onchain_hash(record.record_id)

    if not blockchain_hash:
        record_status = NOT_ON_CHAIN
    elif blockchain_hash == database_hash:
        record_status = VERIFIED
    else:
        record_status = TAMPERED

    return {
        "record_id": record.record_id,
        "database_hash": database_hash,
        "blockchain_hash": blockchain_hash,
        "status": record_status,
    }


def blockchain_unavailable(exc):
    return Response(
        {"detail": f"Could not reach the blockchain: {exc}"},
        status=status.HTTP_503_SERVICE_UNAVAILABLE,
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
    queryset = ClinicalData.objects.select_related("participant").order_by("id")
    serializer_class = ClinicalDataSerializer

    def create(self, request, *args, **kwargs):
        """Save the record, then store its hash on the blockchain.

        The record is always saved. If the blockchain write fails, the
        response still succeeds but carries a `chain_error` message, and the
        record shows as NOT_ON_CHAIN until its hash is stored.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        record = serializer.save()

        result = dict(serializer.data)

        try:
            result["tx_hash"] = blockchain.store_hash_on_blockchain(
                record.record_id,
                compute_record_hash(record),
            )
            result["chain_error"] = None
        except Exception as exc:
            result["tx_hash"] = None
            result["chain_error"] = str(exc)

        return Response(result, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def verify_integrity(self, request, pk=None):
        record = self.get_object()

        try:
            return Response(check_record(record))
        except Exception as exc:
            return blockchain_unavailable(exc)

    @action(detail=False, methods=["get"])
    def verify_all(self, request):
        """Every record with its data, both hashes and its integrity status."""
        rows = []

        for record in self.get_queryset():
            row = {
                "id": record.id,
                "record_id": record.record_id,
                "participant": record.participant.participant_id,
                "blood_pressure": record.blood_pressure,
                "blood_glucose": record.blood_glucose,
                "treatment": record.treatment,
            }

            try:
                row.update(check_record(record))
            except Exception as exc:
                row.update({
                    "database_hash": compute_record_hash(record),
                    "blockchain_hash": "",
                    "status": "ERROR",
                    "error": str(exc),
                })

            rows.append(row)

        return Response(rows)

    @action(detail=True, methods=["post"])
    def anchor(self, request, pk=None):
        """Store a record's hash on the blockchain.

        Only allowed while the record has NO hash on the blockchain yet, so
        this can never be used to overwrite (and hide) a tampered record.
        """
        record = self.get_object()

        try:
            existing = blockchain.get_onchain_hash(record.record_id)
        except Exception as exc:
            return blockchain_unavailable(exc)

        if existing:
            return Response(
                {"detail": "This record already has a hash on the "
                           "blockchain, so it cannot be stored again."},
                status=status.HTTP_409_CONFLICT,
            )

        try:
            tx_hash = blockchain.store_hash_on_blockchain(
                record.record_id,
                compute_record_hash(record),
            )
        except Exception as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({"record_id": record.record_id, "tx_hash": tx_hash})


@api_view(["GET"])
def digital_twin(request, trial_id):
    trial = get_object_or_404(ClinicalTrial, id=trial_id)

    participants = Participant.objects.filter(trial=trial)
    centers = ResearchCenter.objects.all()
    clinical_data = ClinicalData.objects.filter(trial=trial)

    counts = {VERIFIED: 0, TAMPERED: 0, NOT_ON_CHAIN: 0}

    for record in clinical_data:
        try:
            counts[check_record(record)["status"]] += 1
        except Exception:
            counts[NOT_ON_CHAIN] += 1

    return Response({
        "trial_id": trial.trial_id,
        "trial_name": trial.trial_name,
        "status": trial.status,
        "participants": participants.count(),
        "research_centers": centers.count(),
        "clinical_records": clinical_data.count(),
        "verified_records": counts[VERIFIED],
        "tampered_records": counts[TAMPERED],
        "pending_records": counts[NOT_ON_CHAIN],
    })