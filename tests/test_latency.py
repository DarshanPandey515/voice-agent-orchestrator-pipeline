import asyncio
import logging
import os
import statistics
import time

import pytest

from voice_agent.config import asr_config, llm_config, tts_config
from voice_agent.llm import LLMAgent

logger = logging.getLogger(__name__)

LLM_ITERATIONS = int(os.getenv("LLM_LATENCY_ITERATIONS", "5"))
TTS_ITERATIONS = int(os.getenv("TTS_LATENCY_ITERATIONS", "5"))
ASR_ITERATIONS = int(os.getenv("ASR_LATENCY_ITERATIONS", "3"))

PROMPT = "What is 2 + 2? Answer in one short sentence."
LONG_PROMPT = (
    "Explain, in a conversational spoken style, what a neural network is, "
    "why depth matters, and give one everyday analogy. Aim for 4-5 sentences."
)
TTS_SENTENCE = "The quick brown fox jumps over the lazy dog."


def _ms(start: float) -> float:
    return (time.perf_counter() - start) * 1000.0


def _measure_real_asr_turn(audio_file: str) -> tuple[float, str | None]:
    """Stream a wav file through real ASR and time speech-end -> transcript.

    Shared by test_asr_turn_latency and the e2e test so both use the exact
    same measurement path. Returns (turn_ms, transcript_or_None).
    """
    import queue as _queue
    import threading
    import wave
    from assemblyai.streaming.v3 import (
        RealTimeEvents,
        RealTimeParameters,
        RealTimeTranscriber,
        RealTimeTranscriberOptions,
    )

    with wave.open(audio_file, "rb") as wf:
        assert wf.getsampwidth() == 2, "expected 16-bit PCM wav"
        frames = wf.readframes(wf.getnframes())
    chunk_size = asr_config.frames_per_buffer * 2
    chunks = [frames[i:i + chunk_size] for i in range(0, len(frames), chunk_size)]

    turns: "_queue.Queue[str]" = _queue.Queue()
    transcriber = RealTimeTranscriber(
        options=RealTimeTranscriberOptions(),
        api_key=asr_config.api_key,
    )
    transcriber.on(RealTimeEvents.Turn, lambda c, e: turns.put(e.transcript))

    begin = threading.Event()
    transcriber.on(RealTimeEvents.Begin, lambda c, e: begin.set())
    transcriber.connect(
        RealTimeParameters(
            sample_rate=asr_config.sample_rate,
            speech_model=asr_config.model,
        )
    )
    if not begin.wait(timeout=30):
        transcriber.disconnect(terminate=True)
        pytest.skip("ASR session did not begin; skipping")

    start = time.perf_counter()
    for chunk in chunks:
        transcriber.stream(chunk)

    transcript = None
    deadline = time.time() + 60
    while time.time() < deadline:
        try:
            transcript = turns.get(timeout=1.0)
            if transcript:
                break
        except _queue.Empty:
            continue
    transcriber.disconnect(terminate=True)

    if not transcript:
        pytest.skip("No transcript produced from audio file")

    return _ms(start), transcript


# ---------------------------------------------------------------- LLM

