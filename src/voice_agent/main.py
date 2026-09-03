import asyncio
import pyaudio
from voice_agent.asr import StreamingASR
from voice_agent.llm import LLMAgent
from voice_agent.tts import StreamingTTS
from voice_agent.config import asr_config
import logging


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

logger = logging.getLogger(__name__)


class VoiceAgent:
    def __init__(self):
        self.asr = StreamingASR()
        self.llm = LLMAgent()
        self.tts = StreamingTTS()
        self.is_running = False
    
    async def process_turns(self):
        while self.is_running:
            try:
                user_text = await self.asr.get_next_turn()
                
                if self.tts.is_playing:
                    self.tts.interrupt()
                
                response = await self.llm.generate_response(user_text)
                logger.info("Assistant: %s", response)
                
                await self.tts.speak(response)
                
            except asyncio.CancelledError:
                break
            
            except Exception as e:
                logger.debug("Processing error: %s", e)
    
    async def run(self):
        self.is_running = True
        self.asr.connect()
        
        p = pyaudio.PyAudio()
        audio_stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=asr_config.sample_rate,
            input=True,
            frames_per_buffer=asr_config.frames_per_buffer,
        )
        
        logger.info("Listening... Speak into your mic. Press Ctrl+C to stop.")
                
        try:
            processor_task = asyncio.create_task(self.process_turns())
            
            while self.is_running:
                try:
                    data = audio_stream.read(
                        asr_config.frames_per_buffer,
                        exception_on_overflow=False
                    )
                    self.asr.stream_audio(data)
                    await asyncio.sleep(0.001)
                    
                except KeyboardInterrupt:
                    break
                
        finally:
            self.is_running = False
            audio_stream.stop_stream()
            audio_stream.close()
            p.terminate()
            self.asr.disconnect()
            processor_task.cancel()
            await processor_task

def main():
    agent = VoiceAgent()
    asyncio.run(agent.run())

if __name__ == "__main__":
    main()