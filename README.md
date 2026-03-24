# Seedance 2.0 ComfyUI Nodes

> **ComfyUI custom nodes for Seedance 2.0** — the state-of-the-art video generation model by ByteDance.
> Generate stunning AI videos directly inside ComfyUI using the [muapi.ai](https://muapi.ai) API.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![ComfyUI](https://img.shields.io/badge/ComfyUI-Custom%20Node-blue)](https://github.com/comfyanonymous/ComfyUI)
[![Seedance 2.0](https://img.shields.io/badge/Model-Seedance%202.0-green)](https://muapi.ai)

---

## What is Seedance 2.0?

Seedance 2.0 is ByteDance's latest video generation model, capable of producing high-quality, photorealistic videos from text prompts or reference images. It supports:

- **Text-to-Video** — generate video from a text description
- **Image-to-Video** — animate up to 9 reference images with motion guidance
- **Omni Reference** — combine images, video clips, and audio as multi-modal reference inputs
- **Video Extend** — seamlessly extend any generated video

---

## Nodes

| Node | Description |
|------|-------------|
| 🔑 Seedance 2.0 API Key | Set your key once — wire to all nodes |
| 🌱 Seedance 2.0 Text-to-Video | Generate video from a text prompt |
| 🌱 Seedance 2.0 Image-to-Video | Animate up to 9 reference images |
| 🌱 Seedance 2.0 Omni Reference | Multi-modal: combine images, video clips, and audio |
| 🌱 Seedance 2.0 Extend | Extend a previously generated video |
| 🌱 Seedance 2.0 Save Video | Download URL → disk + ComfyUI IMAGE frames |

---

## Installation

### Via ComfyUI Manager (recommended)
1. Open **ComfyUI Manager** → **Install via Git URL**
2. Paste: `https://github.com/Anil-matcha/seedance2-comfyui`
3. Restart ComfyUI

### Manual
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/Anil-matcha/seedance2-comfyui
pip install -r seedance2-comfyui/requirements.txt
```

---

## Quick Start

1. Sign up at [muapi.ai](https://muapi.ai) and go to **Dashboard → API Keys → Create Key**
2. Right-click the ComfyUI canvas → **Add Node** → **🌱 Seedance 2.0**
3. Add a **🔑 Seedance 2.0 API Key** node, paste your key, and wire its output to any generation node
4. Write a prompt and hit **Queue Prompt**

> **Tip:** If you use the [MuAPI CLI](https://github.com/SamurAIGPT/muapi-cli), run `muapi auth configure --api-key YOUR_KEY` once and all nodes will pick it up automatically — no need to paste the key anywhere.

---

## Node Reference

### 🔑 Seedance 2.0 API Key

Set your muapi.ai API key once and wire the output to all generation nodes. Alternatively, leave every `api_key` field blank — nodes automatically read from `~/.muapi/config.json` if you've authenticated via the CLI.

---

### 🌱 Seedance 2.0 Text-to-Video

Generate a video from a text description.

| Field | Values | Default |
|-------|--------|---------|
| `api_key` | Optional — leave blank if using the API Key node or CLI config | — |
| `prompt` | Text describing the video | — |
| `aspect_ratio` | 16:9 / 9:16 / 4:3 / 3:4 | 16:9 |
| `quality` | basic / high | basic |
| `duration` | 5 / 10 / 15 seconds | 5 |

**Outputs:** `video_url` · `first_frame` (IMAGE) · `request_id`

---

### 🌱 Seedance 2.0 Image-to-Video

Animate reference images into a video. Connect up to 9 images via `image_1` … `image_9` and reference them in the prompt using `@image1` … `@image9`.

**Example prompt:**
```
The cat in @image1 walks gracefully through a sunlit garden.
@image1 transforms into @image2 with a smooth dissolve transition.
```

---

### 🌱 Seedance 2.0 Omni Reference

Multi-modal video generation that combines images, video clips, and audio clips as reference material alongside a text prompt. Use `@image1`…`@image9`, `@video1`…`@video3`, and `@audio1`…`@audio3` to reference media in the prompt.

**Example prompt:**
```
A person @image1 walking on the beach at sunset, cinematic lighting, with @audio1 as background music.
```

| Field | Values | Default |
|-------|--------|---------|
| `prompt` | Text with optional `@imageN`, `@videoN`, `@audioN` references | — |
| `aspect_ratio` | 21:9 / 16:9 / 4:3 / 1:1 / 3:4 / 9:16 | 16:9 |
| `duration` | 4 – 15 seconds (integer) | 5 |
| `image_1` … `image_9` | Optional — ComfyUI IMAGE tensors (auto-uploaded) | — |
| `video_url_1` … `video_url_3` | Optional — MP4 URL (max 15s each) | — |
| `audio_url_1` … `audio_url_3` | Optional — MP3/WAV URL (total max 15s) | — |

**Outputs:** `video_url` · `first_frame` (IMAGE) · `request_id`

---

### 🌱 Seedance 2.0 Extend

Continue any completed Seedance 2.0 video. Connect the `request_id` output from a generation node.

| Field | Description |
|-------|-------------|
| `request_id` | From a completed T2V or I2V generation |
| `prompt` | Optional — guide the continuation |
| `quality` | basic / high |
| `duration` | 5 / 10 / 15 seconds to add |

---

### 🌱 Seedance 2.0 Save Video

Downloads the generated video to ComfyUI's output folder and returns all frames as an IMAGE tensor for use with other nodes (preview, VHS, upscale, etc.).

---

## Example Workflow

Load `Seedance2_T2V_Example.json` from this repo via **File → Load** in ComfyUI.

```
[🔑 API Key] ──────────────────────────────────┐
                                                ↓
[🌱 Text-to-Video] → video_url → [🌱 Save Video] → frames → [Preview Image]
```

---

## API

This node pack uses the **muapi.ai** API under the hood:
- **T2V:** `POST https://api.muapi.ai/api/v1/seedance-v2.0-t2v`
- **I2V:** `POST https://api.muapi.ai/api/v1/seedance-v2.0-i2v`
- **Omni:** `POST https://api.muapi.ai/api/v1/seedance-2.0-omni-reference`
- **Extend:** `POST https://api.muapi.ai/api/v1/seedance-v2.0-extend`
- **Poll:** `GET https://api.muapi.ai/api/v1/predictions/{id}/result`
- **Upload:** `POST https://api.muapi.ai/api/v1/upload_file`

Authentication is a single `x-api-key` header — no session tokens required.

---

## Requirements

- Python ≥ 3.8
- `requests` ≥ 2.28 · `Pillow` ≥ 9.0 · `numpy` ≥ 1.23 · `torch` ≥ 2.0 · `opencv-python` ≥ 4.7

---

## Want More Models?

This repo is focused on Seedance 2.0 only. If you need access to **100+ models** — Kling, Veo3, Flux, HiDream, GPT-image-1.5, Imagen4, Wan, lipsync, audio, image enhancement and more — check out the full MuAPI ComfyUI node pack:

**[SamurAIGPT/muapi-comfyui](https://github.com/SamurAIGPT/muapi-comfyui)** — ComfyUI nodes for every muapi.ai model in one place.

---

## License

MIT © 2026
