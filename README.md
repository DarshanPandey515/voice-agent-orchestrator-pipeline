# Voice Agent

A real-time voice AI assistant pipeline: listen with a microphone, transcribe speech, run an LLM agent, and speak the reply aloud.

## Pipeline

```mermaid
flowchart LR
    Mic["You speak"] --> STT["Speech-to-text"]
    STT --> Agent["AI agent"]
    Agent --> TTS["Text-to-speech"]
    TTS --> Speaker["You hear"]
```

`main.py` is the orchestrator: it wires up the event handlers, connects the transcriber, and runs the microphone streaming loop. Each module is self-contained:

| File       | Role                                      |
|------------|-------------------------------------------|
| `main.py`  | Orchestrator — wires everything together  |
| `asr.py`   | Listens and converts speech to text       |
| `llm.py`   | Thinks and replies                        |
| `tts.py`   | Speaks the reply aloud                    |
| `tools.py` | Lets the agent run safe shell commands    |

## Requirements

- Python 3.12+
- A working microphone
- API keys: AssemblyAI, Groq, ElevenLabs

## Setup

```bash
uv sync                 # or: pip install -e .
cp .env.example .env    # then fill in your API keys
```

## Run

```bash
uv run voice-agent      # or: .venv/bin/voice-agent
# or
uv run python -m voice_agent.main
```

Speak into your mic. Press `Ctrl+C` to stop. A running transcript is appended to `transcript.txt`.

## Notes

- ASR model: `universal-3-5-pro` (configurable in `asr.py`)
- LLM model: `groq:openai/gpt-oss-20b` (configurable in `llm.py`)
- The agent's `bash` tool only allows a fixed set of read-only commands (`ls`, `cat`, `date`, etc.)