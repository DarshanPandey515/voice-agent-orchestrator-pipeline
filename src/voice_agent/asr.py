import os
import queue
import asyncio
import threading
from dotenv import load_dotenv
from assemblyai.streaming.v3 import (
    RealTimeTranscriber,
    RealTimeTranscriberOptions,
    RealTimeParameters,
    RealTimeEvents,
    TurnEvent,
    BeginEvent,
    RealTimeError,
)
from voice_agent.config import asr_config
import logging


load_dotenv()


logger = logging.getLogger(__name__)


class StreamingASR:
    
    def __init__(self):
        self.transcriber = RealTimeTranscriber(
            options=RealTimeTranscriberOptions(),
            api_key=asr_config.api_key
        )
        
        self.turn_queue = asyncio.Queue()
        self.is_running = False
        self._connected = threading.Event()

        self.transcriber.on(RealTimeEvents.Begin, self.on_open)
        self.transcriber.on(RealTimeEvents.Turn, self.on_turn)
        self.transcriber.on(RealTimeEvents.Error, self.on_error)
    
    
    def on_open(self, client, event: BeginEvent):
        self.is_running = True
        self._connected.set()
        logger.info("session: %s started", event.id)
        

    def on_turn(self, client, event: TurnEvent):
        if event.transcript and event.end_of_turn:
            self.turn_queue.put_nowait(event.transcript)
            logger.info("user: %s", event.transcript)


    def on_error(self, client, error: RealTimeError):
        logger.info("ASR Error: %s", error)
        
    
    def connect(self, timeout: float = 30.0):
        params = RealTimeParameters(
            sample_rate=asr_config.sample_rate,
            speech_model=asr_config.model
        )
        self._connected.clear()
        self.transcriber.connect(params)
        if not self._connected.wait(timeout=timeout):
            raise TimeoutError(
                f"ASR session did not open within {timeout}s"
            )
        
        
    async def get_next_turn(self):
        return await self.turn_queue.get()
    
    
    def stream_audio(self, data):
        if self.is_running:
            self.transcriber.stream(data)
            
            
    def disconnect(self):
        self.is_running = False
        self._connected.clear()
        self.transcriber.disconnect(terminate=True)