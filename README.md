# MuAPI Seedance 2.0 ComfyUI Nodes

Focused ComfyUI nodes for **Seedance 2.0** video generation via [muapi.ai](https://muapi.ai).

## Nodes (4 total)

| Node | Description |
|------|-------------|
| 🌱 Seedance 2.0 Text-to-Video | Generate video from a text prompt |
| 🌱 Seedance 2.0 Image-to-Video | Animate up to 9 reference images |
| 🌱 Seedance 2.0 Extend | Extend a previously generated video |
| 🌱 Seedance 2.0 Save Video | Download URL → disk + frames tensor |

## Installation

**Via ComfyUI Manager:**
1. Manager → Install via Git URL
2. Paste: `https://github.com/Anil-matcha/seedance2-comfyui`
3. Restart ComfyUI

**Manual:**
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/Anil-matcha/seedance2-comfyui
pip install -r seedance2-comfyui/requirements.txt
```

## Usage

1. Get your API key at [muapi.ai](https://muapi.ai) → Dashboard → API Keys
2. Right-click canvas → Add Node → **🌱 Seedance 2.0**
3. Paste your key into `api_key` and start generating

## Node Reference

### 🌱 Seedance 2.0 Text-to-Video
| Field | Values |
|-------|--------|
| prompt | Text describing the video |
| aspect_ratio | 16:9 / 9:16 / 4:3 / 3:4 |
| quality | basic / high |
| duration | 5 / 10 / 15 seconds |

### 🌱 Seedance 2.0 Image-to-Video
Connect up to 9 reference images (`image_1` … `image_9`).
Reference them in the prompt as `@image1` … `@image9`.

Example: `"The cat in @image1 walks through a sunlit garden."`

### 🌱 Seedance 2.0 Extend
Pass the `request_id` from any completed Seedance 2.0 generation.
Optionally add a continuation prompt.

### 🌱 Seedance 2.0 Save Video
Downloads the generated video URL to disk and returns all frames as an IMAGE tensor for further processing.

## License

MIT
