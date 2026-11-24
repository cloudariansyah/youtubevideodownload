import re
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf
from PySide6.QtCore import QThread, Signal


MODEL_MAP = {
    "id": ("Bahasa Indonesia", "facebook/mms-tts-ind"),
    "sun": ("Bahasa Sunda", "facebook/mms-tts-sun"),
    "jav": ("Bahasa Jawa", "facebook/mms-tts-jav"),
}


def parse_srt(path):
    content = Path(path).read_text(encoding="utf-8-sig")
    blocks = re.split(r"\r?\n\s*\r?\n", content.strip())
    cues = []
    for block in blocks:
        lines = block.splitlines()
        if len(lines) < 3:
            continue
        timing = next((line for line in lines if "-->" in line), None)
        if not timing:
            continue
        match = re.search(
            r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*"
            r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})", timing
        )
        if not match:
            continue
        values = [int(v) for v in match.groups()]
        start = values[0]*3600 + values[1]*60 + values[2] + values[3]/1000
        end = values[4]*3600 + values[5]*60 + values[6] + values[7]/1000
        timing_index = lines.index(timing)
        text = re.sub(r"<[^>]+>", "", " ".join(lines[timing_index+1:])).strip()
        if text and end > start:
            cues.append((start, end, text))
    return cues


class DubbingWorker(QThread):
    progress = Signal(str)
    completed = Signal(dict)
    error = Signal(str)

    def __init__(self, srt_path, source_media_path, language_code):
        super().__init__()
        self.srt_path = srt_path
        self.source_media_path = source_media_path
        self.language_code = language_code

    def run(self):
        try:
            import torch
            from transformers import AutoTokenizer, VitsModel

            if self.language_code not in MODEL_MAP:
                raise RuntimeError("Bahasa dubbing belum didukung oleh model lokal.")
            language_name, model_id = MODEL_MAP[self.language_code]
            cues = parse_srt(self.srt_path)
            if not cues:
                raise RuntimeError("Subtitle SRT tidak berisi cue yang dapat diproses.")

            self.progress.emit(
                f"Memuat model TTS {language_name}. Unduhan model pertama kali memerlukan internet."
            )
            tokenizer = AutoTokenizer.from_pretrained(model_id)
            model = VitsModel.from_pretrained(model_id)
            model.eval()
            sample_rate = int(model.config.sampling_rate)

            # Compose each utterance at its subtitle start time. If speech runs
            # longer than its cue, preserve it instead of cutting off words.
            rendered = []
            total_duration = max(end for _, end, _ in cues) + 2.0
            self.progress.emit(f"Membuat suara dubbing: {len(cues)} subtitle…")

            with torch.no_grad():
                for index, (start, end, text) in enumerate(cues, start=1):
                    inputs = tokenizer(text, return_tensors="pt")
                    waveform = model(**inputs).waveform.squeeze().cpu().numpy().astype(np.float32)
                    if waveform.size == 0:
                        continue
                    peak = float(np.max(np.abs(waveform)))
                    if peak > 0:
                        waveform = waveform / peak * 0.85
                    rendered.append((int(start * sample_rate), waveform))
                    total_duration = max(total_duration, start + len(waveform) / sample_rate + 0.5)
                    self.progress.emit(f"Membuat dubbing… {index}/{len(cues)}")

            mix = np.zeros(int(total_duration * sample_rate), dtype=np.float32)
            for offset, audio in rendered:
                stop = min(len(mix), offset + len(audio))
                if stop > offset:
                    mix[offset:stop] += audio[:stop-offset]

            peak = float(np.max(np.abs(mix))) if mix.size else 0
            if peak > 0.98:
                mix *= 0.98 / peak

            srt = Path(self.srt_path)
            wav_path = srt.with_name(srt.stem + "_dubbed.wav")
            sf.write(str(wav_path), mix, sample_rate)

            result = {
                "wav_path": str(wav_path),
                "language": language_name,
            }

            source = Path(self.source_media_path) if self.source_media_path else None
            video_exts = {".mp4", ".mkv", ".mov", ".webm", ".avi", ".m4v"}
            if source and source.exists() and source.suffix.lower() in video_exts:
                video_path = srt.with_name(srt.stem + "_dubbed.mp4")
                self.progress.emit("Menggabungkan audio dubbing dengan video menggunakan FFmpeg…")
                command = [
                    "ffmpeg", "-y", "-i", str(source), "-i", str(wav_path),
                    "-map", "0:v:0", "-map", "1:a:0",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    str(video_path)
                ]
                completed = subprocess.run(command, capture_output=True, text=True)
                if completed.returncode != 0:
                    raise RuntimeError(
                        "Audio dubbing berhasil dibuat, tetapi penggabungan video gagal:\n"
                        + (completed.stderr[-1800:] or "FFmpeg error")
                    )
                result["video_path"] = str(video_path)

            self.completed.emit(result)

        except Exception as exc:
            self.error.emit(str(exc))
