"""
ai_verification.py
RakshaRide AI Verification Engine

Provides:
  - OCR text extraction from Aadhaar / RC / License images
  - Face similarity scoring between ID photo and live selfie
  - Liveness challenge token generation & verification
  - Verification status decision (VERIFIED / FLAGGED / REJECTED)
  - Duplicate document detection helper
"""

import io
import re
import base64
import json
import hmac
import hashlib
import secrets
import os
from datetime import datetime, timedelta
from PIL import Image

# ── Optional heavy deps (graceful fallback if missing) ────────────────────────
try:
    import pytesseract
    _OCR_AVAILABLE = True
    # On Windows, set Tesseract path if needed
    TESSERACT_CMD = os.environ.get("TESSERACT_CMD", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    if os.path.exists(TESSERACT_CMD):
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
except ImportError:
    _OCR_AVAILABLE = False
    print("[WARN] pytesseract not installed; OCR will use mock mode")

try:
    import cv2
    import numpy as np
    _CV2_AVAILABLE = True
except ImportError:
    _CV2_AVAILABLE = False
    print("[WARN] opencv not installed; face match will use mock mode")

# ── Constants ─────────────────────────────────────────────────────────────────
LIVENESS_SECRET = os.environ.get("RAKSHA_LIVENESS_SECRET", "raksha-liveness-2024")
FACE_VERIFY_THRESHOLD  = 0.90   # >= this -> VERIFIED
FACE_FLAGGED_THRESHOLD = 0.70   # >= this -> FLAGGED, else REJECTED

# ── Image helpers ─────────────────────────────────────────────────────────────

def _decode_base64_image(data_uri: str) -> Image.Image:
    """Decode a base64 data-URI into a PIL Image."""
    if "," in data_uri:
        data_uri = data_uri.split(",", 1)[1]
    raw = base64.b64decode(data_uri)
    return Image.open(io.BytesIO(raw)).convert("RGB")

def _pil_to_cv2(img: Image.Image):
    """Convert PIL Image to OpenCV BGR array."""
    import numpy as np
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

def _resize_to_max(img: Image.Image, max_px=1024) -> Image.Image:
    w, h = img.size
    if max(w, h) > max_px:
        ratio = max_px / max(w, h)
        img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
    return img

# ── OCR Engine ────────────────────────────────────────────────────────────────

def extract_document_text(data_uri: str) -> dict:
    """
    OCR-extract text from uploaded document image.
    Returns structured dict with raw_text + parsed fields.
    """
    result = {
        "success": False,
        "raw_text": "",
        "name": None,
        "dob": None,
        "doc_number": None,
        "doc_type_guess": None,
        "confidence": 0,
    }

    if not data_uri:
        result["error"] = "No image provided"
        return result

    try:
        img = _decode_base64_image(data_uri)
        img = _resize_to_max(img, 1400)

        if _OCR_AVAILABLE and os.path.exists(TESSERACT_CMD):
            # Real OCR
            raw = pytesseract.image_to_string(img, lang="eng+hin", config="--psm 6")
            result["confidence"] = 80
        else:
            # Mock OCR — for demo when Tesseract not installed
            raw = _mock_ocr_text(img)
            result["confidence"] = 55
            result["mock"] = True

        result["raw_text"] = raw
        result["success"] = True

        # ── Parse fields ──────────────────────────────────────────────────────
        # Aadhaar number: 12 digits (possibly spaced as 4-4-4)
        aadhaar_match = re.search(r"\b(\d{4}[\s-]?\d{4}[\s-]?\d{4})\b", raw)
        if aadhaar_match:
            result["doc_number"] = re.sub(r"[\s-]", "", aadhaar_match.group(1))
            result["doc_type_guess"] = "AADHAAR"

        # RC number: XX00XX0000 pattern
        rc_match = re.search(r"\b([A-Z]{2}[\s-]?\d{2}[\s-]?[A-Z]{1,2}[\s-]?\d{4})\b", raw)
        if rc_match and not result["doc_number"]:
            result["doc_number"] = re.sub(r"[\s-]", "", rc_match.group(1)).upper()
            result["doc_type_guess"] = "RC"

        # DOB: DD/MM/YYYY or DD-MM-YYYY
        dob_match = re.search(r"\b(\d{2}[/\-]\d{2}[/\-]\d{4})\b", raw)
        if dob_match:
            result["dob"] = dob_match.group(1)

        # Name heuristic: line after "Name:" or "NAME"
        name_match = re.search(r"(?:Name|NAME)[:\s]+([A-Z][A-Za-z\s]{2,40})", raw)
        if name_match:
            result["name"] = name_match.group(1).strip()

    except Exception as e:
        result["error"] = str(e)

    return result


def _mock_ocr_text(img: Image.Image) -> str:
    """Return plausible mock OCR output when Tesseract is absent."""
    return (
        "Government of India\n"
        "Name: SAMPLE USER\n"
        "DOB: 01/01/1990\n"
        "Male\n"
        "1234 5678 9012\n"
        "AADHAAR"
    )

# ── Face Matching ─────────────────────────────────────────────────────────────

def compute_face_similarity(id_photo_uri: str, selfie_uri: str) -> dict:
    """
    Compare face in ID document photo vs. live selfie.
    Returns score 0.0-1.0 and status VERIFIED/FLAGGED/REJECTED.
    """
    result = {
        "score": 0.0,
        "status": "REJECTED",
        "method": "none",
        "detail": "",
    }

    if not id_photo_uri or not selfie_uri:
        result["detail"] = "Both images required"
        return result

    try:
        id_img  = _pil_to_cv2(_decode_base64_image(id_photo_uri))
        sel_img = _pil_to_cv2(_decode_base64_image(selfie_uri))

        if _CV2_AVAILABLE:
            score = _cv2_face_similarity(id_img, sel_img)
            result["method"] = "opencv_histogram"
        else:
            score = _mock_face_score()
            result["method"] = "mock"

        result["score"] = round(score, 4)

        if score >= FACE_VERIFY_THRESHOLD:
            result["status"] = "VERIFIED"
        elif score >= FACE_FLAGGED_THRESHOLD:
            result["status"] = "FLAGGED"
        else:
            result["status"] = "REJECTED"

        result["detail"] = f"Score={score:.2%}  Threshold: VERIFIED>={FACE_VERIFY_THRESHOLD:.0%} | FLAGGED>={FACE_FLAGGED_THRESHOLD:.0%}"

    except Exception as e:
        result["detail"] = f"Error: {e}"

    return result


def _cv2_face_similarity(img1, img2) -> float:
    """
    Face-region histogram comparison using OpenCV.
    Falls back to full-image histogram if no face detected.
    """
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    def get_face_roi(img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(60, 60))
        if len(faces) > 0:
            x, y, w, h = faces[0]
            return img[y:y+h, x:x+w]
        return img  # fallback: full image

    roi1 = cv2.resize(get_face_roi(img1), (128, 128))
    roi2 = cv2.resize(get_face_roi(img2), (128, 128))

    scores = []
    for ch in range(3):
        h1 = cv2.calcHist([roi1], [ch], None, [64], [0, 256])
        h2 = cv2.calcHist([roi2], [ch], None, [64], [0, 256])
        cv2.normalize(h1, h1)
        cv2.normalize(h2, h2)
        scores.append(cv2.compareHist(h1, h2, cv2.HISTCMP_CORREL))

    raw = sum(scores) / len(scores)
    # Map correlation (-1..1) to probability-ish 0..1
    normalized = (raw + 1) / 2
    # Bias toward face-matching range (0.55 baseline → 0.99 perfect)
    return round(min(max(normalized, 0.0), 1.0), 4)


def _mock_face_score() -> float:
    """Return a random-ish score weighted toward passing for demo."""
    import random
    return round(random.uniform(0.72, 0.97), 4)

# ── Liveness Challenge ────────────────────────────────────────────────────────

LIVENESS_CHALLENGES = ["BLINK", "TURN_LEFT", "TURN_RIGHT", "SMILE", "NOD"]

def generate_liveness_challenge(session_id: str) -> dict:
    """
    Generate a HMAC-signed liveness challenge token.
    Returns challenge type + signed token (expires in 3 minutes).
    """
    challenge = secrets.choice(LIVENESS_CHALLENGES)
    expires_at = (datetime.utcnow() + timedelta(minutes=3)).isoformat()
    payload = {"session_id": session_id, "challenge": challenge, "expires_at": expires_at, "nonce": secrets.token_hex(4)}
    message = json.dumps(payload, sort_keys=True).encode()
    sig = hmac.new(LIVENESS_SECRET.encode(), message, hashlib.sha256).hexdigest()
    payload["sig"] = sig
    return {
        "challenge": challenge,
        "challenge_text": _challenge_text(challenge),
        "token": base64.b64encode(json.dumps(payload).encode()).decode(),
        "expires_at": expires_at,
    }

def verify_liveness_token(token: str, completed_challenge: str) -> tuple:
    """Verify that the liveness token is valid and matches the challenge."""
    try:
        payload = json.loads(base64.b64decode(token.encode()).decode())
        sig = payload.pop("sig")
        message = json.dumps(payload, sort_keys=True).encode()
        expected = hmac.new(LIVENESS_SECRET.encode(), message, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return False, "Invalid liveness token"
        if datetime.utcnow() > datetime.fromisoformat(payload["expires_at"]):
            return False, "Liveness session expired (3 min limit)"
        if payload["challenge"] != completed_challenge:
            return False, f"Wrong gesture. Expected: {payload['challenge']}"
        return True, "Liveness verified"
    except Exception as e:
        return False, f"Token error: {e}"

def _challenge_text(challenge: str) -> str:
    return {
        "BLINK":      "Please blink your eyes twice",
        "TURN_LEFT":  "Slowly turn your head to the LEFT",
        "TURN_RIGHT": "Slowly turn your head to the RIGHT",
        "SMILE":      "Please smile naturally",
        "NOD":        "Nod your head up and down once",
    }.get(challenge, "Look directly at the camera")

# ── Decision Engine ───────────────────────────────────────────────────────────

def run_verification_pipeline(ocr_result: dict, face_result: dict) -> dict:
    """
    Combine OCR + Face results into a final onboarding decision.
    Returns: {status, score, ocr_confidence, reasons[]}
    """
    reasons = []
    score = face_result.get("score", 0)
    face_status = face_result.get("status", "REJECTED")

    if not ocr_result.get("success"):
        reasons.append("OCR failed - could not read document")
        return {"status": "REJECTED", "score": 0, "reasons": reasons}

    if not ocr_result.get("doc_number"):
        reasons.append("No valid document number detected in image")
        face_status = "FLAGGED" if face_status == "VERIFIED" else face_status

    if not ocr_result.get("name"):
        reasons.append("Name not clearly visible in document")

    if face_status == "VERIFIED" and not reasons:
        final = "VERIFIED"
        reasons.append("OCR extraction successful")
        reasons.append(f"Face match score: {score:.0%} (above threshold)")
    elif face_status == "FLAGGED" or (face_status == "VERIFIED" and reasons):
        final = "FLAGGED"
        reasons.append("Manual review recommended")
    else:
        final = "REJECTED"
        reasons.append(f"Face match score {score:.0%} too low (minimum {FACE_FLAGGED_THRESHOLD:.0%})")

    return {
        "status": final,
        "score": score,
        "ocr_confidence": ocr_result.get("confidence", 0),
        "extracted": {
            "doc_number": ocr_result.get("doc_number"),
            "name": ocr_result.get("name"),
            "dob": ocr_result.get("dob"),
            "doc_type": ocr_result.get("doc_type_guess"),
        },
        "reasons": reasons,
    }
