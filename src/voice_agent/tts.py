import asyncio
import threading
import queue
import pyaudio
from elevenlabs.client import ElevenLabs
from elevenlabs import stream
from voice_agent.config import tts_config
from dotenv import load_dotenv

load_dotenv()



class StreamingTTS:
    
    def __init__(self):
        self.client = ElevenLabs(
            api_key=tts_config.api_key
        )
        self.is_playing = False
        self.stop_requested = False


    async def speak(self, text: str) -> None:
        if self.is_playing:
            self.stop_requested = True
            await asyncio.sleep(0.1)
            
        self.stop_requested = False
        self.is_playing = True
        
        try:
            audio_stream = self.client.text_to_speech.stream(
                text=text,
                voice_id=tts_config.voice_id,
                model_id=tts_config.model_id,
                output_format=tts_config.output_format,
            )
            
            p = pyaudio.PyAudio()
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=44100,
                output=True,
                frames_per_buffer=1024,
            )
            
            for chunk in audio_stream:
                if self.stop_requested:
                    break
                stream.write(chunk)
                
            stream.stop_stream()
            stream.close()
            p.terminate()
            
        finally:
            self.is_playing = False
            self.stop_requested = False

    def interrupt(self):
        if self.is_playing:
            self.stop_requested = True