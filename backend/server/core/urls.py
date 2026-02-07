from django.urls import path
from .views import (
    submit_video,
    generate_quiz_view,
    get_lectures,
    get_transcript,
    generate_notes_view      # ✅ IMPORT DIRECTLY
)

urlpatterns = [
    path('lectures/', get_lectures),
    path('submit-video/', submit_video),
    path('generate-quiz/', generate_quiz_view),

    path('transcript/<str:video_id>/', get_transcript),

    # ✅ CORRECT
    path('generate-notes/', generate_notes_view),
]
