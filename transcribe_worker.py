from pathlib import Path
from PySide6.QtCore import QThread, Signal


def timestamp_srt(seconds):
    milliseconds = int(round(seconds * 1000))
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    seconds, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


class TranscriptionWorker(QThread):
    progress = Signal(str)
    completed = Signal(dict)
    error = Signal(str)

    def __init__(self, media_path, language, model_size):
        super().__init__()
        self.media_path = media_path
        self.language = language or None
        self.model_size = model_size

    def run(self):
        try:
            from faster_whisper import WhisperModel

            self.progress.emit(
                f"Memuat model Whisper ({self.model_size}). "
                "Unduhan model pertama kali dapat memerlukan waktu."
            )
            model = WhisperModel(
                self.model_size,
                device="cpu",
                compute_type="int8"
            )

            self.progress.emit("Menganalisis audio dan membuat transkrip…")
            segments, info = model.transcribe(
                self.media_path,
                language=self.language,
                beam_size=5,
                vad_filter=True
            )

            text_lines = []
            srt_lines = []
            count = 0
            for segment in segments:
                text = segment.text.strip()
                if not text:
                    continue
                count += 1
                text_lines.append(text)
                srt_lines.extend([
                    str(count),
                    f"{timestamp_srt(segment.start)} --> {timestamp_srt(segment.end)}",
                    text,
                    ""
                ])
                if count % 10 == 0:
                    self.progress.emit(f"Mentranskripsikan… {count} segmen")

            if not text_lines:
                raise RuntimeError(
                    "Tidak ada ucapan yang berhasil dikenali. "
                    "Pastikan file memiliki audio yang jelas."
                )

            source = Path(self.media_path)
            txt_path = source.with_name(source.stem + "_transcript.txt")
            srt_path = source.with_name(source.stem + "_transcript.srt")

            transcript = "\n".join(text_lines)
            txt_path.write_text(transcript + "\n", encoding="utf-8")
            srt_path.write_text("\n".join(srt_lines), encoding="utf-8")

            self.completed.emit({
                "text": transcript,
                "txt_path": str(txt_path),
                "srt_path": str(srt_path),
                "language": info.language or "unknown",
                "segments": count
            })

        except Exception as exc:
            self.error.emit(str(exc))
