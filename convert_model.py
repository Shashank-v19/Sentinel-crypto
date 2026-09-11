"""
One-time model conversion script.
Run this locally ONCE before pushing to GitHub:
    python convert_model.py

Requires tensorflow to be installed locally (not on Vercel).
"""
import tensorflow as tf
import os

H5_PATH = os.path.join("models", "autoencoder.h5")
TFLITE_PATH = os.path.join("models", "model.tflite")

print(f"Loading model from: {H5_PATH}")
model = tf.keras.models.load_model(H5_PATH, compile=False)

# Build encoder-only model from layers 0-5 (conv+pool layers before upsampling)
# Input  -> Conv2D -> MaxPool -> Conv2D -> MaxPool -> Conv2D  (encoder bottleneck)
# Layer indices: InputLayer(0), Conv2D(1), MaxPool(2), Conv2D(3), MaxPool(4), Conv2D(5)
inp = model.input
encoder_out = model.layers[5].output  # bottleneck feature map
encoder_model = tf.keras.Model(inputs=inp, outputs=encoder_out)
print(f"Encoder input  shape: {encoder_model.input_shape}")
print(f"Encoder output shape: {encoder_model.output_shape}")

print("\nConverting encoder to TFLite (no quantization to ensure compatibility)...")
converter = tf.lite.TFLiteConverter.from_keras_model(encoder_model)
# No optimizations — avoids tf.Conv2D quantization issue
tflite_model = converter.convert()

os.makedirs("models", exist_ok=True)
with open(TFLITE_PATH, "wb") as f:
    f.write(tflite_model)

size_kb = os.path.getsize(TFLITE_PATH) / 1024
print(f"\n✅ TFLite model saved to: {TFLITE_PATH}")
print(f"   Size: {size_kb:.1f} KB")
print("\nNow commit models/model.tflite and push to GitHub.")

