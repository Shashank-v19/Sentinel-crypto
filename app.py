import os
import io
import numpy as np
from flask import Flask, request, jsonify, render_template
from PIL import Image
import onnxruntime as ort
from encryption import encrypt_image
from decryption import decrypt_image
from metrics import calculate_entropy, npcr, uaci
import uuid
import hashlib

app = Flask(__name__)

# Ensure static upload directories exist
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------------------------------------------------------------------
# ONNX Runtime — encoder model (layers 0-5 of the autoencoder)
# Output shape: (1, 8, 8, 64) → flattened to 4096-dim feature vector
# ---------------------------------------------------------------------------
print("Loading ONNX encoder model...")
_ONNX_PATH = os.path.join(app.root_path, "models", "encoder.onnx")
_session = ort.InferenceSession(_ONNX_PATH, providers=["CPUExecutionProvider"])
_input_name  = _session.get_inputs()[0].name
_output_name = _session.get_outputs()[0].name
print(f"  Input  : {_session.get_inputs()[0].shape}")
print(f"  Output : {_session.get_outputs()[0].shape}")
print("Model ready.")


def run_inference(image_norm_32x32):
    """
    Run ONNX encoder and return a flat 1-D float32 feature array.
    image_norm_32x32: numpy array shape (32, 32, 3), values in [0, 1].
    """
    input_data = np.expand_dims(image_norm_32x32, axis=0).astype(np.float32)
    output = _session.run([_output_name], {_input_name: input_data})[0][0]  # (8, 8, 64)
    return output.flatten()  # → 4096-dim feature vector


# ---------------------------------------------------------------------------
# Image helpers using Pillow (replaces OpenCV)
# ---------------------------------------------------------------------------
def decode_image(file_bytes):
    """Decode raw upload bytes → numpy array in BGR order (matches original cv2 behaviour)."""
    pil_img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    rgb = np.array(pil_img)
    return rgb[:, :, ::-1].copy()  # RGB → BGR


def save_image(numpy_bgr, path):
    """Save a numpy BGR uint8 array to disk as PNG."""
    rgb = numpy_bgr[:, :, ::-1].astype(np.uint8)
    Image.fromarray(rgb).save(path, format="PNG")


def resize_and_normalise(file_bytes, size=(32, 32)):
    """Return a (H, W, 3) float32 array in [0, 1] for model input."""
    pil_img = Image.open(io.BytesIO(file_bytes)).convert("RGB").resize(size)
    return np.array(pil_img, dtype=np.float32) / 255.0


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route('/')
def sender_page():
    return render_template('sender.html')


@app.route('/receiver')
def receiver_page():
    return render_template('receiver.html')


# API for encryption
@app.route('/api/encrypt', methods=['POST'])
def api_encrypt():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'})

    file = request.files['image']
    file_bytes = file.read()

    # Decode original high-resolution image (BGR numpy array)
    image = decode_image(file_bytes)

    # Extract encoder features from 32x32 normalised image
    image_norm = resize_and_normalise(file_bytes)
    features = run_inference(image_norm)  # shape (4096,)

    # Generate unique session ID / Cryptographic IV
    session_id = uuid.uuid4().hex

    # Encrypt the ORIGINAL high-resolution image
    encrypted = encrypt_image(image, features, session_id=session_id)

    # Save encrypted image
    enc_path = os.path.join(UPLOAD_FOLDER, f"{session_id}_encrypted.png")
    save_image(encrypted, enc_path)

    # Save original for NPCR/UACI reference
    orig_path = os.path.join(UPLOAD_FOLDER, f"{session_id}_original.png")
    save_image(image, orig_path)

    # Save features (simulated secure key exchange)
    np.save(os.path.join(UPLOAD_FOLDER, f"{session_id}_features.npy"), features)

    # Metrics
    entropy = calculate_entropy(encrypted)
    n = npcr(image, encrypted)
    u = uaci(image, encrypted)

    # Calculate x0 for frontend formula display
    x0_base = float(np.sum(features)) % 1.0
    h_val = int(hashlib.sha256(session_id.encode()).hexdigest()[:8], 16)
    x0_salt = h_val / 4294967295.0
    x0_final = (x0_base + x0_salt) % 1.0
    if x0_final <= 0 or x0_final >= 1:
        x0_final = 0.5

    return jsonify({
        'status': 'success',
        'encryptedUrl': f'/static/uploads/{session_id}_encrypted.png',
        'sessionId': session_id,
        'metrics': {
            'entropy': round(entropy, 4),
            'npcr': round(n, 4),
            'uaci': round(u, 4)
        },
        'formulaData': {
            'x0': round(x0_final, 8)
        }
    })


# API for decryption
@app.route('/api/decrypt', methods=['POST'])
def api_decrypt():
    if 'image' not in request.files:
        return jsonify({'error': 'No encrypted image uploaded'})

    sessionId = request.form.get('sessionId')
    if not sessionId:
        return jsonify({'error': 'No sessionId provided'})

    file = request.files['image']
    file_bytes = file.read()
    encrypted = decode_image(file_bytes)

    # Load features (the key)
    feat_path = os.path.join(UPLOAD_FOLDER, f"{sessionId}_features.npy")
    if not os.path.exists(feat_path):
        return jsonify({'error': 'Decryption key (features) missing for this session'})

    features = np.load(feat_path)

    # Decrypt
    decrypted = decrypt_image(encrypted, features, session_id=sessionId)

    # Save decrypted
    dec_path = os.path.join(UPLOAD_FOLDER, f"{sessionId}_decrypted.png")
    save_image(decrypted, dec_path)

    return jsonify({
        'status': 'success',
        'decryptedUrl': f'/static/uploads/{sessionId}_decrypted.png'
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)
