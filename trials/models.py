from django.db import models
from .hash_utils import generate_hash

# Create your models here.
class ClinicalTrial(models.Model):
    trial_id = models.CharField(max_length=20, unique=True)
    trial_name = models.CharField(max_length=200)
    description = models.TextField()
    start_date = models.DateField()
    status = models.CharField(max_length=50, default="Active")

    def __str__(self):
        return self.trial_name


class ResearchCenter(models.Model):
    center_id = models.CharField(max_length=20, unique=True)
    center_name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)

    def __str__(self):
        return self.center_name

class Participant(models.Model):
    participant_id = models.CharField(max_length=20, unique=True)
    trial = models.ForeignKey(ClinicalTrial, on_delete=models.CASCADE)
    center = models.ForeignKey(ResearchCenter, on_delete=models.CASCADE)
    status = models.CharField(max_length=50, default="Active")

    def __str__(self):
        return self.participant_id

class ClinicalData(models.Model):
    record_id = models.CharField(max_length=20, unique=True)
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
    trial = models.ForeignKey(ClinicalTrial, on_delete=models.CASCADE)
    blood_pressure = models.CharField(max_length=20)
    blood_glucose = models.FloatField()
    treatment = models.CharField(max_length=200)
    timestamp = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    data_hash = models.CharField(max_length=64, blank=True)

    def save(self, *args, **kwargs):
        data = (
            f"{self.record_id}|"
            f"{self.blood_pressure}|"
            f"{self.blood_glucose:g}|"
            f"{self.treatment}"
        )

        self.data_hash = generate_hash(data)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.record_id