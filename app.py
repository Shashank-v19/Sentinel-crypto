import os
import io
import numpy as np
from flask import Flask, request, jsonify, render_template, send_from_directory
from PIL import Image
import onnxruntime as ort
from encryption import encrypt_image
from decryption import decrypt_image
from metrics import calculate_entropy, npcr, uaci
import uuid
import hashlib

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Vercel serverless: filesystem is read-only except /tmp
# All user-generated files (uploads, features) go to /tmp
# ---------------------------------------------------------------------------
UPLOAD_FOLDER = '/tmp/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------------------------------------------------------------------
# ONNX Runtime — encoder model
# Output shape: (1, 8, 8, 64) → flattened to 4096-dim feature vector
# ---------------------------------------------------------------------------
_ONNX_PATH = os.path.join(os.path.dirname(__file__), "models", "encoder.onnx")
_session = ort.InferenceSession(_ONNX_PATH, providers=["CPUExecutionProvider"])
_input_name  = _session.get_inputs()[0].name
_output_name = _session.get_outputs()[0].name


def run_inference(image_norm_32x32):
    """Run ONNX encoder → flat 1-D float32 feature vector (4096,)."""
    inp = np.expand_dims(image_norm_32x32, axis=0).astype(np.float32)
    out = _session.run([_output_name], {_input_name: inp})[0][0]  # (8,8,64)
    return out.flatten()


# ---------------------------------------------------------------------------
# Image helpers (Pillow only — no OpenCV)
# ---------------------------------------------------------------------------
def decode_image(file_bytes):
    """Raw bytes → numpy BGR uint8 array."""
    rgb = np.array(Image.open(io.BytesIO(file_bytes)).convert("RGB"))
    return rgb[:, :, ::-1].copy()


def save_image(numpy_bgr, path):
    """numpy BGR uint8 → PNG on disk."""
    Image.fromarray(numpy_bgr[:, :, ::-1].astype(np.uint8)).save(path, format="PNG")


def image_to_bytes(numpy_bgr):
    """numpy BGR uint8 → PNG bytes (for base64 embedding)."""
    buf = io.BytesIO()
    Image.fromarray(numpy_bgr[:, :, ::-1].astype(np.uint8)).save(buf, format="PNG")
    return buf.getvalue()


def resize_and_normalise(file_bytes, size=(32, 32)):
    """Returns (H,W,3) float32 in [0,1] for the encoder."""
    return np.array(
        Image.open(io.BytesIO(file_bytes)).convert("RGB").resize(size),
        dtype=np.float32
    ) / 255.0


# ---------------------------------------------------------------------------
# Route: serve files from /tmp/uploads
# (Vercel can't serve /tmp via static folder)
# ---------------------------------------------------------------------------
@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------
@app.route('/')
def sender_page():
    return render_template('sender.html')


@app.route('/receiver')
def receiver_page():
    return render_template('receiver.html')


# ---------------------------------------------------------------------------
# API: Encryption
# ---------------------------------------------------------------------------
@app.route('/api/encrypt', methods=['POST'])
def api_encrypt():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'})

    file = request.files['image']
    file_bytes = file.read()

    image      = decode_image(file_bytes)
    image_norm = resize_and_normalise(file_bytes)
    features   = run_inference(image_norm)          # (4096,)
    session_id = uuid.uuid4().hex

    encrypted = encrypt_image(image, features, session_id=session_id)

    # Save to /tmp (writable on Vercel)
    save_image(encrypted, os.path.join(UPLOAD_FOLDER, f"{session_id}_encrypted.png"))
    save_image(image,     os.path.join(UPLOAD_FOLDER, f"{session_id}_original.png"))
    np.save(os.path.join(UPLOAD_FOLDER, f"{session_id}_features.npy"), features)

    # Metrics
    entropy = calculate_entropy(encrypted)
    n       = npcr(image, encrypted)
    u       = uaci(image, encrypted)

    x0_base  = float(np.sum(features)) % 1.0
    h_val    = int(hashlib.sha256(session_id.encode()).hexdigest()[:8], 16)
    x0_salt  = h_val / 4294967295.0
    x0_final = (x0_base + x0_salt) % 1.0
    if x0_final <= 0 or x0_final >= 1:
        x0_final = 0.5

    return jsonify({
        'status': 'success',
        'encryptedUrl': f'/uploads/{session_id}_encrypted.png',
        'sessionId': session_id,
        'metrics': {
            'entropy': round(entropy, 4),
            'npcr':    round(n, 4),
            'uaci':    round(u, 4)
        },
        'formulaData': {'x0': round(x0_final, 8)}
    })


# ---------------------------------------------------------------------------
# API: Decryption
# ---------------------------------------------------------------------------
@app.route('/api/decrypt', methods=['POST'])
def api_decrypt():
    if 'image' not in request.files:
        return jsonify({'error': 'No encrypted image uploaded'})

    sessionId = request.form.get('sessionId')
    if not sessionId:
        return jsonify({'error': 'No sessionId provided'})

    file_bytes = request.files['image'].read()
    encrypted  = decode_image(file_bytes)

    feat_path = os.path.join(UPLOAD_FOLDER, f"{sessionId}_features.npy")
    if not os.path.exists(feat_path):
        return jsonify({'error': 'Session expired or not found. Please encrypt the image again.'})

    features  = np.load(feat_path)
    decrypted = decrypt_image(encrypted, features, session_id=sessionId)

    dec_path = os.path.join(UPLOAD_FOLDER, f"{sessionId}_decrypted.png")
    save_image(decrypted, dec_path)

    return jsonify({
        'status': 'success',
        'decryptedUrl': f'/uploads/{sessionId}_decrypted.png'
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)
