from kvf.models.application import Application
from kvf.models.voice import Voice
from kvf.providers.edge_tts_provider import EdgeTTSProvider
from kvf.repositories.script_repository import ScriptRepository
from kvf.repositories.voice_repository import VoiceRepository
from kvf.steps.base_step import BaseStep


class GenerateVoiceStep(BaseStep):

    def execute(
        self,
        application: Application,
    ):

        workspace = application.project.workspace

        output_dir = workspace / "voice"

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        audio_path = output_dir / "narration.mp3"

        metadata_path = output_dir / "voice.json"

        if audio_path.exists():
            print(
                "Voice already exists. [SKIP]"
            )
            return

        script = ScriptRepository().load(
            workspace
            / "script"
            / "script.json"
        )

        narration = []

        for section in script.sections:

            narration.append(
                section.narration
            )

        text = "\n\n".join(
            narration
        )

        provider = EdgeTTSProvider()

        provider.generate(
            text,
            audio_path,
        )

        voice = Voice(
            provider="edge_tts",
            voice="en-US-AndrewNeural",
            file=audio_path.name,
        )

        VoiceRepository().save(
            voice,
            metadata_path,
        )

        print(
            f"Voice generated: {audio_path}"
        )