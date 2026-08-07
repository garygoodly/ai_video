from kvf.models.application import Application
from kvf.models.voice import Voice
from kvf.providers.edge_tts_provider import EdgeTTSProvider
from kvf.repositories.script_repository import ScriptRepository
from kvf.repositories.voice_repository import VoiceRepository
from kvf.services.session_service import SessionService
from kvf.steps.base_step import BaseStep


class GenerateVoiceStep(BaseStep):
    def execute(self, application: Application) -> None:
        workspace = application.project.workspace
        output_dir = workspace / "voice"
        output_dir.mkdir(parents=True, exist_ok=True)
        audio_path = output_dir / "narration.mp3"
        metadata_path = output_dir / "voice.json"

        if audio_path.exists():
            print("Voice already exists. [SKIP]")
            return

        script = ScriptRepository().load(workspace / "script" / "script.json")
        text = "\n\n".join(section.narration for section in script.sections)
        metadata = SessionService._read_metadata(workspace)
        voice_name = metadata.get("voice", "en-US-AndrewNeural")
        voice_rate = metadata.get("voice_rate", "+0%")
        voice_pitch = metadata.get("voice_pitch", "+0Hz")

        EdgeTTSProvider(
            voice=voice_name, rate=voice_rate, pitch=voice_pitch
        ).generate(text, audio_path)
        VoiceRepository().save(
            Voice(provider="edge_tts", voice=voice_name, file=audio_path.name),
            metadata_path,
        )
        print(
            f"Voice generated with {voice_name}, rate {voice_rate}, "
            f"pitch {voice_pitch}: {audio_path}"
        )
