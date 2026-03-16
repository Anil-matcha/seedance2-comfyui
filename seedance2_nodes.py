"""
MuAPI Seedance 2.0 ComfyUI Nodes
==================================
Focused nodes for Seedance 2.0 video generation via muapi.ai.

  Seedance2TextToVideo  — POST /api/v1/seedance-v2.0-t2v
  Seedance2ImageToVideo — POST /api/v1/seedance-v2.0-i2v
  Seedance2Extend       — POST /api/v1/seedance-v2.0-extend

Auth:     x-api-key header
Polling:  GET /api/v1/predictions/{request_id}/result
Upload:   POST /api/v1/upload_file
"""

import io
import os
import time

import numpy as np
import requests
import torch
from PIL import Image

BASE_URL = "https://api.muapi.ai/api/v1"
POLL_INTERVAL = 10
MAX_WAIT = 900

# ── Helpers ────────────────────────────────────────────────────────────────────

def _load_api_key(api_key_input):
    """Return api_key_input if set, otherwise fall back to ~/.muapi/config.json."""
    if api_key_input and api_key_input.strip():
        return api_key_input.strip()
    config_path = os.path.expanduser("~/.muapi/config.json")
    if os.path.isfile(config_path):
        try:
            import json as _json
            with open(config_path) as f:
                key = _json.load(f).get("api_key", "")
            if key:
                return key
        except Exception:
            pass
    raise RuntimeError(
        "No API key found. Either paste your key into the api_key field, "
        "or run `muapi auth configure --api-key YOUR_KEY` in a terminal."
    )

def _upload_image(api_key, image_tensor):
    if image_tensor.dim() == 4:
        image_tensor = image_tensor[0]
    arr = (image_tensor.cpu().numpy() * 255).astype("uint8")
    buf = io.BytesIO()
    Image.fromarray(arr, "RGB").save(buf, format="JPEG", quality=95)
    buf.seek(0)
    resp = requests.post(f"{BASE_URL}/upload_file",
                         headers={"x-api-key": api_key},
                         files={"file": ("image.jpg", buf, "image/jpeg")},
                         timeout=120)
    _check(resp)
    return _url(resp.json())

def _url(data):
    u = data.get("url") or data.get("file_url") or data.get("output")
    if not u: raise RuntimeError(f"Upload missing URL: {data}")
    return str(u)

def _submit(api_key, endpoint, payload):
    resp = requests.post(f"{BASE_URL}/{endpoint}",
                         headers={"x-api-key": api_key, "Content-Type": "application/json"},
                         json=payload, timeout=60)
    _check(resp)
    rid = resp.json().get("request_id")
    if not rid: raise RuntimeError(f"No request_id: {resp.json()}")
    return rid

def _poll(api_key, request_id):
    deadline = time.time() + MAX_WAIT
    while time.time() < deadline:
        resp = requests.get(f"{BASE_URL}/predictions/{request_id}/result",
                            headers={"x-api-key": api_key}, timeout=30)
        _check(resp)
        data = resp.json()
        status = data.get("status")
        print(f"[Seedance2] {status}  {request_id}")
        if status == "completed": return data
        if status == "failed": raise RuntimeError(f"Failed: {data.get('error','unknown')}")
        time.sleep(POLL_INTERVAL)
    raise RuntimeError(f"Timeout: {request_id}")

def _output_url(result):
    out = result.get("outputs") or result.get("output") or []
    if isinstance(out, list) and out: return str(out[0])
    if isinstance(out, str): return out
    for k in ("video_url", "url"):
        if result.get(k): return str(result[k])
    raise RuntimeError(f"No output URL: {result}")

def _check(resp):
    if resp.status_code == 401: raise RuntimeError("Auth failed — check API key.")
    if resp.status_code == 402: raise RuntimeError("Insufficient credits — top up at muapi.ai")
    if resp.status_code == 429: raise RuntimeError("Rate limited — retry later.")
    resp.raise_for_status()

def _first_frame(video_url):
    try:
        import tempfile, cv2
        r = requests.get(video_url, timeout=180, stream=True)
        r.raise_for_status()
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            for chunk in r.iter_content(8192):
                if chunk: tmp.write(chunk)
            path = tmp.name
        cap = cv2.VideoCapture(path)
        ret, frame = cap.read()
        cap.release(); os.remove(path)
        if not ret: raise RuntimeError("no frame")
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        return torch.from_numpy(rgb).unsqueeze(0)
    except Exception as e:
        print(f"[Seedance2] first frame failed: {e}")
        return torch.zeros(1, 64, 64, 3)

# ── Nodes ──────────────────────────────────────────────────────────────────────

