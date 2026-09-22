import textwrap
from pathlib import Path
from typing import List, Tuple
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import config


class SubtitleEngine:
    def __init__(self, width: int = config.VIDEO_WIDTH, height: int = config.VIDEO_HEIGHT):
        self.width = width
        self.height = height

    def _get_font(self, size: int = 56):
        """Find or load a bold font."""
        font_candidates = [
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/impact.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/calibrib.ttf",
            "C:/Windows/Fonts/arial.ttf"
        ]
        for f in font_candidates:
            if Path(f).exists():
                try:
                    return ImageFont.truetype(f, size)
                except Exception:
                    continue
        return ImageFont.load_default()

    def create_subtitle_image(
        self,
        text: str,
        highlight_color: str = "#FFE600",
        text_color: str = "#FFFFFF",
        stroke_color: str = "#000000",
        stroke_width: int = 4
    ) -> np.ndarray:
        """
        Renders a transparent RGBA image with styled high-retention vertical subtitles.
        Uses Pillow to ensure 100% compatibility on Windows without ImageMagick.
        """
        # Create transparent canvas
        img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        font = self._get_font(size=64)

        # Wrap text nicely for 9:16 vertical reels (around 22-26 chars per line)
        wrapped_lines = textwrap.wrap(text.upper(), width=24)
        if not wrapped_lines:
            return np.array(img)

        # Calculate bounding box and height
        line_height = 80
        total_text_height = len(wrapped_lines) * line_height

        # Position subtitles in the middle-lower third (Y around 68-75% of screen)
        start_y = int(self.height * 0.72) - (total_text_height // 2)

        for i, line in enumerate(wrapped_lines):
            # Compute text width
            bbox = draw.textbbox((0, 0), line, font=font, stroke_width=stroke_width)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]

            x = (self.width - text_w) // 2
            y = start_y + (i * line_height)

            # Draw background pill/box for crisp contrast
            pad_x = 24
            pad_y = 10
            box_rect = [x - pad_x, y - pad_y, x + text_w + pad_x, y + text_h + pad_y]
            
            # Semi-transparent dark pill background
            draw.rounded_rectangle(box_rect, radius=16, fill=(10, 10, 15, 190))

            # Draw text with dark border stroke
            draw.text(
                (x, y),
                line,
                font=font,
                fill=highlight_color if i == 0 else text_color,
                stroke_fill=stroke_color,
                stroke_width=stroke_width
            )

        return np.array(img)


if __name__ == "__main__":
    engine = SubtitleEngine()
    arr = engine.create_subtitle_image("DID YOU KNOW THIS SECRET?")
    img = Image.fromarray(arr)
    test_out = config.OUTPUT_DIR / "test_subtitle.png"
    img.save(test_out)
    print(f"Generated subtitle test at: {test_out}")
