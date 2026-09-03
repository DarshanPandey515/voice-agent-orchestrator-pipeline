import os
from dotenv import load_dotenv
from assemblyai.streaming.v3 import (
    RealTimeTranscriber,
    RealTimeTranscriberOptions,
    RealTimeParameters,
)

load_dotenv()

FRAMES_PER_BUFFER = 800
SAMPLE_RATE = 16000

transcriber = RealTimeTranscriber(
    options=RealTimeTranscriberOptions(),
    api_key=os.getenv("ASSEMBLYAI_API_KEY")
)


def connect() -> None:
    transcriber.connect(RealTimeParameters(
        sample_rate=SAMPLE_RATE,
        speech_model="universal-3-5-pro"
    ))