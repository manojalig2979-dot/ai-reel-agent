import textwrap
from pathlib import Path
from typing import List, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import config


class SubtitleEngine:
    def __init__(self, width: int = config.VIDEO_WIDTH, height: int = config.VIDEO_HEIGHT):
        self.width = width
        self.height = height

    def _get_font(self, size: int = 46):
        """Find or load a bold font with full Unicode/Hindi/Devanagari support."""
        font_candidates = [
            # 1. Bundled High-Retention Project Fonts
            config.FONTS_DIR / "Mukta-Bold.ttf",
            config.FONTS_DIR / "NotoSansDevanagari.ttf",
            config.FONTS_DIR / "Poppins-Bold.ttf",
            # 2. Windows Indic Fonts (Hindi, Sanskrit, Marathi, etc.)
            "C:/Windows/Fonts/NirmalaB.ttf",
            "C:/Windows/Fonts/Nirmala.ttf",
            "C:/Windows/Fonts/mangalb.ttf",
            "C:/Windows/Fonts/mangal.ttf",
            "C:/Windows/Fonts/aparajb.ttf",
            "C:/Windows/Fonts/utsaahb.ttf",
            # 3. Linux / Ubuntu System Fonts
            "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf",
            "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            # 4. Standard Fallbacks
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/impact.ttf",
            "C:/Windows/Fonts/arial.ttf"
        ]
        for f in font_candidates:
            p = Path(f)
            if p.exists():
                try:
                    return ImageFont.truetype(str(p), size)
                except Exception:
                    continue
        return ImageFont.load_default()

    def create_subtitle_image(
        self,
        text: str,
        position: str = "bottom",
        highlight_color: str = "#FFE600",
        text_color: str = "#FFFFFF",
        stroke_color: str = "#000000",
        stroke_width: int = 3,
        bg_style: str = "soft_pill"
    ) -> np.ndarray:
        """
        Renders a transparent RGBA image with styled, non-intrusive subtitles.
        Text dynamically scales and adapts to never block or overwhelm the background artwork.
        
        position options: 'bottom' (default), 'center', 'top'
        bg_style options: 'soft_pill' (subtle semi-transparent pill), 'clean_shadow' (stroke only, maximum visual visibility)
        """
        img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Wrap text nicely for 9:16 vertical reels
        display_text = text.upper() if text.isascii() else text
        raw_lines = [l.strip() for l in display_text.split("\n") if l.strip()]
        
        wrapped_lines = []
        for line in raw_lines:
            wrapped = textwrap.wrap(line, width=28)
            wrapped_lines.extend(wrapped)

        if not wrapped_lines:
            return np.array(img)

        # Dynamically calculate font size and line height based on text density
        line_count = len(wrapped_lines)
        if line_count <= 2:
            font_size = 48
            line_height = 68
        elif line_count <= 4:
            font_size = 40
            line_height = 56
        else:
            font_size = 34
            line_height = 46

        font = self._get_font(size=font_size)
        total_text_height = line_count * line_height

        # Position calculation
        pos_lower = position.lower()
        if "top" in pos_lower:
            start_y = int(self.height * 0.18) - (total_text_height // 2)
        elif "center" in pos_lower or "middle" in pos_lower:
            start_y = int(self.height * 0.50) - (total_text_height // 2)
        else:
            # Bottom third (default)
            start_y = int(self.height * 0.76) - (total_text_height // 2)

        start_y = max(60, min(self.height - total_text_height - 60, start_y))

        for i, line in enumerate(wrapped_lines):
            bbox = draw.textbbox((0, 0), line, font=font, stroke_width=stroke_width)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]

            x = (self.width - text_w) // 2
            y = start_y + (i * line_height)

            # Draw subtle backdrop only if requested
            if bg_style == "soft_pill":
                pad_x = 18
                pad_y = 6
                box_rect = [x - pad_x, y - pad_y, x + text_w + pad_x, y + text_h + pad_y]
                # Lightweight translucent dark pill (alpha=130 so background image is clearly visible)
                draw.rounded_rectangle(box_rect, radius=12, fill=(10, 10, 16, 130))

            # Draw text with dark border stroke for razor-sharp legibility
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
    arr = engine.create_subtitle_image("मेरी खामोशियाँ भी एक दास्तान कहती हैं।", position="bottom")
    img = Image.fromarray(arr)
    test_out = config.OUTPUT_DIR / "test_subtitle.png"
    img.save(test_out)
    print(f"Generated subtitle test at: {test_out}")
