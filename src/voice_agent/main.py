import pyaudio
from assemblyai.streaming.v3 import (
    RealTimeTranscriber,
    RealTimeEvents,
    BeginEvent,
    TurnEvent,
    RealTimeError,
)

from voice_agent.asr import transcriber, connect, SAMPLE_RATE, FRAMES_PER_BUFFER
from voice_agent.llm import agent
from voice_agent.tts import audio_play


def on_open(client: RealTimeTranscriber, event: BeginEvent):
    print(f"\n🚀 Session ID: {event.id} started successfully!")


def on_data(client: RealTimeTranscriber, event: TurnEvent):
    if not event.transcript:
        return

    if event.end_of_turn:
        print("=" * 20)
        print(f"\nUser: {event.transcript}")
        
        
        user_prompt = event.transcript

        response = agent.run_sync(user_prompt)

        print("=" * 20)
        print(f"ai response: {response.output}")
        print("=" * 20)

        audio_play(response.output)

        with open("transcript.txt", "a", encoding="utf-8") as file:
            file.write(f"User: {event.transcript}\n")
            file.write(f"AI: {response.output}\n")
            file.write("\n")

    else:
        print(f"Partial: {event.transcript}", end="\r")


def on_error(client: RealTimeTranscriber, error: RealTimeError):
    print(f"\nAn error occurred: {error}")


def on_close():
    print("\nSession closed.")


def main() -> None:
    transcriber.on(RealTimeEvents.Begin, on_open)
    transcriber.on(RealTimeEvents.Turn, on_data)
    transcriber.on(RealTimeEvents.Error, on_error)
    transcriber.on(RealTimeEvents.Termination, on_close)

    connect()

    p = pyaudio.PyAudio()
    audio_stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=FRAMES_PER_BUFFER,
    )

    print("\n🎙️ Listening... Speak into your mic. Press Ctrl+C to stop.\n")

    try:
        while True:
            data = audio_stream.read(FRAMES_PER_BUFFER, exception_on_overflow=False)
            transcriber.stream(data)

    except KeyboardInterrupt:
        print("\nStopping transcription...")

    finally:
        audio_stream.stop_stream()
        audio_stream.close()
        p.terminate()
        transcriber.disconnect(terminate=True)


if __name__ == "__main__":
    main()