class Seedance2TextToVideo:
    """
    Seedance 2.0 Text-to-Video
    ---------------------------
    Generate video purely from a text prompt.
    Aspect ratios: 16:9 | 9:16 | 4:3 | 3:4
    Duration: 5 | 10 | 15 seconds
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "prompt": ("STRING", {"multiline": True,
                "default": "A cinematic aerial shot of a futuristic city at dusk, volumetric lighting, 4K"}),
            "aspect_ratio": (["16:9", "9:16", "4:3", "3:4"], {"default": "16:9"}),
            "quality": (["basic", "high"], {"default": "basic"}),
            "duration": ([5, 10, 15], {"default": 5}),
        }, "optional": {
            "api_key": ("STRING", {"multiline": False, "default": ""}),
        }}
    RETURN_TYPES = ("STRING", "IMAGE", "STRING")
    RETURN_NAMES = ("video_url", "first_frame", "request_id")
    FUNCTION = "run"
    CATEGORY = "🌱 Seedance 2.0"

    def run(self, prompt, aspect_ratio, quality, duration, api_key=""):
        api_key = _load_api_key(api_key)
        payload = {"prompt": prompt, "aspect_ratio": aspect_ratio,
                   "quality": quality, "duration": duration}
        print("[Seedance2 T2V] Submitting...")
        rid = _submit(api_key, "seedance-v2.0-t2v", payload)
        result = _poll(api_key, rid)
        url = _output_url(result)
        print(f"[Seedance2 T2V] Done → {url}")
        return (url, _first_frame(url), rid)


class Seedance2ImageToVideo:
    """
    Seedance 2.0 Image-to-Video
    ----------------------------
    Connect up to 9 reference images. Reference them in the prompt
    using @image1 … @image9.

    Example: "The cat in @image1 walks through a sunlit garden."
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "prompt": ("STRING", {"multiline": True,
                "default": "The character in @image1 walks through a beautiful garden, cinematic motion"}),
            "aspect_ratio": (["16:9", "9:16", "4:3", "3:4"], {"default": "16:9"}),
            "quality": (["basic", "high"], {"default": "basic"}),
            "duration": ([5, 10, 15], {"default": 5}),
        }, "optional": {
            "api_key": ("STRING", {"multiline": False, "default": ""}),
            "image_1": ("IMAGE",), "image_2": ("IMAGE",), "image_3": ("IMAGE",),
            "image_4": ("IMAGE",), "image_5": ("IMAGE",), "image_6": ("IMAGE",),
            "image_7": ("IMAGE",), "image_8": ("IMAGE",), "image_9": ("IMAGE",),
        }}
    RETURN_TYPES = ("STRING", "IMAGE", "STRING")
    RETURN_NAMES = ("video_url", "first_frame", "request_id")
    FUNCTION = "run"
    CATEGORY = "🌱 Seedance 2.0"

    def run(self, prompt, aspect_ratio, quality, duration, api_key="",
            image_1=None, image_2=None, image_3=None, image_4=None, image_5=None,
            image_6=None, image_7=None, image_8=None, image_9=None):
        api_key = _load_api_key(api_key)
        tensors = [image_1, image_2, image_3, image_4, image_5,
                   image_6, image_7, image_8, image_9]
        images_list = []
        for i, img in enumerate(tensors, 1):
            if img is not None:
                print(f"[Seedance2 I2V] Uploading image {i}...")
                images_list.append(_upload_image(api_key, img))
        if not images_list: raise ValueError("At least one image required.")
        payload = {"prompt": prompt, "images_list": images_list,
                   "aspect_ratio": aspect_ratio, "quality": quality, "duration": duration}
        print(f"[Seedance2 I2V] Submitting ({len(images_list)} image(s))...")
        rid = _submit(api_key, "seedance-v2.0-i2v", payload)
        result = _poll(api_key, rid)
        url = _output_url(result)
        print(f"[Seedance2 I2V] Done → {url}")
        return (url, _first_frame(url), rid)


class Seedance2Extend:
    """
    Seedance 2.0 Extend Video
    --------------------------
    Extend a previously generated Seedance 2.0 video.
    Pass the request_id from a completed generation.
    Optionally provide a prompt to guide the continuation.
    Duration: 5 | 10 | 15 seconds added to the original.
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "request_id": ("STRING", {"multiline": False, "default": "",
                "tooltip": "request_id from a completed Seedance 2.0 generation"}),
            "quality": (["basic", "high"], {"default": "basic"}),
            "duration": ([5, 10, 15], {"default": 5}),
        }, "optional": {
            "api_key": ("STRING", {"multiline": False, "default": ""}),
            "prompt": ("STRING", {"multiline": True, "default": "",
                "tooltip": "Optional continuation prompt"}),
        }}
    RETURN_TYPES = ("STRING", "IMAGE", "STRING")
    RETURN_NAMES = ("video_url", "first_frame", "new_request_id")
    FUNCTION = "run"
    CATEGORY = "🌱 Seedance 2.0"

    def run(self, request_id, quality, duration, api_key="", prompt=""):
        api_key = _load_api_key(api_key)
        if not request_id.strip(): raise ValueError("request_id required.")
        payload = {"request_id": request_id.strip(), "quality": quality, "duration": duration}
        if prompt.strip(): payload["prompt"] = prompt.strip()
        print(f"[Seedance2 Extend] Extending {request_id}...")
        new_id = _submit(api_key, "seedance-v2.0-extend", payload)
        result = _poll(api_key, new_id)
        url = _output_url(result)
        print(f"[Seedance2 Extend] Done → {url}")
        return (url, _first_frame(url), new_id)


class Seedance2ApiKey:
    """
    Store your MuAPI API key once and wire it to any Seedance 2.0 node.
    Leave all node api_key fields empty — they auto-read from this node
    or from ~/.muapi/config.json (set via `muapi auth configure`).
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "api_key": ("STRING", {"multiline": False, "default": "",
                "tooltip": "Your muapi.ai API key. Get one at muapi.ai → Dashboard → API Keys"}),
        }}
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("api_key",)
    FUNCTION = "run"
    CATEGORY = "🌱 Seedance 2.0"

    def run(self, api_key):
        return (_load_api_key(api_key),)


NODE_CLASS_MAPPINGS = {
    "Seedance2ApiKey":       Seedance2ApiKey,
    "Seedance2TextToVideo":  Seedance2TextToVideo,
    "Seedance2ImageToVideo": Seedance2ImageToVideo,
    "Seedance2Extend":       Seedance2Extend,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Seedance2ApiKey":       "🔑 Seedance 2.0 API Key",
    "Seedance2TextToVideo":  "🌱 Seedance 2.0 Text-to-Video",
    "Seedance2ImageToVideo": "🌱 Seedance 2.0 Image-to-Video",
    "Seedance2Extend":       "🌱 Seedance 2.0 Extend",
}