class TestLLMLatency:
    @pytest.mark.latency
    @pytest.mark.asyncio
    async def test_llm_latency(self, latency_results, require_keys):
        require_keys(["GROQ_API_KEY"])
        llm = LLMAgent()

        for i in range(LLM_ITERATIONS):
            start = time.perf_counter()
            async with llm.agent.run_stream(PROMPT) as result:
                ttft = None
                async for chunk in result.stream_text():
                    if ttft is None:
                        ttft = _ms(start)
                        latency_results.record(
                            component="llm", model=llm_config.model,
                            metric="llm_ttft", ms=ttft,
                        )
                total = _ms(start)
            latency_results.record(
                component="llm", model=llm_config.model,
                metric="llm_total", ms=total,
            )
            output = await result.get_output()
            assert output, "LLM produced no output"
            logger.info(
                "LLM iter %d: ttft=%.1fms total=%.1fms output=%s",
                i, ttft, total, output,
            )

    @pytest.mark.latency
    @pytest.mark.asyncio
    async def test_llm_latency_long(self, latency_results, require_keys):
        """Longer response so TTFT and total have room to diverge.

        On the short PROMPT, ttft ~= total simply because Groq generates
        a 1-3 sentence reply faster than the first network chunk arrives,
        not because timing is broken. This test uses a longer response to
        verify the streaming split is actually working.
        """
        require_keys(["GROQ_API_KEY"])
        llm = LLMAgent()

        for i in range(LLM_ITERATIONS):
            start = time.perf_counter()
            async with llm.agent.run_stream(LONG_PROMPT) as result:
                ttft = None
                async for chunk in result.stream_text():
                    if ttft is None:
                        ttft = _ms(start)
                        latency_results.record(
                            component="llm_long", model=llm_config.model,
                            metric="llm_ttft", ms=ttft,
                        )
                total = _ms(start)
            latency_results.record(
                component="llm_long", model=llm_config.model,
                metric="llm_total", ms=total,
            )
            output = await result.get_output()
            assert output, "LLM produced no output"
            gap = total - ttft if ttft is not None else None
            logger.info(
                "LLM long iter %d: ttft=%.1fms total=%.1fms gap=%.1fms",
                i, ttft, total, gap,
            )

    @pytest.mark.latency
    @pytest.mark.asyncio
    async def test_model_latency(self, latency_results, require_keys):
        require_keys(["GROQ_API_KEY"])
        llm = LLMAgent()
        start = time.perf_counter()
        response = await llm.generate_response(PROMPT)
        total = _ms(start)
        latency_results.record(
            component="model", model=llm_config.model,
            metric="llm_total", ms=total,
        )
        assert response
        logger.info("Model latency: %s total=%.1fms", llm_config.model, total)


# ---------------------------------------------------------------- TTS

class TestTTSLatency:
    @pytest.mark.latency
    def test_tts_latency(self, latency_results, require_keys):
        require_keys(["ELEVENLABS_API_KEY"])
        from voice_agent.tts import StreamingTTS

        tts = StreamingTTS()

        for i in range(TTS_ITERATIONS):
            start = time.perf_counter()
            stream = tts.client.text_to_speech.stream(
                text=TTS_SENTENCE,
                voice_id=tts_config.voice_id,
                model_id=tts_config.model_id,
                output_format=tts_config.output_format,
            )
            first_chunk = None
            total_bytes = 0
            for chunk in stream:
                if first_chunk is None:
                    first_chunk = _ms(start)
                    latency_results.record(
                        component="tts", model=tts_config.model_id,
                        metric="tts_first_chunk", ms=first_chunk,
                    )
                total_bytes += len(chunk)
            total = _ms(start)
            latency_results.record(
                component="tts", model=tts_config.model_id,
                metric="tts_total", ms=total,
            )
            audio_seconds = total_bytes / 2 / tts_config.sample_rate
            latency_results.record(
                component="tts", model=tts_config.model_id,
                metric="tts_audio_rate",
                ms=total / audio_seconds if audio_seconds else 0.0,
            )
            assert total_bytes > 0, "TTS produced no audio"
            logger.info(
                "TTS iter %d: first_chunk=%.1fms total=%.1fms bytes=%d",
                i, first_chunk, total, total_bytes,
            )


# ---------------------------------------------------------------- ASR

