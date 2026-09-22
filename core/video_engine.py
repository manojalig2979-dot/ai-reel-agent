import os
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from PIL import Image
import imageio_ffmpeg
import config
from core.subtitle_engine import SubtitleEngine


class VideoEngine:
    def __init__(
        self,
        width: int = config.VIDEO_WIDTH,
        height: int = config.VIDEO_HEIGHT,
        fps: int = 30
    ):
        self.width = width
        self.height = height
        self.fps = fps
        self.subtitle_engine = SubtitleEngine(width, height)
        self.ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    def get_audio_duration(self, audio_path: Path) -> float:
        """Extracts exact audio duration in seconds using FFmpeg."""
        cmd = [
            self.ffmpeg_exe,
            "-i", str(audio_path),
            "-f", "null", "-"
        ]
        try:
            res = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, check=False)
            import re
            match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", res.stderr)
            if match:
                hours, minutes, seconds = match.groups()
                return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
        except Exception:
            pass
        return 4.5

    def render_scene_ffmpeg(
        self,
        image_path: Path,
        audio_path: Path,
        subtitle_png_path: Path,
        output_scene_path: Path,
        duration: float,
        scene_idx: int = 0,
        text_animation: str = "static",
        watermark_path: Optional[Path] = None,
        watermark_opacity: float = 0.88
    ) -> Path:
        """
        Renders an animated vertical scene with Ken Burns zoom + dynamic subtitles + creator logo watermark.
        Supports motion animations: 'static', 'scroll_up', 'scroll_down', 'float_up'.
        """
        frames = int(duration * self.fps)
        zoom_speed = 0.0012

        if scene_idx % 2 == 0:
            zoom_expr = f"min(zoom+{zoom_speed}, 1.15)"
            x_expr = "iw/2-(iw/zoom/2)"
            y_expr = "ih/2-(ih/zoom/2)"
        else:
            zoom_expr = f"max(1.15-(on*{zoom_speed}), 1.0)"
            x_expr = "iw/2-(iw/zoom/2)"
            y_expr = "ih/2-(ih/zoom/2)"

        # Text motion overlay calculation
        anim = text_animation.lower()
        if anim in ["scroll_up", "bottom_to_top", "scroll_bottom_to_top"]:
            sub_overlay = f"overlay=0:'H-(H+overlay_h)*(t/{duration:.3f})':eval=frame"
        elif anim in ["scroll_down", "top_to_bottom", "scroll_top_to_bottom"]:
            sub_overlay = f"overlay=0:'-overlay_h+(H+overlay_h)*(t/{duration:.3f})':eval=frame"
        elif anim in ["float_up", "floating", "float"]:
            sub_overlay = f"overlay=0:'0-45*(t/{duration:.3f})':eval=frame"
        else:
            sub_overlay = "overlay=0:0"

        has_watermark = watermark_path and Path(watermark_path).exists()

        if has_watermark:
            filter_complex = (
                f"[0:v]scale=1200:2133:force_original_aspect_ratio=increase,crop=1200:2133,"
                f"zoompan=z='{zoom_expr}':d={frames}:x='{x_expr}':y='{y_expr}':s={self.width}x{self.height}:fps={self.fps}[bg];"
                f"[1:v]scale={self.width}:{self.height}[sub];"
                f"[3:v]scale=130:130,format=rgba,colorchannelmixer=aa={watermark_opacity}[wm];"
                f"[bg][sub]{sub_overlay}[v1];"
                f"[v1][wm]overlay=48:64:format=auto[v]"
            )
            cmd = [
                self.ffmpeg_exe,
                "-y",
                "-loop", "1", "-i", str(image_path),
                "-i", str(subtitle_png_path),
                "-i", str(audio_path),
                "-i", str(watermark_path),
                "-filter_complex", filter_complex,
                "-map", "[v]",
                "-map", "2:a",
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "192k",
                "-t", f"{duration:.3f}",
                str(output_scene_path)
            ]
        else:
            filter_complex = (
                f"[0:v]scale=1200:2133:force_original_aspect_ratio=increase,crop=1200:2133,"
                f"zoompan=z='{zoom_expr}':d={frames}:x='{x_expr}':y='{y_expr}':s={self.width}x{self.height}:fps={self.fps}[bg];"
                f"[1:v]scale={self.width}:{self.height}[sub];"
                f"[bg][sub]{sub_overlay}[v]"
            )
            cmd = [
                self.ffmpeg_exe,
                "-y",
                "-loop", "1", "-i", str(image_path),
                "-i", str(subtitle_png_path),
                "-i", str(audio_path),
                "-filter_complex", filter_complex,
                "-map", "[v]",
                "-map", "2:a",
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "192k",
                "-t", f"{duration:.3f}",
                str(output_scene_path)
            ]

        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return output_scene_path

    def assemble_reel(
        self,
        scenes_data: List[Dict[str, Any]],
        output_path: Path,
        bg_music_path: Optional[Path] = None,
        bg_music_volume: float = 0.12,
        text_position: str = "bottom",
        text_animation: str = "static",
        text_style: str = "soft_pill",
        watermark_path: Optional[Path] = None
    ) -> Path:
        """
        Renders all scenes with Ken Burns + customizable subtitle placement/animation + watermark and concatenates with optional music.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        temp_dir = output_path.parent / "temp_scenes"
        temp_dir.mkdir(parents=True, exist_ok=True)

        scene_files = []
        print(f"[VideoEngine] Rendering {len(scenes_data)} scenes (motion: {text_animation}, position: {text_position})...")

        for idx, scene in enumerate(scenes_data):
            img_path = Path(scene["image_path"])
            aud_path = Path(scene["audio_path"])
            text = scene.get("narration", "")

            # 1. Audio duration
            duration = self.get_audio_duration(aud_path)

            # 2. Subtitle overlay with chosen position and non-intrusive styling
            sub_arr = self.subtitle_engine.create_subtitle_image(
                text=text,
                position=text_position,
                bg_style=text_style
            )
            sub_png = temp_dir / f"sub_{idx}.png"
            Image.fromarray(sub_arr).save(sub_png)

            # 3. Render Scene MP4 with animation
            scene_mp4 = temp_dir / f"scene_{idx}.mp4"
            self.render_scene_ffmpeg(
                image_path=img_path,
                audio_path=aud_path,
                subtitle_png_path=sub_png,
                output_scene_path=scene_mp4,
                duration=duration,
                scene_idx=idx,
                text_animation=text_animation,
                watermark_path=watermark_path
            )
            scene_files.append(scene_mp4)

        # 4. Concatenate scenes
        concat_txt = temp_dir / "concat_list.txt"
        with open(concat_txt, "w", encoding="utf-8") as f:
            for s in scene_files:
                f.write(f"file '{s.as_posix()}'\n")

        raw_stitched = temp_dir / "raw_stitched.mp4" if bg_music_path else output_path

        concat_cmd = [
            self.ffmpeg_exe,
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_txt),
            "-c", "copy",
            str(raw_stitched)
        ]
        subprocess.run(concat_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        # 5. Mix Background Music if provided
        if bg_music_path and Path(bg_music_path).exists():
            print(f"[VideoEngine] Mixing background music track: {bg_music_path} (volume: {bg_music_volume})...")
            mix_filter = (
                f"[0:a]volume=1.0[voice];"
                f"[1:a]volume={bg_music_volume},aloop=loop=-1:size=2e+09[music];"
                f"[voice][music]amix=inputs=2:duration=first:dropout_transition=2[aout]"
            )
            music_cmd = [
                self.ffmpeg_exe,
                "-y",
                "-i", str(raw_stitched),
                "-i", str(bg_music_path),
                "-filter_complex", mix_filter,
                "-map", "0:v",
                "-map", "[aout]",
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                str(output_path)
            ]
            subprocess.run(music_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        print(f"[VideoEngine] [SUCCESS] Final 9:16 vertical Reel rendered: {output_path}")
        return output_path
