# afeat - Universal Personal CLI Utility & Media Converter

`afeat` adalah personal CLI utility tool serbaguna berbasis Python yang dapat dipanggil dari folder mana pun di terminal sistem operasi Windows (PowerShell, CMD, Bash) dan memproses file di Current Working Directory (`Path.cwd()`).

---

## Fitur Utama

1. **Batch & Single-File Conversion**:
   - Mendukung gambar modern, audio, video, dan dokumen.
   - Menggunakan sintaks bersih dan aman dari konflik shell.
   - Bisa memproses 1 file spesifik atau seluruh file berekstensi sama di folder aktif.
2. **Social Media Downloader**:
   - Mengunduh video atau audio dari YouTube, TikTok, Instagram, Twitter/X, Facebook, Reddit, dll., langsung ke direktori aktif.
3. **CWD File Inspector**:
   - Menampilkan ringkasan jenis file, jumlah, dan total ukuran di folder tempat terminal berada.
4. **Arsitektur Modular (Registry Pattern)**:
   - Setiap tipe file ditangani oleh modul terpisah di dalam folder `features/`.
   - Mudah ditambah format baru di masa depan tanpa mengubah kode yang ada.

---

## Panduan Sintaks Perintah (Universal Commands)

### 1. Konversi Format File (`afeat convert`)

#### A. Konversi Seluruh File Berekstensi Sama di Folder Aktif:
```bash
# Ubah semua file PNG menjadi WebP
afeat convert png webp

# Ubah semua foto iPhone (HEIC) menjadi JPG
afeat convert heic jpg

# Ubah semua rekaman audio WAV menjadi MP3
afeat convert wav mp3

# Ubah semua video MP4 menjadi audio MP3
afeat convert mp4 mp3

# Ubah video MP4 menjadi animasi GIF berkualitas tinggi
afeat convert mp4 gif

# Ubah dokumen Markdown menjadi HTML
afeat convert md html
```

#### B. Konversi 1 File Spesifik:
Cukup sebutkan nama filenya diikuti format tujuan:
```bash
# Konversi hanya file 'banner.png' menjadi 'banner.webp'
afeat convert banner.png webp

# Konversi hanya file 'recording.wav' menjadi 'recording.mp3'
afeat convert recording.wav mp3

# Konversi hanya file 'clip.mp4' menjadi 'clip.gif'
afeat convert clip.mp4 gif
```
*Catatan: Anda juga bisa menuliskan kata "to" jika terbiasa (misal: `afeat convert banner.png to webp`).*

#### C. Konversi Otomatis Berdasarkan Format Target Saja:
Jika Anda hanya memasukkan format target, `afeat` akan memindai semua file di folder aktif yang kompatibel dan mengubahnya:
```bash
# Mengonversi semua gambar (.jpg, .png, .heic, dll) di folder ini menjadi .webp
afeat convert webp

# Mengonversi semua audio/video di folder ini menjadi .mp3
afeat convert mp3
```

#### D. Opsi & Parameter Tambahan:
- `-q`, `--quality <angka>`: Mengatur kualitas gambar (1–100) atau bitrate audio (128, 192, 256, 320).
  ```bash
  afeat convert png webp -q 90
  afeat convert wav mp3 -q 320
  ```
- `-o`, `--output <folder>`: Menyimpan file hasil ke subfolder tertentu.
  ```bash
  afeat convert png webp -o converted_images
  ```
- `-r`, `--recursive`: Memproses file di subfolder secara rekursif.
  ```bash
  afeat convert heic jpg -r
  ```
- `-d`, `--delete-source`: Menghapus file sumber asli setelah konversi berhasil (misal: convert mp4 ke mp3 lalu hapus mp4 aslinya).
  ```bash
  afeat convert mp4 mp3 -d
  afeat convert video.mp4 mp3 -d
  afeat convert heic jpg -d
  ```

---

### 2. Download Media Sosial ke Folder Aktif (`afeat vid`)

Mengunduh video/audio media sosial langsung ke folder terminal saat ini:

```bash
# Download video kualitas terbaik ke direktori aktif
afeat vid "https://www.youtube.com/watch?v=VIDEO_ID"

# Download audio saja (MP3)
afeat vid "https://www.youtube.com/watch?v=VIDEO_ID" --audio

# Tentukan resolusi (misal 1080p atau 720p)
afeat vid "https://www.youtube.com/watch?v=VIDEO_ID" -q 1080
```

---

### 3. Informasi Direktori & Daftar Format

```bash
# Melihat rekapitulasi file di direktori aktif saat ini
afeat info

# Melihat seluruh ekstensi dan format yang didukung
afeat list

# Melihat bantuan perintah
afeat --help
afeat convert --help
afeat vid --help
```

---

## Format File yang Didukung

| Kategori | Ekstensi Input | Format Output Target | Engine |
|---|---|---|---|
| **Gambar** | `jpg`, `jpeg`, `png`, `webp`, `heic`, `heif`, `bmp`, `tiff`, `tif`, `gif`, `ico` | `webp`, `jpg`, `jpeg`, `png`, `bmp`, `tiff`, `ico`, `pdf` | Pillow & pillow-heif |
| **Audio** | `mp3`, `wav`, `m4a`, `aac`, `flac`, `opus`, `ogg`, `wma` | `mp3`, `m4a`, `wav`, `flac`, `opus`, `ogg`, `aac` | FFmpeg |
| **Video** | `mp4`, `mkv`, `mov`, `avi`, `webm`, `flv`, `wmv`, `m4v`, `ts` | `mp4`, `mkv`, `webm`, `mov`, `avi`, `gif` *(animasi)*, `mp3` *(ekstrak audio)*, `wav`, `m4a`, `flac`, `ogg` | FFmpeg |
| **Dokumen** | `md`, `txt`, `pdf` | `html`, `txt`, `pdf` | markdown & pypdf |

---

## Struktur Kode Modular

```text
d:/Project/aFeature/
├── features/                      # 1 folder menampung semua modul fitur
│   ├── __init__.py                # Registrasi converter otomatis
│   ├── base.py                    # BaseConverter (Abstract Base Class)
│   ├── registry.py                # ConverterRegistry (Dispatcher)
│   ├── img.py                     # Handler konversi & kompresi gambar
│   ├── audio.py                   # Handler audio & bitrate
│   ├── video.py                   # Handler video, remuxing & GIF generator
│   ├── doc.py                     # Handler dokumen (Markdown, PDF text)
│   └── vid_downloader.py          # Handler download medsos via yt-dlp
├── main.py                        # Entry point CLI (argparse & CWD handler)
├── afeat.cmd                      # Windows wrapper untuk eksekusi global
├── requirements.txt               # Daftar paket dependensi
├── pyproject.toml                 # Konfigurasi pip package
└── README.md                      # Dokumentasi
```
