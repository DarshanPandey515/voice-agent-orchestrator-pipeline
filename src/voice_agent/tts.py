import os
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs.play import play 

load_dotenv()

client = ElevenLabs(
    api_key=os.environ.get("ELEVENLABS_API_KEY")
)



def audio_play(ai_text):
    audio_stream = client.text_to_speech.stream(
        text=ai_text,
        voice_id="JBFqnCBsd6RMkjVDRZzb",
        model_id="eleven_v3",
        output_format="mp3_44100_128",
    )
    
    return play(audio_stream)

