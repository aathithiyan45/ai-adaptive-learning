from django.urls import path
from .views import (
    get_lectures,
    submit_video,
    get_transcript,
    generate_quiz_view,
    generate_notes_view,
    chatbot_view,
)

urlpatterns = [
    path("lectures/", get_lectures),
    path("submit-video/", submit_video),
    path("transcript/<str:video_id>/", get_transcript),
    path("generate-quiz/", generate_quiz_view),
    path("generate-notes/", generate_notes_view),
    path("chatbot/", chatbot_view),
]
