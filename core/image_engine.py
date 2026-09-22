import os
import sys
import random
import urllib.parse
from pathlib import Path
from typing import Optional
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
        seed: Optional[int] = None
    ) -> Path:
        """
        Fetches vertical 9:16 image using multi-tier free endpoints:
        Tier 1: Pollinations AI
        Tier 2: High-definition vertical curated imagery
        Tier 3: Procedural dynamic cinematic graphic generator
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if seed is None:
            seed = random.randint(1000, 999999)

        # 1. Attempt Pollinations AI
        clean_prompt = prompt.strip().replace("\n", " ")
        encoded = urllib.parse.quote(f"{clean_prompt}, cinematic, 8k, vertical 9:16")
        pollinations_url = f"https://image.pollinations.ai/prompt/{encoded}?width={self.width}&height={self.height}&seed={seed}&nologo=true"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        try:
            res = requests.get(pollinations_url, headers=headers, timeout=8)
            if res.status_code == 200 and len(res.content) > 10000 and b"<!DOCTYPE html>" not in res.content[:100]:
                with open(output_path, "wb") as f:
                    f.write(res.content)
                with Image.open(output_path) as img:
                    img.verify()
                print(f"[ImageEngine] [OK] Pollinations AI image downloaded: {output_path}")
                return output_path
        except Exception:
            pass

        # 2. Free High-Res Vertical Backdrops
        try:
            keywords = [w for w in clean_prompt.split() if len(w) > 3][:2]
            kw_query = ",".join(keywords) if keywords else "space,dark"
            res2 = requests.get(f"https://picsum.photos/1080/1920?random={seed}", headers=headers, timeout=8)
            if res2.status_code == 200 and len(res2.content) > 10000:
                with open(output_path, "wb") as f:
                    f.write(res2.content)
                print(f"[ImageEngine] [OK] Vertical image downloaded: {output_path}")
                return output_path
        except Exception:
            pass

        # 3. Procedural Cinematic Vertical Visual (100% Reliable Offline Fallback)
        self._generate_cinematic_fallback(clean_prompt, output_path, seed)
        return output_path

    def _generate_cinematic_fallback(self, prompt: str, output_path: Path, seed: int) -> None:
        """Procedurally renders a rich, high-aesthetic cinematic backdrop."""
        random.seed(seed)
        
        # Select harmonious modern palette
        palettes = [
            [(15, 12, 41), (48, 43, 99), (36, 36, 62)],      # Deep Cosmic Purple
            [(10, 24, 40), (20, 50, 80), (10, 80, 100)],     # Cyber Deep Ocean
            [(20, 10, 30), (70, 20, 60), (140, 45, 80)],    # Neon Cyberpunk Sunset
            [(18, 18, 24), (32, 38, 57), (40, 60, 80)]       # Sleek Tech Stealth
        ]
        chosen_palette = random.choice(palettes)

        # Base canvas
        img = Image.new("RGB", (self.width, self.height), color=chosen_palette[0])
        draw = ImageDraw.Draw(img)

        # Vertical Gradient
        steps = 60
        for i in range(steps):
            t = i / steps
            if t < 0.5:
                blend = t * 2
                c = [int(chosen_palette[0][k]*(1-blend) + chosen_palette[1][k]*blend) for k in range(3)]
            else:
                blend = (t - 0.5) * 2
                c = [int(chosen_palette[1][k]*(1-blend) + chosen_palette[2][k]*blend) for k in range(3)]
            
            y0 = int(i * (self.height / steps))
            y1 = int((i + 1) * (self.height / steps))
            draw.rectangle([0, y0, self.width, y1], fill=tuple(c))

        # Add luminous ambient orbs / light bursts for depth
        for _ in range(4):
            cx = random.randint(100, self.width - 100)
            cy = random.randint(200, self.height - 200)
            radius = random.randint(200, 400)
            glow_col = (
                random.randint(100, 255),
                random.randint(100, 255),
                random.randint(150, 255)
            )
            draw.ellipse(
                [cx - radius, cy - radius, cx + radius, cy + radius],
                fill=glow_col
            )

        # Apply rich blur for smooth cinematic lighting
        img = img.filter(ImageFilter.GaussianBlur(radius=60))

        img.save(output_path, quality=95)
        print(f"[ImageEngine] [OK] Cinematic procedural backdrop generated at {output_path}")
