import wave
import struct
import math
import subprocess
from pathlib import Path
import numpy as np
import imageio_ffmpeg
import config


class MusicGenerator:
    """
    Generates seamless, royalty-free background ambient music loops
    procedurally for different video moods including Devotional / Spiritual.
    """
    SAMPLE_RATE = 44100

    @classmethod
    def generate_track(cls, mood: str = "spiritual", duration: float = 45.0, output_filename: str = None) -> Path:
        output_dir = config.MUSIC_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        if not output_filename:
            output_filename = f"{mood.lower().replace(' ', '_')}.mp3"

        wav_temp = output_dir / f"temp_{mood}.wav"
        mp3_final = output_dir / output_filename

        t = np.linspace(0, duration, int(cls.SAMPLE_RATE * duration), endpoint=False)
        audio = np.zeros_like(t)

        if mood == "spiritual" or mood == "meditative" or mood == "geeta":
            # Soothing Indian Classical Tanpura Drone (Sa-Pa fundamental in C# / D: 138.59 Hz, 207.65 Hz)
            # Gentle meditative harmonic overtone swells
            sa = 138.59  # C#3
            pa = 207.65  # G#3
            sa_high = 277.18 # C#4
            
            # Tanpura Drone Pluck simulation
            for i, f in enumerate([sa, pa, sa_high, sa/2]):
                lfo = 0.5 + 0.5 * np.sin(2 * np.pi * 0.12 * (i + 1) * t)
                audio += 0.25 * np.sin(2 * np.pi * f * t) * lfo
                audio += 0.10 * np.sin(2 * np.pi * (f * 2) * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.08 * t))

            # Warm Bansuri / Flute harmonic air resonance
            flute_freqs = [277.18, 311.13, 369.99, 415.30, 466.16]
            for idx, ff in enumerate(flute_freqs):
                section_len = duration / len(flute_freqs)
                mask = (t >= idx * section_len) & (t < (idx + 1) * section_len)
                vibrato = 1.0 + 0.005 * np.sin(2 * np.pi * 5.0 * t[mask])
                audio[mask] += 0.18 * np.sin(2 * np.pi * ff * vibrato * t[mask])

        elif mood == "suspense" or mood == "space":
            freqs = [73.42, 110.0, 146.83, 174.61, 220.0, 440.0]
            for i, f in enumerate(freqs):
                lfo = 0.5 + 0.5 * np.sin(2 * np.pi * 0.15 * (i + 1) * t)
                audio += 0.2 * np.sin(2 * np.pi * f * t) * lfo
            sub = 0.3 * np.sin(2 * np.pi * 36.71 * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.5 * t))
            audio += sub

        elif mood == "motivation" or mood == "inspiring":
            chords = [
                [130.81, 164.81, 196.0, 261.63],
                [146.83, 174.61, 220.0, 293.66],
                [164.81, 196.0, 246.94, 329.63],
                [174.61, 220.0, 261.63, 349.23],
            ]
            section_len = duration / len(chords)
            for idx, chord in enumerate(chords):
                mask = (t >= idx * section_len) & (t < (idx + 1) * section_len)
                for f in chord:
                    audio[mask] += 0.18 * np.sin(2 * np.pi * f * t[mask])
                    audio[mask] += 0.08 * np.sin(2 * np.pi * (f * 2) * t[mask])

        elif mood == "poetry_piano" or mood == "piano":
            # Soulful, melancholic piano chord progression: Am -> F -> C -> G
            progression = [
                [220.0, 261.63, 329.63],         # Am (A3, C4, E4)
                [174.61, 220.0, 261.63, 349.23], # F  (F3, A3, C4, F4)
                [130.81, 164.81, 196.0, 261.63], # C  (C3, E3, G3, C4)
                [196.0, 246.94, 293.66, 392.0],  # G  (G3, B3, D4, G4)
            ]
            section_len = duration / len(progression)
            for idx, chord in enumerate(progression):
                mask = (t >= idx * section_len) & (t < (idx + 1) * section_len)
                sub_t = t[mask] - (idx * section_len)
                decay = np.exp(-sub_t * 0.4)
                for f in chord:
                    audio[mask] += 0.22 * np.sin(2 * np.pi * f * t[mask]) * decay
                    audio[mask] += 0.08 * np.sin(2 * np.pi * (f * 2) * t[mask]) * decay

        elif mood == "acoustic_strings" or mood == "nostalgia":
            # Warm acoustic ambient pads & slow melodic strings
            string_freqs = [146.83, 220.0, 293.66, 329.63, 440.0]
            for i, f in enumerate(string_freqs):
                swell = 0.5 + 0.5 * np.sin(2 * np.pi * 0.08 * (i + 1) * t)
                audio += 0.16 * np.sin(2 * np.pi * f * t) * swell

        else:
            bass_f = 55.0
            for h in range(1, 6):
                audio += (0.2 / h) * np.sin(2 * np.pi * bass_f * h * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 2.0 * t))

        # Fade in / fade out
        fade_samples = int(cls.SAMPLE_RATE * 3.0)
        fade_in = np.linspace(0.0, 1.0, fade_samples)
        fade_out = np.linspace(1.0, 0.0, fade_samples)
        audio[:fade_samples] *= fade_in
        audio[-fade_samples:] *= fade_out

        max_val = np.max(np.abs(audio))
        if max_val > 0:
            audio = (audio / max_val) * 0.7

        audio_int16 = (audio * 32767).astype(np.int16)
        with wave.open(str(wav_temp), "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(cls.SAMPLE_RATE)
            wf.writeframes(audio_int16.tobytes())

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

        if wav_temp.exists():
            wav_temp.unlink()

        print(f"[MusicGenerator] [OK] Created track: {mp3_final}")
        return mp3_final

    @classmethod
    def generate_all_presets(cls) -> dict:
        tracks = {}
        for mood in ["spiritual", "suspense", "motivation", "lofi", "cyberpunk"]:
            tracks[mood] = cls.generate_track(mood=mood)
        return tracks


if __name__ == "__main__":
    MusicGenerator.generate_all_presets()
