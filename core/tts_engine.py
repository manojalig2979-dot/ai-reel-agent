import asyncio
import os
from pathlib import Path
from typing import Optional, Tuple
import config

try:
    import edge_tts
except ImportError:
    edge_tts = None


class TTSEngine:
    def __init__(self, default_voice: str = None):
        self.default_voice = default_voice or config.DEFAULT_VOICE

    async def _generate_audio_async(self, text: str, output_path: Path, voice: str) -> None:
        """Asynchronously call edge-tts and save to output_path."""
        if not edge_tts:
            raise ImportError("edge-tts library is not installed. Please run 'pip install edge-tts'.")
        
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(output_path))

    def generate_voiceover(
        self,
        text: str,
        output_path: Path,
        voice: Optional[str] = None
    ) -> Path:
        """Synchronous wrapper to generate voiceover MP3."""
        selected_voice = voice or self.default_voice
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Check if event loop is running
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                # In an environment with an active loop (e.g., notebooks or certain frameworks)
                import nest_asyncio
                nest_asyncio.apply()
                asyncio.run(self._generate_audio_async(text, output_path, selected_voice))
            else:
                asyncio.run(self._generate_audio_async(text, output_path, selected_voice))

            print(f"[TTSEngine] Generated voiceover: {output_path} with voice: {selected_voice}")
            return output_path

        except Exception as e:
            print(f"[TTSEngine] Error generating voiceover: {e}")
            raise


if __name__ == "__main__":
    engine = TTSEngine()
    test_out = config.OUTPUT_DIR / "test_voice.mp3"
    engine.generate_voiceover("Welcome to the automated AI Reel generator!", test_out)
    print(f"Generated at: {test_out}")