class TestASRLatency:
    @pytest.mark.latency
    def test_asr_connect_latency(self, latency_results, require_keys):
        require_keys(["ASSEMBLYAI_API_KEY"])
        import threading
        from assemblyai.streaming.v3 import (
            RealTimeEvents,
            RealTimeParameters,
            RealTimeTranscriber,
            RealTimeTranscriberOptions,
        )

        connect_times = []
        for i in range(ASR_ITERATIONS):
            begin = threading.Event()

            transcriber = RealTimeTranscriber(
                options=RealTimeTranscriberOptions(),
                api_key=asr_config.api_key,
            )
            transcriber.on(RealTimeEvents.Begin, lambda c, e: begin.set())

            start = time.perf_counter()
            transcriber.connect(
                RealTimeParameters(
                    sample_rate=asr_config.sample_rate,
                    speech_model=asr_config.model,
                )
            )
            if not begin.wait(timeout=30):
                transcriber.disconnect(terminate=True)
                pytest.skip("ASR session did not begin; skipping")
            connect_ms = _ms(start)
            connect_times.append(connect_ms)
            latency_results.record(
                component="asr", model=asr_config.model,
                metric="asr_connect", ms=connect_ms,
            )
            transcriber.disconnect(terminate=True)
            logger.info("ASR connect iter %d: %.1fms", i, connect_ms)

        assert len(connect_times) == ASR_ITERATIONS

    @pytest.mark.latency
    def test_asr_turn_latency(self, latency_results, require_keys):
        audio_file = os.getenv("ASR_AUDIO_FILE")
        if not audio_file:
            pytest.skip("Set ASR_AUDIO_FILE=<path to speech wav> to measure STT turn latency")
        require_keys(["ASSEMBLYAI_API_KEY"])

        turn_ms, transcript = _measure_real_asr_turn(audio_file)
        latency_results.record(
            component="asr", model=asr_config.model,
            metric="asr_turn", ms=turn_ms,
        )
        logger.info("ASR turn latency: %.1fms transcript=%s", turn_ms, transcript)


# ---------------------------------------------------------------- E2E

class TestEndToEndLatency:
    @pytest.mark.latency
    @pytest.mark.asyncio
    async def test_e2e_pipeline_latency(self, latency_results, require_keys):
        """Speech-to-speech pipeline latency.

        If ASR_AUDIO_FILE is set, real ASR turn latency (speech-end ->
        final transcript) is measured and folded into the total, giving a
        true "user stops talking -> audio starts playing" number. Without
        it, ASR is mocked at 0ms and the result is a best-case LLM+TTS-only
        floor -- NOT representative of real speech-to-speech latency.
        """
        require_keys(["GROQ_API_KEY", "ELEVENLABS_API_KEY"])

        audio_file = os.getenv("ASR_AUDIO_FILE")
        asr_turn_ms = 0.0

        if audio_file:
            require_keys(["ASSEMBLYAI_API_KEY"])
            asr_turn_ms, transcribed_text = _measure_real_asr_turn(audio_file)
            latency_results.record(
                component="e2e", model=asr_config.model,
                metric="e2e_asr_turn", ms=asr_turn_ms,
            )
            user_text_fixed = transcribed_text or PROMPT
        else:
            logger.warning(
                "ASR_AUDIO_FILE not set -- e2e_pipeline excludes real ASR "
                "turn latency and is a best-case LLM+TTS floor, not a true "
                "speech-to-speech number."
            )
            user_text_fixed = PROMPT

        class FakeASR:
            async def get_next_turn(self):
                await asyncio.sleep(0)
                return user_text_fixed

        from voice_agent.llm import LLMAgent
        from voice_agent.tts import StreamingTTS

        llm = LLMAgent()
        tts = StreamingTTS()
        asr = FakeASR()

        for i in range(LLM_ITERATIONS):
            user_text = await asr.get_next_turn()
            # Start the clock from end-of-speech, not from LLM call, so the
            # recorded e2e figure includes ASR turn time when available.
            start = time.perf_counter() - (asr_turn_ms / 1000.0)

            ttft = None
            async with llm.agent.run_stream(user_text) as result:
                async for chunk in result.stream_text():
                    if ttft is None:
                        ttft = _ms(start)
                        break
            llm_total = _ms(start)
            output = await result.get_output()

            tts_start = time.perf_counter()
            audio_stream = tts.client.text_to_speech.stream(
                text=output,
                voice_id=tts_config.voice_id,
                model_id=tts_config.model_id,
                output_format=tts_config.output_format,
            )
            first_audio = None
            for chunk in audio_stream:
                if first_audio is None:
                    first_audio = _ms(tts_start)
                break

            speak_latency = _ms(start)
            latency_results.record(
                component="e2e", model=llm_config.model,
                metric="e2e_pipeline", ms=speak_latency,
            )
            logger.info(
                "E2E iter %d: llm_total=%.1fms ttft=%.1fms tts_first=%.1fms -> speak in %.1fms",
                i, llm_total, ttft, first_audio, speak_latency,
            )

            samples = latency_results.get("e2e", "e2e_pipeline")
            assert samples, "no e2e samples recorded"