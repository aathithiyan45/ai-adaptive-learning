from django.urls import path
from .views import (
    submit_video,
    generate_quiz_view,
    get_lectures,
    get_transcript        # 🔥 ADD THIS
)

urlpatterns = [
    path('lectures/', get_lectures),
    path('submit-video/', submit_video),
    path('generate-quiz/', generate_quiz_view),

    # 🔥 MISSING API
    path('transcript/<str:video_id>/', get_transcript),
]
