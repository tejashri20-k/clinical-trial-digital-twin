from datetime import date, datetime, timezone

from django.core.management.base import BaseCommand
from trials.models import (
    ClinicalTrial,
    ResearchCenter,
    Participant,
    ClinicalData,
)


class Command(BaseCommand):
    help = "Create demo clinical trial data if it does not exist"

    def handle(self, *args, **options):
        trial, _ = ClinicalTrial.objects.get_or_create(
            trial_id="TRIAL001",
            defaults={
                "trial_name": "Diabetes Clinical Trial",
                "description": "Demo clinical trial for integrity monitoring",
                "start_date": date(2026, 1, 1),
                "status": "Active",
            },
        )

        center, _ = ResearchCenter.objects.get_or_create(
            center_id="CENTER001",
            defaults={
                "center_name": "VIT Clinical Research Center",
                "location": "Vellore",
            },
        )

        participant, _ = Participant.objects.get_or_create(
            participant_id="P001",
            defaults={
                "trial": trial,
                "center": center,
                "status": "Active",
            },
        )

        records = [
            ("REC001", "120/80", 95, "TREATMENT A"),
            ("REC002", "118/78", 102, "TREATMENT A"),
            ("REC003", "122/82", 110, "TREATMENT B"),
            ("REC004", "120/80", 105, "TREATMENT A"),
        ]

        for index, (record_id, bp, glucose, treatment) in enumerate(records):
            ClinicalData.objects.get_or_create(
                record_id=record_id,
                defaults={
                    "participant": participant,
                    "trial": trial,
                    "blood_pressure": bp,
                    "blood_glucose": glucose,
                    "treatment": treatment,
                    "timestamp": datetime(
                        2026, 1, 1, 10 + index, 0,
                        tzinfo=timezone.utc,
                    ),
                },
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Demo trial data created or already present."
            )
        )