import wave
import struct
import math
import random
import subprocess
from pathlib import Path
import numpy as np
import imageio_ffmpeg
import config


class MusicGenerator:
    """
    Generates seamless, royalty-free background ambient music loops
    procedurally for different video moods using harmonic synthesis.
    """
    SAMPLE_RATE = 44100

    @classmethod
    def generate_track(cls, mood: str = "suspense", duration: float = 45.0, output_filename: str = None) -> Path:
        output_dir = config.MUSIC_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        if not output_filename:
            output_filename = f"{mood.lower().replace(' ', '_')}.mp3"

        wav_temp = output_dir / f"temp_{mood}.wav"
        mp3_final = output_dir / output_filename

        t = np.linspace(0, duration, int(cls.SAMPLE_RATE * duration), endpoint=False)
        audio = np.zeros_like(t)

        if mood == "suspense" or mood == "space":
            # Deep atmospheric ambient drone with minor chords (D minor / A minor)
            freqs = [73.42, 110.0, 146.83, 174.61, 220.0, 440.0]  # D2, A2, D3, F3, A3, A4
            for i, f in enumerate(freqs):
                lfo = 0.5 + 0.5 * np.sin(2 * np.pi * 0.15 * (i + 1) * t)
                audio += 0.2 * np.sin(2 * np.pi * f * t) * lfo
            # Subtle low-frequency pulse
            sub = 0.3 * np.sin(2 * np.pi * 36.71 * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.5 * t))
            audio += sub

        elif mood == "motivation" or mood == "inspiring":
            # Uplifting harmonic progressions (C major / G major / A minor / F major)
            chords = [
                [130.81, 164.81, 196.0, 261.63],   # C major
                [146.83, 174.61, 220.0, 293.66],   # D minor
                [164.81, 196.0, 246.94, 329.63],   # E minor
                [174.61, 220.0, 261.63, 349.23],   # F major
            ]
            section_len = duration / len(chords)
            for idx, chord in enumerate(chords):
                mask = (t >= idx * section_len) & (t < (idx + 1) * section_len)
                for f in chord:
                    audio[mask] += 0.18 * np.sin(2 * np.pi * f * t[mask])
                    audio[mask] += 0.08 * np.sin(2 * np.pi * (f * 2) * t[mask])

        elif mood == "lofi" or mood == "chill":
            # Warm jazzy 7th chords with gentle amplitude modulation
            freqs = [130.81, 155.56, 196.0, 233.08, 311.13]  # C minor 7
            for i, f in enumerate(freqs):
                wobble = 1.0 + 0.003 * np.sin(2 * np.pi * 4.0 * t)
                audio += 0.15 * np.sin(2 * np.pi * f * wobble * t)

        else:  # Cyberpunk synth
            # Pulsing saw-like harmonic waves
            bass_f = 55.0  # A1
            for h in range(1, 6):
                audio += (0.2 / h) * np.sin(2 * np.pi * bass_f * h * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 2.0 * t))

        # Apply smooth master fade-in and fade-out
        fade_samples = int(cls.SAMPLE_RATE * 3.0)
        fade_in = np.linspace(0.0, 1.0, fade_samples)
        fade_out = np.linspace(1.0, 0.0, fade_samples)
        audio[:fade_samples] *= fade_in
        audio[-fade_samples:] *= fade_out

        # Normalize audio volume
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            audio = (audio / max_val) * 0.7

        # Convert to 16-bit PCM WAV
        audio_int16 = (audio * 32767).astype(np.int16)
        with wave.open(str(wav_temp), "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(cls.SAMPLE_RATE)
            wf.writeframes(audio_int16.tobytes())

        # Convert to high-quality MP3 using FFmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        cmd = [
            ffmpeg_exe,
            "-y",
            "-i", str(wav_temp),
            "-c:a", "libmp3lame",
            "-b:a", "192k",
            str(mp3_final)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        # Cleanup temporary WAV
        if wav_temp.exists():
            wav_temp.unlink()

        print(f"[MusicGenerator] [OK] Created background music track: {mp3_final}")
        return mp3_final

    @classmethod
    def generate_all_presets(cls) -> dict:
        """Generates all starter background music tracks."""
        tracks = {}
        for mood in ["suspense", "motivation", "lofi", "cyberpunk"]:
            tracks[mood] = cls.generate_track(mood=mood)
        return tracks


if __name__ == "__main__":
    tracks = MusicGenerator.generate_all_presets()
    print("All preset music tracks generated:", tracks)
