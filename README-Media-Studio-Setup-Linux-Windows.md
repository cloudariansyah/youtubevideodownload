# Media Studio — Setup Linux & Windows (Panduan Tanpa Terminal)

Panduan ini menjelaskan cara menyiapkan dan menjalankan Media Studio melalui antarmuka grafis (GUI), tanpa mengetik perintah terminal untuk penggunaan sehari-hari.

> **Penting — kondisi distribusi saat ini:** source project Python (`main.py`, `requirements.txt`) bukan installer mandiri. Python dan seluruh dependency harus sudah dipasang terlebih dahulu. Launcher desktop hanya menghilangkan kebutuhan membuka terminal saat menjalankan aplikasi. Untuk pengalaman instalasi 100% tanpa terminal sejak awal, developer perlu menyediakan paket aplikasi siap pakai: AppImage/installer Linux dan `.exe` Windows yang sudah membundel runtime serta dependency.

---

## 1. Struktur folder project

Setelah ZIP diekstrak, struktur project minimal seperti ini:

```text
MediaStudio/
├── main.py
├── workers.py
├── downloader.py
├── transcribe_worker.py
├── translation_worker.py
├── dubbing_worker.py
├── requirements.txt
├── README.md
├── launch.sh
├── .venv/                 # Linux, setelah environment disiapkan
└── ...
```

Jangan memisahkan `main.py` dari file Python pendukungnya. Simpan folder project di lokasi tetap.

---

# A. Ubuntu / Linux Mint

## 2. Persiapan melalui GUI

1. Unduh ZIP Media Studio.
2. Buka **Files** (file manager).
3. Buka folder **Downloads**.
4. Klik kanan ZIP, pilih **Extract Here** atau **Extract To…**.
5. Pindahkan folder hasil ekstraksi ke lokasi tetap, misalnya `Home/MediaStudio`.

### Prasyarat sistem

Pastikan komponen berikut tersedia:
- Python 3.10–3.12 yang sesuai dengan dependency project.
- FFmpeg.
- Library GUI Qt yang diperlukan oleh PySide6.
- Koneksi internet saat mengunduh dependency dan model AI pertama kali.

Komponen sistem seperti Python dan FFmpeg dapat dipasang melalui aplikasi **Software Manager** jika tersedia pada distro. Ketersediaan versi yang sesuai berbeda antar distro.

## 3. Setup Python environment

**Batasan versi source saat ini:** pembuatan virtual environment dan instalasi `requirements.txt` belum disediakan sebagai wizard GUI. Langkah awal ini memerlukan salah satu dari:
- setup satu kali oleh administrator/developer melalui terminal; atau
- paket siap pakai yang sudah membundel Python dan dependency.

Setelah `.venv` tersedia di dalam folder project, penggunaan berikutnya dapat dilakukan tanpa terminal.

## 4. Membuat launcher menu Applications

Jika file `launch.sh` sudah tersedia di folder project:

1. Buka **Files**.
2. Klik kanan `launch.sh` → **Properties**.
3. Buka tab **Permissions**.
4. Aktifkan **Allow executing file as program**.
5. Tutup jendela Properties.
6. Klik dua kali `launch.sh`.
7. Jika muncul pilihan, pilih **Run** atau **Run in Terminal**. Pilih **Run** agar aplikasi dibuka sebagai GUI.

Untuk menampilkan aplikasi di menu Applications, file menu `.desktop` harus dibuat satu kali. Pada source version saat ini, pembuatan file tersebut menggunakan terminal atau perlu disediakan oleh paket installer. Setelah file menu terpasang, cari **Media Studio** dari menu Applications dan klik untuk menjalankan.

Contoh isi `launch.sh` untuk virtual environment bernama `.venv`:

```bash
#!/bin/bash
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$APP_DIR"
exec "$APP_DIR/.venv/bin/python" "$APP_DIR/main.py"
```

Jika environment bernama `venv`, ubah `.venv` menjadi `venv`.

## 5. Membuat shortcut Desktop (opsional)

Jika file `media-studio.desktop` sudah dibuat oleh installer:

1. Buka `~/.local/share/applications` melalui Files.
2. Salin `media-studio.desktop`.
3. Tempel ke folder Desktop.
4. Klik kanan shortcut dan pilih **Allow Launching** atau **Trust and Launch** jika pilihan itu tersedia.

---

# B. Windows 10 / Windows 11

## 6. Persiapan melalui GUI

1. Unduh ZIP Media Studio.
2. Buka **File Explorer** → **Downloads**.
3. Klik kanan ZIP → **Extract All…**.
4. Pilih folder tujuan, misalnya `Documents\MediaStudio`.
5. Klik **Extract**.

### Prasyarat sistem

Source project membutuhkan:
- Python 3.10–3.12 yang kompatibel dengan dependency.
- FFmpeg yang dapat ditemukan oleh aplikasi.
- Dependency Python dari `requirements.txt`.
- Koneksi internet untuk mengunduh dependency dan model AI pertama kali.

Python dapat dipasang dari installer resmi Windows dengan opsi **Add Python to PATH**. Namun instalasi dependency dari `requirements.txt` pada source version saat ini belum memiliki wizard GUI.

