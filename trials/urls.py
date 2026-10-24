from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ClinicalTrialViewSet,
    ResearchCenterViewSet,
    ParticipantViewSet,
    ClinicalDataViewSet,
    digital_twin
)
router = DefaultRouter()

router.register('trials', ClinicalTrialViewSet)
router.register('centers', ResearchCenterViewSet)
router.register('participants', ParticipantViewSet)
router.register('clinical-data', ClinicalDataViewSet, basename='clinical-data')

urlpatterns = [
    path('', include(router.urls)),
    path('digital-twin/<int:trial_id>/', digital_twin),
]