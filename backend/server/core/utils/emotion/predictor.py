import cv2
import numpy as np
from .model_loader import model

LABELS = ["Bored", "Engaged", "Confused", "Frustrated"]

face_cascade = cv2.CascadeClassifier(
    "core/utils/emotion/haarcascade_frontalface_default.xml"
)

def predict_emotion(image_bgr):
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)

    if len(faces) == 0:
        return {"emotion": "No Face", "confidence": 0.0}

    x, y, w, h = max(faces, key=lambda f: f[2]*f[3])
    face = image_bgr[y:y+h, x:x+w]
    face = cv2.resize(face, (224, 224))
    face = face[..., ::-1]
    face = np.expand_dims(face, axis=0)

    preds = model.predict(face, verbose=0)[0]

    emotion = LABELS[np.argmax(preds)]
    confidence = float(np.max(preds))

    return {
        "emotion": emotion,
        "confidence": confidence
    }
