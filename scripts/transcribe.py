"""Transcription avec reprise. python scripts/transcribe.py cache/<dossier> [--force] [--force-whisper] [--cookies]"""
import argparse, glob, os, platform, re, subprocess
from common import BASE, ffmpeg, load, save, hms

TS = re.compile(r"((?:\d+:)?\d+:\d+\.\d+) --> ((?:\d+:)?\d+:\d+\.\d+)")
ARM = platform.machine() == "arm64"

def sec(t):
    p = [float(x) for x in t.split(":")]
    while len(p) < 3:
        p.insert(0, 0.0)
    return p[0] * 3600 + p[1] * 60 + p[2]

def parse_vtt(path):
    segs, seen = [], ""
    for b in open(path, encoding="utf-8").read().split("\n\n"):
        lines = b.strip().split("\n")
        for i, l in enumerate(lines):
            m = TS.search(l)
            if m:
                for x in lines[i + 1:]:
                    t = re.sub(r"<[^>]+>", "", x).strip()
                    if t and t != seen:
                        segs.append({"start": sec(m.group(1)), "end": sec(m.group(2)), "text": t})
                        seen = t
                break
    return segs

def get_audio(d, meta, cookies):
    vids = glob.glob(os.path.join(d, "video.*"))
    if vids:
        return vids[0]
    a = os.path.join(d, "audio.m4a")
    if not os.path.exists(a):
        import yt_dlp
        opts = {"quiet": True, "format": "ba/b", "outtmpl": os.path.join(d, "audio.%(ext)s"),
                "ffmpeg_location": ffmpeg(),
                "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "m4a"}]}
        if cookies:
            opts["cookiesfrombrowser"] = ("chrome",)
        with yt_dlp.YoutubeDL(opts) as y:
            y.download([meta["webpage_url"]])
    return a

def whisper(d, src, lang):
    pd = os.path.join(d, "parts")
    os.makedirs(pd, exist_ok=True)
    if not glob.glob(os.path.join(pd, "p*.wav")):
        subprocess.run([ffmpeg(), "-loglevel", "error", "-y", "-i", src, "-vn", "-ac", "1", "-ar", "16000",
                        "-f", "segment", "-segment_time", "1800", os.path.join(pd, "p%03d.wav")], check=True)
    wavs = sorted(glob.glob(os.path.join(pd, "p*.wav")))
    out = []
    for i, w in enumerate(wavs):
        js = w[:-4] + ".json"
        if not os.path.exists(js):
            print(f"Transcription partie {i+1}/{len(wavs)}…", flush=True)
            if ARM:
                import mlx_whisper
                r = mlx_whisper.transcribe(w, path_or_hf_repo="mlx-community/whisper-large-v3-turbo", language=lang)
                segs = [{"start": s["start"], "end": s["end"], "text": s["text"].strip()} for s in r["segments"]]
            else:
                from faster_whisper import WhisperModel
                m = WhisperModel("medium", compute_type="int8")
                ss, _ = m.transcribe(w, language=lang, vad_filter=True)
                segs = [{"start": s.start, "end": s.end, "text": s.text.strip()} for s in ss]
            save(js, segs)
        else:
            print(f"Partie {i+1}/{len(wavs)} déjà faite", flush=True)
        off = i * 1800
        out += [{"start": s["start"] + off, "end": s["end"] + off, "text": s["text"]} for s in load(js, [])]
    return out

ap = argparse.ArgumentParser()
ap.add_argument("dir")
ap.add_argument("--force", action="store_true")
ap.add_argument("--force-whisper", action="store_true")
ap.add_argument("--cookies", action="store_true")
a = ap.parse_args()
d = a.dir if os.path.isabs(a.dir) else os.path.join(BASE, a.dir)
meta = load(os.path.join(d, "meta.json"), {})
out = os.path.join(d, "transcript.json")

if os.path.exists(out) and not a.force:
    tr = load(out)
    print("Déjà transcrit (cache).")
else:
    segs, source = [], None
    subs = sorted(glob.glob(os.path.join(d, "subs*.vtt")))
    lang = meta.get("language")
    if subs and not a.force_whisper:
        pick = next((s for s in subs if lang and f".{lang}" in os.path.basename(s)), subs[0])
        segs, source = parse_vtt(pick), "sous-titres " + os.path.basename(pick)
    if len(segs) < 5:
        segs, source = whisper(d, get_audio(d, meta, a.cookies), lang), "whisper"
    dur = meta.get("duration") or (segs[-1]["end"] if segs else 0)
    words = sum(len(s["text"].split()) for s in segs)
    tr = {"source": source, "mots": words,
          "mots_par_minute": round(words / (dur / 60)) if dur else None, "segments": segs}
    save(out, tr)
    lines, buf, t0 = [], [], None
    for s in segs:
        if t0 is None:
            t0 = s["start"]
        buf.append(s["text"])
        if s["end"] - t0 >= 30:
            lines.append(f"[{hms(t0)}] " + " ".join(buf))
            buf, t0 = [], None
    if buf:
        lines.append(f"[{hms(t0)}] " + " ".join(buf))
    open(os.path.join(d, "transcript.txt"), "w", encoding="utf-8").write("\n".join(lines))
print(f"Source : {tr['source']} · {tr['mots']} mots · {tr['mots_par_minute']} mots/min -> {d}/transcript.txt")
