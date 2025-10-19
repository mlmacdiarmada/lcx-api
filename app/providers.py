import os, tempfile, subprocess, textwrap, httpx

def generate_script(topic: str, audience: str, tone: str) -> str:
    return textwrap.dedent(f"""
    Title: {topic}
    Audience: {audience}
    Tone: {tone}

    [Hook] In under a minute, let's cover the essentials of {topic.lower()}.
    [What] Plain-language definition.
    [Why] Who benefits / when it's used.
    [How] 3 key points or steps.
    [Safety] Common risks and when to talk to a clinician.

    [CTA] Educational only. Not medical advice.
    """).strip()

async def tts_elevenlabs_or_texttone(script_text: str, voice_id: str | None) -> str:
    api_key = os.getenv("ELEVENLABS_API_KEY")
    fd, path = tempfile.mkstemp(suffix=".wav"); os.close(fd)
    if not api_key:
        words = max(1, len(script_text.split()))
        seconds = min(120, max(10, int(words / 2.5)))
        subprocess.run([
            "ffmpeg","-f","lavfi","-i","anullsrc=channel_layout=stereo:sample_rate=44100",
            "-t",str(seconds),"-y",path
        ], check=True)
        return path
    url = "https://api.elevenlabs.io/v1/text-to-speech/" + (voice_id or "21m00Tcm4TlvDq8ikWAM")
    headers = {"xi-api-key": api_key, "accept": "audio/wav", "Content-Type": "application/json"}
    payload = {"text": script_text, "model_id": "eleven_monolingual_v1"}
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        with open(path, "wb") as f: f.write(r.content)
    return path

def _write_basic_srt(script_text: str, target_seconds: int) -> str:
    chunk = " ".join([l.strip() for l in script_text.splitlines() if l.strip()])[:120]
    srt = f"1\n00:00:00,000 --> 00:00:{max(5, min(59, target_seconds)):02d},000\n{chunk}\n"
    fd, srt_path = tempfile.mkstemp(suffix=".srt"); os.close(fd)
    with open(srt_path,"w") as f: f.write(srt)
    return srt_path

def render_wave_video(audio_path: str, script_text: str, duration_sec: int) -> str:
    srt_path = _write_basic_srt(script_text, duration_sec)
    fdv, out_path = tempfile.mkstemp(suffix=".mp4"); os.close(fdv)
    subprocess.run([
        "ffmpeg","-y",
        "-f","lavfi","-i","color=size=1280x720:rate=30:color=white",
        "-i",audio_path,
        "-filter_complex",
        "[1:a]showwaves=s=1280x300:mode=cline:rate=30[vis];[0:v][vis]overlay=0:210,subtitles='" + srt_path.replace("\\","/") + "':force_style='Fontsize=28'",
        "-shortest", out_path
    ], check=True)
    return out_path
