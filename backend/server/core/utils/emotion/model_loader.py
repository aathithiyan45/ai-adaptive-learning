import tensorflow as tf
import os

MODEL_PATHS = [
    "checkpoints/mobilenet_aug/Epoch_500_model.hp5",
    "checkpoints/scratch_aug/Epoch_500_model.hp5",
    "checkpoints/Epoch_90_model.hp5",
]

model = None

for path in MODEL_PATHS:
    if os.path.exists(path):
        model = tf.keras.models.load_model(path, compile=False)
        print("✅ Emotion model loaded:", path)
        break

if model is None:
    raise RuntimeError("❌ Emotion model not found")
