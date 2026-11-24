# Media Downloader (Python + PySide6)

Aplikasi desktop untuk menyimpan video/audio yang Anda miliki atau yang pemiliknya mengizinkan untuk diunduh.

## 1. Persiapan (Ubuntu / Linux Mint)

```bash
sudo apt update
sudo apt install python3-venv python3-pip ffmpeg -y
```

## 2. Setup project

```bash
cd youtube-downloader
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Jalankan

```bash
python main.py
```

## Fitur

- UI desktop dark modern
- Input URL dan pemeriksaan metadata
- Mode video MP4 / audio MP3
- Pilihan kualitas video
- Custom output folder
- Progress, kecepatan, estimasi waktu
- Cancel download
- Riwayat unduhan lokal

## Catatan

- FFmpeg diperlukan untuk menggabungkan stream video/audio terpisah dan ekstraksi MP3.
- Gunakan hanya untuk konten yang Anda miliki atau yang secara eksplisit diizinkan untuk diunduh.
- yt-dlp dan YouTube dapat berubah; jika ekstraksi gagal, perbarui yt-dlp dengan `pip install -U yt-dlp`.


## Perbaikan versi ini
- Perbaikan kompatibilitas ETA: tidak lagi memanggil `yt_dlp.utils.format_eta`.
- Thumbnail diunduh pada worker metadata dan ditampilkan sebagai gambar di area preview.
- Progress menampilkan status pemrosesan setelah transfer selesai.

## Transkripsi audio/video ke teks

Versi ini menambahkan transkripsi lokal dengan Faster-Whisper:
- Pilih file MP3, WAV, M4A, AAC, FLAC, OGG, OPUS, MP4, MKV, MOV, WEBM, atau AVI.
- Pilih deteksi bahasa otomatis, Indonesia, English, atau Melayu.
- Pilih model `base`, `small`, atau `medium`.
- Hasil dibuat sebagai file `_transcript.txt` dan `_transcript.srt` di folder yang sama dengan file sumber.
- Hasil teks juga ditampilkan di jendela aplikasi.

Catatan:
- FFmpeg harus terpasang agar format media yang didukung dapat dibaca.
- Model Whisper diunduh saat pertama kali dipakai; koneksi internet diperlukan untuk pengunduhan model awal.
- Transkripsi berjalan lokal di CPU dengan mode int8. Model lebih besar biasanya lebih akurat tetapi lebih lambat dan membutuhkan RAM lebih besar.
- Pastikan Anda memiliki hak atau izin untuk memproses konten tersebut.

## Terjemahan transkrip

Versi ini menambahkan terjemahan transkrip ke berbagai bahasa:
- Pilih bahasa tujuan pada bagian **Terjemahkan Transkrip**.
- Terjemahan TXT dibuat dari teks hasil Whisper.
- Subtitle SRT diterjemahkan per cue, sementara nomor cue dan timestamp dipertahankan.
- Hasil terjemahan disimpan di folder file sumber.
- Terjemahan memakai `deep-translator` (Google Translate) dan memerlukan koneksi internet.
- Jangan gunakan hasil terjemahan mesin sebagai terjemahan tersertifikasi atau untuk keputusan kritis tanpa pemeriksaan manusia.

## AI Dubbing / Voice Localization

Dubbing offline menggunakan Meta MMS-TTS (VITS) untuk:
- Indonesian: `facebook/mms-tts-ind`
- Sundanese: `facebook/mms-tts-sun`
- Javanese: `facebook/mms-tts-jav`

Workflow:
1. Pilih file audio/video dan buat transkrip.
2. Terjemahkan transkrip ke bahasa sasaran.
3. Pilih bahasa dubbing dan klik **Buat Dubbing**.
4. WAV dubbing dibuat dengan penempatan cue mengikuti timestamp subtitle.
5. Jika sumber merupakan video, FFmpeg membuat MP4 baru dengan video asli dan audio dubbing (audio asli diganti).

Model diunduh dari Hugging Face pada penggunaan pertama. Butuh koneksi internet dan ruang disk. Pemrosesan TTS berjalan lokal setelah model tersedia.

**Lisensi penting:** Meta MMS-TTS model checkpoints berlisensi CC-BY-NC 4.0 (non-komersial). Jangan gunakan model ini untuk layanan atau produksi komersial tanpa memastikan izin/lisensi yang sesuai. Model ini menyediakan satu suara per checkpoint; pemilihan gender/voice cloning tidak tersedia pada implementasi ini. Hasil bahasa lokal perlu ditinjau penutur asli, terutama dialek, intonasi, dan istilah.
