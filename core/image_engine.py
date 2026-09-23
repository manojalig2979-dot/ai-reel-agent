import os
import sys
import random
import urllib.parse
from pathlib import Path
from typing import Optional, List
import requests
from PIL import Image, ImageDraw, ImageFilter
import config


class ImageEngine:
    def __init__(self, width: int = config.VIDEO_WIDTH, height: int = config.VIDEO_HEIGHT):
        self.width = width
        self.height = height

    def generate_image(
        self,
        prompt: str,
        output_path: Path,
        style: Optional[str] = None,
        seed: Optional[int] = None
    ) -> Path:
        """
        Generates a 9:16 vertical image referencing the exact scene script and chosen visual style.
        Uses a multi-tier AI model cascade (FLUX -> Turbo -> Contextual) for high quality.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if seed is None:
            seed = random.randint(1000, 999999)

        # Style-aware prompt enhancement
        style_suffix = ""
        if style and style in config.STYLE_PRESETS:
            style_suffix = f", {config.STYLE_PRESETS[style]['prompt_suffix']}"
        elif any(k in prompt.lower() for k in ["hanuman", "bal ", "kid", "child", "pixar", "disney"]):
            style_suffix = ", 3D Pixar Disney style CGI animation, adorable heroic character design, bright expressive eyes, vibrant colors, magical golden sparkle aura, volumetric studio lighting, vertical 9:16"
        else:
            style_suffix = ", cinematic atmosphere, 8k resolution, volumetric lighting, photorealistic masterwork, vertical 9:16"

        clean_prompt = prompt.strip().replace("\n", " ")
        enhanced_prompt = f"{clean_prompt}{style_suffix}"
        encoded = urllib.parse.quote(enhanced_prompt)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        # 1. Multi-Model AI Generation Cascade (Flux -> Turbo -> Realism)
        ai_models = ["flux", "turbo", "flux-realism"]
        for model_name in ai_models:
            url = (
                f"https://image.pollinations.ai/prompt/{encoded}"
                f"?width=720&height=1280&seed={seed}&nologo=true&model={model_name}&enhance=true"
            )
            try:
                res = requests.get(url, headers=headers, timeout=22)
                if res.status_code == 200 and len(res.content) > 15000 and b"<!DOCTYPE html>" not in res.content[:100]:
                    with open(output_path, "wb") as f:
                        f.write(res.content)
                    with Image.open(output_path) as img:
                        img.verify()
                    # Resize/upscale to target video dimensions if needed
                    with Image.open(output_path) as img:
                        if img.size != (self.width, self.height):
                            resized = img.resize((self.width, self.height), Image.Resampling.LANCZOS)
                            resized.save(output_path, quality=95)
                    print(f"[ImageEngine] [SUCCESS] AI Scene Image generated via {model_name}: {output_path}")
                    return output_path
            except Exception as e:
                print(f"[ImageEngine] Model {model_name} note: {e}. Trying next cascade model...")
                continue

        # 2. Contextual Thematic Visual Fallback
        self._generate_thematic_fallback(clean_prompt, output_path, seed)
        return output_path

    def _generate_thematic_fallback(self, prompt: str, output_path: Path, seed: int) -> None:
        """
        Renders a thematic, mood-aligned procedural gradient with ambient lighting.
        """
        random.seed(seed)
        prompt_lower = prompt.lower()
        
        # Determine theme-specific color palette based on prompt content
        if any(w in prompt_lower for w in ["hanuman", "bajrangbali", "maruti", "ram", "krishna", "divine", "god", "spiritual", "shloka", "temple", "sacred"]):
            # Divine Golden Saffron & Radiant Aura
            palette = [(30, 15, 45), (180, 70, 20), (255, 170, 30)]
            accent_col = (255, 220, 90)
        elif any(w in prompt_lower for w in ["kid", "child", "pixar", "disney", "cartoon", "animation"]):
            # Cheerful Vibrant Coral & Cyan
            palette = [(18, 30, 60), (40, 120, 180), (255, 130, 80)]
            accent_col = (255, 230, 100)
        elif any(w in prompt_lower for w in ["rain", "melancholy", "sad", "alone", "dark", "heart", "tears", "poetry", "shayari"]):
            # Deep Rainy Indigo & Moody Twilight
            palette = [(10, 15, 30), (30, 40, 65), (70, 80, 110)]
            accent_col = (120, 180, 240)
        elif any(w in prompt_lower for w in ["space", "cosmos", "galaxy", "black hole", "star", "universe"]):
            # Cosmic Deep Violet & Nebula Starfield
            palette = [(8, 8, 20), (35, 15, 55), (80, 30, 100)]
            accent_col = (180, 120, 255)
        elif any(w in prompt_lower for w in ["motivation", "fire", "success", "warrior", "battle"]):
            # Fiery Amber & Volcanic Red
            palette = [(25, 10, 10), (90, 25, 15), (200, 70, 20)]
            accent_col = (255, 130, 40)
        else:
            # Modern Cyber Dark
            palette = [(15, 18, 26), (32, 42, 60), (45, 65, 90)]
            accent_col = (0, 229, 255)

        img = Image.new("RGB", (self.width, self.height), color=palette[0])
        draw = ImageDraw.Draw(img)

        # Smooth vertical gradient
        steps = 80
        for i in range(steps):
            t = i / steps
            if t < 0.5:
                blend = t * 2
                c = [int(palette[0][k]*(1-blend) + palette[1][k]*blend) for k in range(3)]
            else:
                blend = (t - 0.5) * 2
                c = [int(palette[1][k]*(1-blend) + palette[2][k]*blend) for k in range(3)]
            
            y0 = int(i * (self.height / steps))
            y1 = int((i + 1) * (self.height / steps))
            draw.rectangle([0, y0, self.width, y1], fill=tuple(c))

        # Add celestial light blooms matching the theme
        for _ in range(6):
            cx = random.randint(150, self.width - 150)
            cy = random.randint(250, self.height - 250)
            radius = random.randint(220, 450)
            glow_col = (
                min(255, accent_col[0] + random.randint(-30, 30)),
                min(255, accent_col[1] + random.randint(-30, 30)),
                min(255, accent_col[2] + random.randint(-30, 30))
            )
            draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=glow_col)

        # Gaussian blur for soft volumetric cinematic glow
        img = img.filter(ImageFilter.GaussianBlur(radius=75))
        img.save(output_path, quality=95)
        print(f"[ImageEngine] [THEMATIC VISUAL] Backdrop generated: {output_path}")
