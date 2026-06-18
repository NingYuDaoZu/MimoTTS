import argparse
import base64
import os
import struct
import wave
from pathlib import Path

from openai import OpenAI


def get_client() -> OpenAI:
    # Priority: environment variable > key.txt in script directory
    api_key = os.getenv("MIMO_API_KEY")
    if not api_key:
        key_file = Path(__file__).resolve().parent / "key.txt"
        if key_file.exists():
            api_key = key_file.read_text(encoding="utf-8").strip()
    if not api_key:
        raise RuntimeError(
            "API key not found. Please set MIMO_API_KEY env var "
            "or put your key in key.txt in the script directory."
        )
    return OpenAI(api_key=api_key, base_url="https://api.xiaomimimo.com/v1")


def encode_audio(path: Path) -> str:
    """Read an audio file and return a data-URI string with base64 encoding."""
    data = path.read_bytes()
    b64 = base64.b64encode(data).decode()
    suffix = path.suffix.lower()
    if suffix == ".mp3":
        mime = "audio/mpeg"
    elif suffix == ".wav":
        mime = "audio/wav"
    else:
        raise ValueError(f"Unsupported audio format: {suffix}. Use mp3 or wav.")
    return f"data:{mime};base64,{b64}"


def save_pcm16_wav(path: Path, pcm_bytes: bytes, sample_rate: int = 24000) -> None:
    """Write raw PCM16LE mono bytes to a WAV file."""
    n_samples = len(pcm_bytes) // 2
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit = 2 bytes
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)


def clone_voice(
    voice: Path,
    text: str,
    output: Path,
    stream: bool = False,
    style: str | None = None,
) -> None:
    client = get_client()
    voice_uri = encode_audio(voice)

    messages: list[dict[str, str]] = []
    # user message: optional style instruction (natural language control)
    messages.append({"role": "user", "content": style or ""})
    # assistant message: the text to synthesize
    messages.append({"role": "assistant", "content": text})

    if stream:
        audio_cfg = {"format": "pcm16", "voice": voice_uri}
        completion = client.chat.completions.create(
            model="mimo-v2.5-tts-voiceclone",
            messages=messages,
            audio=audio_cfg,
            stream=True,
        )
        pcm_chunks: list[bytes] = []
        for chunk in completion:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            audio = getattr(delta, "audio", None)
            if audio and isinstance(audio, dict) and "data" in audio:
                pcm_chunks.append(base64.b64decode(audio["data"]))
        all_pcm = b"".join(pcm_chunks)
        output.parent.mkdir(parents=True, exist_ok=True)
        save_pcm16_wav(output, all_pcm)
    else:
        audio_cfg = {"format": "wav", "voice": voice_uri}
        completion = client.chat.completions.create(
            model="mimo-v2.5-tts-voiceclone",
            messages=messages,
            audio=audio_cfg,
        )
        message = completion.choices[0].message
        audio_bytes = base64.b64decode(message.audio.data)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(audio_bytes)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Voice clone using MiMo-V2.5-TTS (mimo-v2.5-tts-voiceclone)"
    )
    parser.add_argument(
        "voice",
        type=Path,
        help="Reference audio file for voice cloning (mp3 or wav, <=10MB)",
    )
    parser.add_argument(
        "text",
        help="Text to synthesize with the cloned voice",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=Path("clone_output.wav"),
        help="Output audio file path (default: clone_output.wav)",
    )
    parser.add_argument(
        "--stream",
        action="store_true",
        help="Use streaming mode (PCM16, low-latency)",
    )
    parser.add_argument(
        "-s", "--style",
        type=str,
        default=None,
        help='Style instruction for voice (e.g. "用欢快的语气说")',
    )
    args = parser.parse_args()

    print(f"Reference audio : {args.voice}")
    print(f"Text            : {args.text}")
    print(f"Output          : {args.output}")
    print(f"Streaming        : {args.stream}")
    if args.style:
        print(f"Style           : {args.style}")
    print("Cloning voice...")

    clone_voice(args.voice, args.text, args.output, args.stream, args.style)
    print(f"Done! Audio saved to {args.output}")


if __name__ == "__main__":
    main()

