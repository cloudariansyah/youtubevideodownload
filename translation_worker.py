from pathlib import Path
import re
from PySide6.QtCore import QThread, Signal


LANGUAGES = [
    ("English", "en"),
    ("Bahasa Indonesia", "id"),
    ("Bahasa Melayu", "ms"),
    ("日本語 (Japanese)", "ja"),
    ("中文 (Chinese)", "zh-CN"),
    ("한국어 (Korean)", "ko"),
    ("Español (Spanish)", "es"),
    ("Français (French)", "fr"),
    ("Deutsch (German)", "de"),
    ("العربية (Arabic)", "ar"),
    ("Português (Portuguese)", "pt"),
    ("ไทย (Thai)", "th"),
    ("हिन्दी (Hindi)", "hi"),
    ("Русский (Russian)", "ru"),
    ("Italiano (Italian)", "it"),
    ("Türkçe (Turkish)", "tr"),
    ("Tiếng Việt (Vietnamese)", "vi"),
    ("Filipino", "tl"),
]


def translate_long_text(translator, text, max_chars=4000):
    """Split long paragraphs into API-safe chunks without dropping text."""
    if not text:
        return ""
    chunks = []
    remaining = text
    while len(remaining) > max_chars:
        cut = remaining.rfind("\n", 0, max_chars)
        if cut < max_chars // 2:
            cut = remaining.rfind(" ", 0, max_chars)
        if cut < max_chars // 2:
            cut = max_chars
        chunks.append(remaining[:cut])
        remaining = remaining[cut:].lstrip()
    if remaining:
        chunks.append(remaining)
    return "\n".join(translator.translate(chunk) for chunk in chunks)


class TranslationWorker(QThread):
    progress = Signal(str)
    completed = Signal(dict)
    error = Signal(str)

    def __init__(self, source_text, source_srt_path, target_code, target_name):
        super().__init__()
        self.source_text = source_text
        self.source_srt_path = source_srt_path
        self.target_code = target_code
        self.target_name = target_name

    def run(self):
        try:
            from deep_translator import GoogleTranslator

            translator = GoogleTranslator(source="auto", target=self.target_code)
            self.progress.emit(f"Menerjemahkan transkrip ke {self.target_name}…")

            translated_text = translate_long_text(translator, self.source_text)
            if not translated_text.strip():
                raise RuntimeError("Hasil terjemahan kosong.")

            source_srt = Path(self.source_srt_path)
            translated_txt_path = source_srt.with_name(
                source_srt.stem.replace("_transcript", f"_translated_{self.target_code}") + ".txt"
            )
            translated_srt_path = source_srt.with_name(
                source_srt.stem.replace("_transcript", f"_translated_{self.target_code}") + ".srt"
            )

            translated_txt_path.write_text(translated_text + "\n", encoding="utf-8")

            # Translate subtitle cue-by-cue; keep cue numbers and timestamps intact.
            srt_content = source_srt.read_text(encoding="utf-8")
            blocks = re.split(r"\r?\n\s*\r?\n", srt_content.strip())
            translated_blocks = []
            cue_total = len(blocks)
            for index, block in enumerate(blocks, start=1):
                lines = block.splitlines()
                if len(lines) >= 3 and "-->" in lines[1]:
                    cue_text = "\n".join(lines[2:]).strip()
                    translated_cue = translate_long_text(translator, cue_text)
                    translated_blocks.append("\n".join(lines[:2] + [translated_cue]))
                else:
                    translated_blocks.append(block)
                if index % 5 == 0 or index == cue_total:
                    self.progress.emit(
                        f"Menerjemahkan subtitle… {index}/{cue_total}"
                    )

            translated_srt_path.write_text(
                "\n\n".join(translated_blocks) + "\n", encoding="utf-8"
            )

            self.completed.emit({
                "text": translated_text,
                "txt_path": str(translated_txt_path),
                "srt_path": str(translated_srt_path),
                "language": self.target_name,
            })
        except Exception as exc:
            self.error.emit(
                f"Gagal menerjemahkan: {exc}\n"
                "Periksa koneksi internet dan coba lagi."
            )
