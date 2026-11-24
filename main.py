import sys
from pathlib import Path
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QFileDialog, QProgressBar, QTextEdit,
    QFrame, QMessageBox, QCheckBox
)
from workers import InfoWorker, DownloadWorker
from downloader import load_history, save_history
from transcribe_worker import TranscriptionWorker
from translation_worker import TranslationWorker, LANGUAGES
from dubbing_worker import DubbingWorker, MODEL_MAP

APP_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT = APP_DIR / "downloads"

STYLE = """
QWidget { background: #101827; color: #e5edf7; font-family: 'Segoe UI', sans-serif; font-size: 13px; }
QFrame#Card { background: #192538; border: 1px solid #293a52; border-radius: 14px; }
QLabel#Title { font-size: 25px; font-weight: 700; color: #f4f8ff; }
QLabel#Muted { color: #91a4bd; }
QLineEdit, QComboBox, QTextEdit {
  background: #0e1725; border: 1px solid #344760; border-radius: 9px;
  padding: 10px; color: #edf4ff; selection-background-color: #1689e8;
}
QComboBox::drop-down { border: 0; width: 24px; }
QPushButton {
  background: #263951; border: 1px solid #3a526f; border-radius: 9px;
  padding: 10px 15px; font-weight: 600;
}
QPushButton:hover { background: #324b69; }
QPushButton:disabled { color: #718096; background: #1b293b; }
QPushButton#Primary { background: #0879d1; border: 0; color: white; }
QPushButton#Primary:hover { background: #0b8be9; }
QPushButton#Danger { background: #8f3544; border: 0; color: white; }
QProgressBar { background: #0e1725; border: 1px solid #344760; border-radius: 7px; height: 16px; text-align: center; }
QProgressBar::chunk { background: #11a5a0; border-radius: 6px; }
"""

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Media Downloader")
        self.resize(900, 760)
        self.info_worker = None
        self.download_worker = None
        self.transcription_worker = None
        self.translation_worker = None
        self.dubbing_worker = None
        self.transcription_path = ""
        self.last_translation_srt = ""
        self.last_transcript_text = ""
        self.last_transcript_srt = ""
        self.current_info = None
        self.history = load_history()
        self.output_dir = str(DEFAULT_OUTPUT)
        DEFAULT_OUTPUT.mkdir(parents=True, exist_ok=True)

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Media Downloader")
        title.setObjectName("Title")
        subtitle = QLabel("Unduh konten yang Anda miliki atau diizinkan untuk disimpan.")
        subtitle.setObjectName("Muted")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)
        header.addStretch()
        badge = QLabel("PYTHON • DESKTOP")
        badge.setStyleSheet("color:#66c6ff; font-weight:700; letter-spacing:1px;")
        header.addWidget(badge)
        layout.addLayout(header)

        url_card = self.card()
        url_layout = QVBoxLayout(url_card)
        url_layout.addWidget(QLabel("URL VIDEO"))
        url_row = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Tempel URL video di sini…")
        self.url_input.returnPressed.connect(self.fetch_info)
        self.fetch_btn = QPushButton("Periksa")
        self.fetch_btn.setObjectName("Primary")
        self.fetch_btn.clicked.connect(self.fetch_info)
        url_row.addWidget(self.url_input, 1)
        url_row.addWidget(self.fetch_btn)
        url_layout.addLayout(url_row)
        layout.addWidget(url_card)

        info_card = self.card()
        info_layout = QHBoxLayout(info_card)
        self.thumbnail = QLabel("PREVIEW")
        self.thumbnail.setAlignment(Qt.AlignCenter)
        self.thumbnail.setFixedSize(160, 100)
        self.thumbnail.setStyleSheet("background:#0e1725;border-radius:9px;color:#718096;")
        info_layout.addWidget(self.thumbnail)
        text_col = QVBoxLayout()
        self.video_title = QLabel("Informasi video akan tampil di sini")
        self.video_title.setWordWrap(True)
        self.video_title.setStyleSheet("font-size:16px;font-weight:700;")
        self.video_meta = QLabel("Judul • channel • durasi")
        self.video_meta.setObjectName("Muted")
        self.video_meta.setWordWrap(True)
        text_col.addWidget(self.video_title)
        text_col.addWidget(self.video_meta)
        text_col.addStretch()
        info_layout.addLayout(text_col, 1)
        layout.addWidget(info_card)

        settings_card = self.card()
        settings = QVBoxLayout(settings_card)
        settings.addWidget(QLabel("PENGATURAN DOWNLOAD"))
        row = QHBoxLayout()
        self.mode = QComboBox()
        self.mode.addItems(["Video (MP4)", "Audio (MP3)"])
        self.mode.currentIndexChanged.connect(self.update_quality_state)
        self.quality = QComboBox()
        self.quality.addItems(["Best available", "1080p", "720p", "480p", "360p"])
        row.addWidget(QLabel("Format"))
        row.addWidget(self.mode, 1)
        row.addWidget(QLabel("Kualitas"))
        row.addWidget(self.quality, 1)
        settings.addLayout(row)

        folder_row = QHBoxLayout()
        self.folder_input = QLineEdit(self.output_dir)
        self.folder_input.setReadOnly(True)
        browse = QPushButton("Pilih folder…")
        browse.clicked.connect(self.choose_folder)
        open_folder = QPushButton("Buka folder")
        open_folder.clicked.connect(self.open_folder)
        folder_row.addWidget(QLabel("Simpan ke"))
        folder_row.addWidget(self.folder_input, 1)
        folder_row.addWidget(browse)
        folder_row.addWidget(open_folder)
        settings.addLayout(folder_row)
        layout.addWidget(settings_card)

        progress_card = self.card()
        progress_layout = QVBoxLayout(progress_card)
        progress_top = QHBoxLayout()
        progress_top.addWidget(QLabel("PROGRES"))
        progress_top.addStretch()
        self.status = QLabel("Siap")
        self.status.setObjectName("Muted")
        progress_top.addWidget(self.status)
        progress_layout.addLayout(progress_top)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        progress_layout.addWidget(self.progress)
        self.progress_detail = QLabel("Menunggu download dimulai")
        self.progress_detail.setObjectName("Muted")
        progress_layout.addWidget(self.progress_detail)
        buttons = QHBoxLayout()
        self.download_btn = QPushButton("Mulai Download")
        self.download_btn.setObjectName("Primary")
        self.download_btn.clicked.connect(self.start_download)
        self.cancel_btn = QPushButton("Batalkan")
        self.cancel_btn.setObjectName("Danger")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.cancel_download)
        buttons.addWidget(self.download_btn, 1)
        buttons.addWidget(self.cancel_btn)
        progress_layout.addLayout(buttons)
        layout.addWidget(progress_card)


        # Audio/video transcription section
        transcript_card = self.card()
        transcript_layout = QVBoxLayout(transcript_card)
        transcript_layout.addWidget(QLabel("TRANSKRIPSI AUDIO / VIDEO"))
        transcript_hint = QLabel(
            "Ubah ucapan dalam file audio atau video menjadi teks TXT dan subtitle SRT."
        )
        transcript_hint.setObjectName("Muted")
        transcript_hint.setWordWrap(True)
        transcript_layout.addWidget(transcript_hint)

        transcript_file_row = QHBoxLayout()
        self.transcript_file_input = QLineEdit()
        self.transcript_file_input.setReadOnly(True)
        self.transcript_file_input.setPlaceholderText("Pilih file audio/video…")
        choose_media_btn = QPushButton("Pilih file…")
        choose_media_btn.clicked.connect(self.choose_transcription_file)
        transcript_file_row.addWidget(self.transcript_file_input, 1)
        transcript_file_row.addWidget(choose_media_btn)
        transcript_layout.addLayout(transcript_file_row)

        transcript_options = QHBoxLayout()
        self.transcript_language = QComboBox()
        self.transcript_language.addItem("Deteksi otomatis", "")
        self.transcript_language.addItem("Bahasa Indonesia", "id")
        self.transcript_language.addItem("English", "en")
        self.transcript_language.addItem("Bahasa Melayu", "ms")
        self.transcript_model = QComboBox()
        self.transcript_model.addItems(["base", "small", "medium"])
        transcript_options.addWidget(QLabel("Bahasa"))
        transcript_options.addWidget(self.transcript_language, 1)
        transcript_options.addWidget(QLabel("Model"))
        transcript_options.addWidget(self.transcript_model, 1)
        transcript_layout.addLayout(transcript_options)

        transcript_actions = QHBoxLayout()
        self.transcribe_btn = QPushButton("Buat Transkrip TXT + SRT")
        self.transcribe_btn.setObjectName("Primary")
        self.transcribe_btn.clicked.connect(self.start_transcription)
        self.transcript_open_btn = QPushButton("Buka folder hasil")
        self.transcript_open_btn.clicked.connect(self.open_transcript_folder)
        transcript_actions.addWidget(self.transcribe_btn, 1)
        transcript_actions.addWidget(self.transcript_open_btn)
        transcript_layout.addLayout(transcript_actions)

        self.transcript_status = QLabel("Pilih file untuk memulai transkripsi.")
        self.transcript_status.setObjectName("Muted")
        self.transcript_status.setWordWrap(True)
        transcript_layout.addWidget(self.transcript_status)

        self.transcript_preview = QTextEdit()
        self.transcript_preview.setReadOnly(True)
        self.transcript_preview.setPlaceholderText("Hasil transkripsi akan tampil di sini…")
        self.transcript_preview.setMaximumHeight(120)

        transcript_layout.addWidget(self.transcript_preview)

        translation_title = QLabel("TERJEMAHKAN TRANSKRIP")
        translation_title.setStyleSheet("font-weight:700;color:#66c6ff;")
        transcript_layout.addWidget(translation_title)
        translation_row = QHBoxLayout()
        self.translation_language = QComboBox()
        for label, code in LANGUAGES:
            self.translation_language.addItem(label, code)
        self.translate_btn = QPushButton("Terjemahkan")
        self.translate_btn.setObjectName("Primary")
        self.translate_btn.setEnabled(False)
        self.translate_btn.clicked.connect(self.start_translation)
        translation_row.addWidget(QLabel("Bahasa tujuan"))
        translation_row.addWidget(self.translation_language, 1)
        translation_row.addWidget(self.translate_btn)
        transcript_layout.addLayout(translation_row)

        self.translation_preview = QTextEdit()
        self.translation_preview.setReadOnly(True)
        self.translation_preview.setPlaceholderText("Hasil terjemahan akan tampil di sini…")
        self.translation_preview.setMaximumHeight(100)

        transcript_layout.addWidget(self.translation_preview)

        dubbing_title = QLabel("AI DUBBING / VOICE LOCALIZATION")
        dubbing_title.setStyleSheet("font-weight:700;color:#66c6ff;")
        transcript_layout.addWidget(dubbing_title)
        dubbing_hint = QLabel(
            "Buat audio dubbing lokal dari subtitle terjemahan. "
            "Untuk video, aplikasi dapat mengganti audio asli dengan audio dubbing."
        )
        dubbing_hint.setObjectName("Muted")
        dubbing_hint.setWordWrap(True)
        transcript_layout.addWidget(dubbing_hint)

        dubbing_row = QHBoxLayout()
        self.dubbing_language = QComboBox()
        self.dubbing_language.addItem("Bahasa Indonesia", "id")
        self.dubbing_language.addItem("Bahasa Sunda", "sun")
        self.dubbing_language.addItem("Bahasa Jawa", "jav")
        self.dub_btn = QPushButton("Buat Dubbing")
        self.dub_btn.setObjectName("Primary")
        self.dub_btn.setEnabled(False)
        self.dub_btn.clicked.connect(self.start_dubbing)
        dubbing_row.addWidget(QLabel("Suara tujuan"))
        dubbing_row.addWidget(self.dubbing_language, 1)
        dubbing_row.addWidget(self.dub_btn)
        transcript_layout.addLayout(dubbing_row)

        self.dubbing_status = QLabel(
            "Buat terjemahan terlebih dahulu. Model TTS akan diunduh saat pertama digunakan."
        )
        self.dubbing_status.setObjectName("Muted")
        self.dubbing_status.setWordWrap(True)
        transcript_layout.addWidget(self.dubbing_status)
        layout.addWidget(transcript_card)

        history_card = self.card()
        history_layout = QVBoxLayout(history_card)
        history_header = QHBoxLayout()
        history_header.addWidget(QLabel("RIWAYAT DOWNLOAD"))
        history_header.addStretch()
        clear_btn = QPushButton("Bersihkan riwayat")
        clear_btn.clicked.connect(self.clear_history)
        history_header.addWidget(clear_btn)
        history_layout.addLayout(history_header)
        self.history_view = QTextEdit()
        self.history_view.setReadOnly(True)
        self.history_view.setMaximumHeight(105)
        history_layout.addWidget(self.history_view)
        layout.addWidget(history_card)
        self.refresh_history()

    def card(self):
        frame = QFrame()
        frame.setObjectName("Card")
        return frame

    def fetch_info(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "URL kosong", "Masukkan URL video terlebih dahulu.")
            return
        self.fetch_btn.setEnabled(False)
        self.thumbnail.setPixmap(QPixmap())
        self.thumbnail.setText("Memuat…")
        self.video_title.setText("Mengambil informasi video…")
        self.video_meta.setText("")
        self.status.setText("Memeriksa informasi…")
        self.info_worker = InfoWorker(url)
        self.info_worker.info_ready.connect(self.on_info)
        self.info_worker.error.connect(self.on_error)
        self.info_worker.start()

    def on_info(self, info, thumbnail_data):
        self.fetch_btn.setEnabled(True)
        self.current_info = info
        title = info.get("title") or "Judul tidak tersedia"
        uploader = info.get("uploader") or info.get("channel") or "Channel tidak diketahui"
        duration = info.get("duration_string") or "Durasi tidak tersedia"
        self.video_title.setText(title)
        self.video_meta.setText(f"{uploader}  •  {duration}")
        self.status.setText("Informasi siap")
        thumb = info.get("thumbnail")
        if thumbnail_data:
            pixmap = QPixmap()
            if pixmap.loadFromData(thumbnail_data):
                scaled = pixmap.scaled(
                    self.thumbnail.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.thumbnail.setPixmap(scaled)
                self.thumbnail.setText("")
                self.thumbnail.setToolTip(thumb or "")
            else:
                self.thumbnail.setPixmap(QPixmap())
                self.thumbnail.setText("Preview gagal")
        else:
            self.thumbnail.setPixmap(QPixmap())
            self.thumbnail.setText("Preview tidak tersedia")

    def on_error(self, message):
        self.fetch_btn.setEnabled(True)
        self.status.setText("Terjadi kesalahan")
        QMessageBox.critical(self, "Proses gagal", message)

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Pilih folder output", self.output_dir)
        if folder:
            self.output_dir = folder
            self.folder_input.setText(folder)

    def open_folder(self):
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(self.output_dir))

    def update_quality_state(self):
        self.quality.setEnabled(self.mode.currentIndex() == 0)

    def start_download(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "URL kosong", "Masukkan URL video terlebih dahulu.")
            return
        if self.download_worker and self.download_worker.isRunning():
            return
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        audio = self.mode.currentIndex() == 1
        quality = self.quality.currentText()
        self.download_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.fetch_btn.setEnabled(False)
        self.progress.setValue(0)
        self.status.setText("Mengunduh…")
        self.progress_detail.setText("Menyiapkan unduhan")
        self.download_worker = DownloadWorker(url, self.output_dir, audio, quality)
        self.download_worker.progress.connect(self.on_progress)
        self.download_worker.completed.connect(self.on_download_complete)
        self.download_worker.error.connect(self.on_download_error)
        self.download_worker.start()

    def on_progress(self, data):
        percent = data.get("percent", 0)
        self.progress.setValue(max(0, min(100, int(percent))))
        speed = data.get("speed") or "-"
        eta = data.get("eta") or "-"
        self.progress_detail.setText(f"{percent:.1f}%  •  Kecepatan: {speed}  •  Sisa: {eta}")

    def on_download_complete(self, filepath):
        self.download_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.fetch_btn.setEnabled(True)
        self.progress.setValue(100)
        self.status.setText("Selesai")
        self.progress_detail.setText(f"Tersimpan: {filepath}")
        self.history.insert(0, {"title": self.video_title.text(), "path": filepath})
        self.history = self.history[:30]
        save_history(self.history)
        self.refresh_history()
        QMessageBox.information(self, "Download selesai", f"File tersimpan:\n{filepath}")

    def on_download_error(self, message):
        self.download_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.fetch_btn.setEnabled(True)
        self.status.setText("Gagal / dibatalkan")
        self.progress_detail.setText(message)
        if "dibatalkan" not in message.lower():
            QMessageBox.critical(self, "Download gagal", message)

    def cancel_download(self):
        if self.download_worker:
            self.download_worker.cancel()
            self.status.setText("Membatalkan…")
            self.cancel_btn.setEnabled(False)



    def start_translation(self):
        if not self.last_transcript_text or not self.last_transcript_srt:
            QMessageBox.warning(
                self, "Transkrip belum tersedia",
                "Buat transkrip terlebih dahulu sebelum menerjemahkan."
            )
            return
        if self.translation_worker and self.translation_worker.isRunning():
            return

        target_code = self.translation_language.currentData()
        target_name = self.translation_language.currentText()
        self.translate_btn.setEnabled(False)
        self.transcript_status.setText(f"Menyiapkan terjemahan ke {target_name}…")
        self.translation_worker = TranslationWorker(
            self.last_transcript_text,
            self.last_transcript_srt,
            target_code,
            target_name
        )
        self.translation_worker.progress.connect(self.on_translation_progress)
        self.translation_worker.completed.connect(self.on_translation_complete)
        self.translation_worker.error.connect(self.on_translation_error)
        self.translation_worker.start()

    def on_translation_progress(self, message):
        self.transcript_status.setText(message)

    def on_translation_complete(self, result):
        self.translate_btn.setEnabled(True)
        self.last_translation_srt = result["srt_path"]
        self.dub_btn.setEnabled(True)
        self.translation_preview.setPlainText(result["text"])
        self.transcript_status.setText(
            f"Terjemahan selesai • {result['language']}\n"
            f"TXT: {result['txt_path']}\nSRT: {result['srt_path']}"
        )
        QMessageBox.information(
            self,
            "Terjemahan selesai",
            f"Hasil terjemahan tersimpan:\n\n"
            f"{result['txt_path']}\n{result['srt_path']}"
        )

    def on_translation_error(self, message):
        self.translate_btn.setEnabled(True)
        self.transcript_status.setText("Terjemahan gagal.")
        QMessageBox.critical(self, "Terjemahan gagal", message)


    def start_dubbing(self):
        if not self.last_translation_srt:
            QMessageBox.warning(
                self, "Terjemahan belum tersedia",
                "Buat transkrip dan terjemahan terlebih dahulu."
            )
            return
        if self.dubbing_worker and self.dubbing_worker.isRunning():
            return

        lang = self.dubbing_language.currentData()
        self.dub_btn.setEnabled(False)
        self.dubbing_status.setText("Menyiapkan model text-to-speech…")
        self.dubbing_worker = DubbingWorker(
            self.last_translation_srt,
            self.transcription_path,
            lang
        )
        self.dubbing_worker.progress.connect(self.on_dubbing_progress)
        self.dubbing_worker.completed.connect(self.on_dubbing_complete)
        self.dubbing_worker.error.connect(self.on_dubbing_error)
        self.dubbing_worker.start()

    def on_dubbing_progress(self, message):
        self.dubbing_status.setText(message)

    def on_dubbing_complete(self, result):
        self.dub_btn.setEnabled(True)
        lines = [f"Audio: {result['wav_path']}"]
        if result.get("video_path"):
            lines.append(f"Video: {result['video_path']}")
        self.dubbing_status.setText("Dubbing selesai • " + result["language"] + "\n" + "\n".join(lines))
        QMessageBox.information(
            self,
            "Dubbing selesai",
            "Hasil dubbing berhasil dibuat:\n\n" + "\n".join(lines)
        )

    def on_dubbing_error(self, message):
        self.dub_btn.setEnabled(True)
        self.dubbing_status.setText("Dubbing gagal.")
        QMessageBox.critical(self, "Dubbing gagal", message)

    def choose_transcription_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Pilih file audio atau video",
            self.output_dir,
            "Media (*.mp3 *.wav *.m4a *.aac *.flac *.ogg *.opus *.mp4 *.mkv *.mov *.webm *.avi);;Semua file (*)"
        )
        if path:
            self.transcription_path = path
            self.transcript_file_input.setText(path)
            self.transcript_status.setText("File siap ditranskripsikan.")
            self.transcript_preview.clear()

    def start_transcription(self):
        if not self.transcription_path:
            QMessageBox.warning(self, "File belum dipilih", "Pilih file audio atau video terlebih dahulu.")
            return
        if self.transcription_worker and self.transcription_worker.isRunning():
            return

        language = self.transcript_language.currentData()
        model_size = self.transcript_model.currentText()
        self.transcribe_btn.setEnabled(False)
        self.transcript_status.setText(
            "Memulai transkripsi… Model Whisper mungkin perlu diunduh pada penggunaan pertama."
        )
        self.transcription_worker = TranscriptionWorker(
            self.transcription_path, language, model_size
        )
        self.transcription_worker.progress.connect(self.on_transcription_progress)
        self.transcription_worker.completed.connect(self.on_transcription_complete)
        self.transcription_worker.error.connect(self.on_transcription_error)
        self.transcription_worker.start()

    def on_transcription_progress(self, message):
        self.transcript_status.setText(message)

    def on_transcription_complete(self, result):
        self.transcribe_btn.setEnabled(True)
        self.last_transcript_text = result["text"]
        self.last_transcript_srt = result["srt_path"]
        self.translate_btn.setEnabled(True)
        self.translation_preview.clear()
        self.transcript_preview.setPlainText(result["text"])
        self.transcript_status.setText(
            f"Selesai • Bahasa: {result['language']} • {result['segments']} segmen\n"
            f"TXT: {result['txt_path']}\nSRT: {result['srt_path']}"
        )
        QMessageBox.information(
            self,
            "Transkripsi selesai",
            f"File teks dan subtitle berhasil dibuat:\n\n"
            f"{result['txt_path']}\n{result['srt_path']}"
        )

    def on_transcription_error(self, message):
        self.transcribe_btn.setEnabled(True)
        self.transcript_status.setText("Transkripsi gagal.")
        QMessageBox.critical(self, "Transkripsi gagal", message)

    def open_transcript_folder(self):
        if self.transcription_path:
            folder = str(Path(self.transcription_path).parent)
        else:
            folder = self.output_dir
        Path(folder).mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(folder))

    def refresh_history(self):
        if not self.history:
            self.history_view.setPlainText("Belum ada unduhan.")
            return
        lines = []
        for item in self.history:
            lines.append(f"• {item.get('title', 'Tanpa judul')}\n  {item.get('path', '')}")
        self.history_view.setPlainText("\n".join(lines))

    def clear_history(self):
        self.history = []
        save_history(self.history)
        self.refresh_history()

    def closeEvent(self, event):
        if self.download_worker and self.download_worker.isRunning():
            self.download_worker.cancel()
            self.download_worker.wait(3000)
        if self.transcription_worker and self.transcription_worker.isRunning():
            self.transcription_worker.wait(3000)
        if self.translation_worker and self.translation_worker.isRunning():
            self.translation_worker.wait(3000)
        if self.dubbing_worker and self.dubbing_worker.isRunning():
            self.dubbing_worker.wait(3000)
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