## 7. Menjalankan aplikasi dari File Explorer

Jika Python environment sudah disiapkan dan file `launch.bat` tersedia, pengguna dapat menjalankan aplikasi dengan klik dua kali file tersebut.

Contoh isi `launch.bat`:

```bat
@echo off
set "APP_DIR=%~dp0"
cd /d "%APP_DIR%"
"%APP_DIR%.venv\Scripts\pythonw.exe" "%APP_DIR%main.py"
```

`pythonw.exe` menjalankan aplikasi GUI tanpa membuka jendela console. Pastikan folder `.venv` sudah dibuat dan dependency sudah terpasang sebelum menjalankan launcher.

Untuk membuat shortcut:
1. Klik kanan `launch.bat`.
2. Pilih **Show more options** jika diperlukan.
3. Pilih **Create shortcut**.
4. Pindahkan shortcut ke Desktop atau pin ke Start.

> Jika `pythonw.exe` tidak ditemukan, periksa apakah virtual environment `.venv` sudah ada dan Python telah terpasang dengan benar.

## 8. Instalasi 100% tanpa terminal di Windows

Untuk pengguna akhir, bentuk distribusi yang disarankan adalah installer `.exe` yang dibuat developer, misalnya:
- PyInstaller untuk membundel aplikasi dan dependency Python.
- Inno Setup untuk membuat wizard installer Windows.
- FFmpeg disertakan atau dipasang sebagai bagian dari installer.
- Shortcut Start Menu dan Desktop dibuat otomatis.

Dengan paket tersebut, pengguna cukup:
1. Klik dua kali `MediaStudio-Setup.exe`.
2. Ikuti wizard instalasi.
3. Klik **Finish**.
4. Jalankan Media Studio dari Start Menu atau Desktop.

Source ZIP saat ini belum sama dengan installer `.exe` tersebut.

---

# C. Alur penggunaan aplikasi

Setelah environment atau paket aplikasi siap, pengguna dapat membuka Media Studio melalui menu/shortcut.

1. **Download** — masukkan URL dan pilih format video atau audio.
2. **Transcription** — pilih file audio/video, lalu buat transkrip TXT dan SRT.
3. **Translation** — pilih bahasa tujuan dan terjemahkan transkrip.
4. **Dubbing** — pilih bahasa suara yang tersedia dan buat audio dubbing.
5. **Output** — periksa file hasil pada folder output.

## D. Model AI dan koneksi internet

- Faster-Whisper dapat mengunduh model saat pertama kali digunakan.
- Model TTS dapat diunduh saat pertama kali digunakan.
- Fitur terjemahan berbasis layanan online memerlukan koneksi internet.
- Model AI dapat membutuhkan ruang disk, RAM, dan waktu pemrosesan yang cukup.
- Lisensi model harus diperiksa sebelum penggunaan komersial. Khusus checkpoint Meta MMS-TTS yang digunakan untuk bahasa lokal, periksa ketentuan lisensinya sebelum distribusi atau penggunaan bisnis.

---

# E. Troubleshooting

## Aplikasi tidak terbuka di Linux

- Pastikan `launch.sh` memiliki izin **Allow executing file as program**.
- Pastikan `.venv/bin/python` tersedia.
- Pastikan FFmpeg dan library Qt sistem telah terpasang.
- Untuk melihat detail error, jalankan aplikasi melalui terminal atau minta administrator memeriksa log.

## Aplikasi tidak terbuka di Windows

- Pastikan `.venv\Scripts\pythonw.exe` tersedia.
- Pastikan dependency telah terpasang.
- Jika perlu melihat pesan error, jalankan `launch.bat` yang menggunakan `python.exe` (bukan `pythonw.exe`) agar pesan error terlihat.

## Transkripsi gagal

- Pastikan file audio/video dapat dibuka.
- Pastikan FFmpeg dan dependency Faster-Whisper kompatibel.
- Pastikan model Whisper sudah terunduh.
- Periksa ruang disk dan RAM.

## Dubbing gagal

- Pastikan subtitle hasil terjemahan tersedia.
- Pastikan model TTS bahasa tujuan dapat diunduh dan dimuat.
- Periksa kompatibilitas PyTorch, Transformers, dan model TTS.

---

## F. Ringkasan status instalasi tanpa terminal

| Tahap | Linux source ZIP | Windows source ZIP |
|---|---|---|
| Ekstrak ZIP melalui GUI | Ya | Ya |
| Jalankan setelah environment siap | Ya, melalui launcher | Ya, melalui `launch.bat` |
| Instal Python/dependency dari source tanpa terminal | Belum tersedia | Belum tersedia |
| Shortcut aplikasi | Perlu file `.desktop` | Bisa dibuat dari shortcut |
| Instalasi penuh satu klik | Perlu paket AppImage/installer | Perlu installer `.exe` |

**Rekomendasi distribusi resmi:** sediakan dua paket untuk pengguna akhir:
- `MediaStudio-Linux.AppImage` atau paket Linux setara.
- `MediaStudio-Setup-Windows.exe`.

Dengan paket tersebut, pengguna tidak perlu membuat virtual environment, menjalankan pip, atau membuka terminal untuk instalasi dan penggunaan normal.
