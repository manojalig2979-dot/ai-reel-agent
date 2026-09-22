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
        watermark_path: Optional[Path] = None,
        watermark_opacity: float = 0.88
    ) -> Path:
        """
        Renders an animated vertical scene with Ken Burns zoom + subtitles + creator logo watermark.
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

        has_watermark = watermark_path and Path(watermark_path).exists()

        if has_watermark:
            filter_complex = (
                f"[0:v]scale=1200:2133:force_original_aspect_ratio=increase,crop=1200:2133,"
                f"zoompan=z='{zoom_expr}':d={frames}:x='{x_expr}':y='{y_expr}':s={self.width}x{self.height}:fps={self.fps}[bg];"
                f"[1:v]scale={self.width}:{self.height}[sub];"
                f"[3:v]scale=130:130,format=rgba,colorchannelmixer=aa={watermark_opacity}[wm];"
                f"[bg][sub]overlay=0:0[v1];"
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
                f"[bg][sub]overlay=0:0:format=auto[v]"
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
        watermark_path: Optional[Path] = None
    ) -> Path:
        """
        Renders all scenes with Ken Burns + subtitles + watermark and concatenates into final MP4 with optional music.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        temp_dir = output_path.parent / "temp_scenes"
        temp_dir.mkdir(parents=True, exist_ok=True)

        scene_files = []
        print(f"[VideoEngine] Rendering {len(scenes_data)} scenes via high-speed FFmpeg engine...")

        for idx, scene in enumerate(scenes_data):
            img_path = Path(scene["image_path"])
            aud_path = Path(scene["audio_path"])
            text = scene.get("narration", "")

            # 1. Exact audio duration
            duration = self.get_audio_duration(aud_path)

            # 2. Subtitle overlay
            sub_arr = self.subtitle_engine.create_subtitle_image(text)
            sub_png = temp_dir / f"sub_{idx}.png"
            Image.fromarray(sub_arr).save(sub_png)

            # 3. Render Scene MP4 with watermark
            scene_mp4 = temp_dir / f"scene_{idx}.mp4"
            self.render_scene_ffmpeg(
                image_path=img_path,
                audio_path=aud_path,
                subtitle_png_path=sub_png,
                output_scene_path=scene_mp4,
                duration=duration,
                scene_idx=idx,
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
