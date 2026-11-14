from django.urls import path
from .views import QualityAssessmentView

urlpatterns = [
    path('quality-assessment/', QualityAssessmentView.as_view(), name='ai-quality-assessment'),
]
