# Voice Agent Latency Report

_Generated: 2026-09-04 16:06 UTC | Results: `reports/latency_results.json`_

## Summary

| Component | Model | Metric | Samples | Min | Mean | Median (p50) | p95 | Max | Std dev |
|---|---|---|---|---|---|---|---|---|---|
| Speech-to-Text (AssemblyAI) | `universal-3-5-pro` | WebSocket connect | 1 | 1463.3 ms | 1463.3 ms | 1463.3 ms | 1463.3 ms | 1463.3 ms | 0.0 ms |
| End-to-end pipeline | `groq:openai/gpt-oss-20b` | User turn -> audio plays | 5 | 4519.0 ms | 5004.3 ms | 4656.4 ms | 6012.6 ms | 6012.6 ms | 627.6 ms |
| End-to-end pipeline | `universal-3-5-pro` | e2e_asr_turn | 1 | 3793.4 ms | 3793.4 ms | 3793.4 ms | 3793.4 ms | 3793.4 ms | 0.0 ms |
| LLM (Groq) | `groq:openai/gpt-oss-20b` | Full response | 5 | 397.2 ms | 680.0 ms | 612.6 ms | 1260.5 ms | 1260.5 ms | 340.2 ms |
| LLM (Groq) | `groq:openai/gpt-oss-20b` | Time-to-first-token (TTFT) | 5 | 395.7 ms | 652.4 ms | 479.1 ms | 1259.6 ms | 1259.6 ms | 351.8 ms |
| llm_long | `groq:openai/gpt-oss-20b` | Full response | 5 | 572.7 ms | 835.9 ms | 833.3 ms | 1103.6 ms | 1103.6 ms | 217.0 ms |
| llm_long | `groq:openai/gpt-oss-20b` | Time-to-first-token (TTFT) | 5 | 525.3 ms | 791.0 ms | 790.9 ms | 1096.6 ms | 1096.6 ms | 238.4 ms |
| Model inference | `groq:openai/gpt-oss-20b` | Full response | 1 | 741.2 ms | 741.2 ms | 741.2 ms | 741.2 ms | 741.2 ms | 0.0 ms |
| Text-to-Speech (ElevenLabs) | `eleven_flash_v2_5` | Synthesis real-time factor (x) | 5 | 98.59x | 167.04x | 154.76x | 277.26x | 277.26x | 70.33x |
| Text-to-Speech (ElevenLabs) | `eleven_flash_v2_5` | Time-to-first-audio-chunk | 5 | 194.4 ms | 334.4 ms | 254.3 ms | 691.0 ms | 691.0 ms | 207.5 ms |
| Text-to-Speech (ElevenLabs) | `eleven_flash_v2_5` | Full synthesis | 5 | 279.3 ms | 465.3 ms | 431.2 ms | 772.6 ms | 772.6 ms | 195.8 ms |

## Component Breakdown

### Speech-to-Text (AssemblyAI)

- **WebSocket connect** (`universal-3-5-pro`): mean 1463.3 ms, p50 1463.3 ms, p95 1463.3 ms (n=1, range 1463.3 ms–1463.3 ms)
### End-to-end pipeline

- **User turn -> audio plays** (`groq:openai/gpt-oss-20b`): mean 5004.3 ms, p50 4656.4 ms, p95 6012.6 ms (n=5, range 4519.0 ms–6012.6 ms)
- **e2e_asr_turn** (`universal-3-5-pro`): mean 3793.4 ms, p50 3793.4 ms, p95 3793.4 ms (n=1, range 3793.4 ms–3793.4 ms)
### LLM (Groq)

- **Full response** (`groq:openai/gpt-oss-20b`): mean 680.0 ms, p50 612.6 ms, p95 1260.5 ms (n=5, range 397.2 ms–1260.5 ms)
- **Time-to-first-token (TTFT)** (`groq:openai/gpt-oss-20b`): mean 652.4 ms, p50 479.1 ms, p95 1259.6 ms (n=5, range 395.7 ms–1259.6 ms)
### llm_long

- **Full response** (`groq:openai/gpt-oss-20b`): mean 835.9 ms, p50 833.3 ms, p95 1103.6 ms (n=5, range 572.7 ms–1103.6 ms)
- **Time-to-first-token (TTFT)** (`groq:openai/gpt-oss-20b`): mean 791.0 ms, p50 790.9 ms, p95 1096.6 ms (n=5, range 525.3 ms–1096.6 ms)
### Model inference

- **Full response** (`groq:openai/gpt-oss-20b`): mean 741.2 ms, p50 741.2 ms, p95 741.2 ms (n=1, range 741.2 ms–741.2 ms)
### Text-to-Speech (ElevenLabs)

- **Synthesis real-time factor (x)** (`eleven_flash_v2_5`): mean 167.04x, p50 154.76x, p95 277.26x (n=5, range 98.59x–277.26x)
- **Time-to-first-audio-chunk** (`eleven_flash_v2_5`): mean 334.4 ms, p50 254.3 ms, p95 691.0 ms (n=5, range 194.4 ms–691.0 ms)
- **Full synthesis** (`eleven_flash_v2_5`): mean 465.3 ms, p50 431.2 ms, p95 772.6 ms (n=5, range 279.3 ms–772.6 ms)

## Notes

- All timings are wall-clock, measured from the client machine.
- LLM latency uses streaming; TTFT = first generated token.
- TTS `first_chunk` = time until first PCM audio chunk; `total` = until the audio stream is fully received.
- ASR `connect` = WebSocket session setup. Turn latency requires real speech (set `ASR_AUDIO_FILE`).
- End-to-end pipeline = ASR turn (mocked in test) + LLM total + TTS first chunk; represents time from end of speech to audio start.
- Run with: `uv run pytest tests/test_latency.py -v`
