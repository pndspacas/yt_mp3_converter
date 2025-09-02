import streamlit as st
import os
import re
from yt_dlp import YoutubeDL
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1
import imageio_ffmpeg as ffmpeg  # garante FFmpeg no ambiente

# Pasta Downloads
downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
if not os.path.exists(downloads_folder):
    downloads_folder = os.path.join(os.path.expanduser("~"), "Transferências")

st.title("YouTube MP3 Downloader (320 kbps com Trim)")

# URL
url = st.text_input("Cole o link do YouTube:")

# Trim inputs
col1, col2 = st.columns(2)
start_input = col1.text_input("Início (segundos ou mm:ss):", "")
end_input = col2.text_input("Fim (segundos ou mm:ss):", "")

def parse_time(t):
    """Converte mm:ss ou ss em segundos"""
    if not t:
        return None
    if ":" in t:
        m, s = t.split(":")
        return int(m)*60 + int(s)
    return int(t)

if st.button("Baixar MP3"):
    if not url:
        st.warning("⚠️ Insira o link do YouTube.")
    else:
        st.info("⏳ Baixando e processando metadata...")
        try:
            start_time = parse_time(start_input)
            end_time = parse_time(end_input)

            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(downloads_folder, '%(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '320',
                }],
                'restrictfilenames': True,
                'noplaylist': True,
            }

            # Trim direto no download
            if start_time is not None or end_time is not None:
                ydl_opts['download_ranges'] = {
                    'ranges': [{'start_time': start_time, 'end_time': end_time}]
                }

            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                mp3_file = ydl.prepare_filename(info)
                mp3_file = os.path.splitext(mp3_file)[0] + ".mp3"

            # Limpeza do título
            original_title = info['title']
            clean_title = re.sub(r"\(.*?\)|\[.*?\]", "", original_title)
            clean_title = re.sub(r"(?i)official video|lyric video|HD|HQ|video clip", "", clean_title).strip()

            # Extrair artista e música
            if " - " in clean_title:
                artist_name, track_name = map(str.strip, clean_title.split(" - ", 1))
            else:
                artist_name = info.get('uploader', 'Unknown')
                track_name = clean_title

            # Uppercase
            artist_name = artist_name.upper()
            track_name = track_name.upper()

            # Tags ID3
            audio = MP3(mp3_file, ID3=ID3)
            try:
                audio.add_tags()
            except:
                pass
            audio.tags.add(TIT2(encoding=3, text=track_name))
            audio.tags.add(TPE1(encoding=3, text=artist_name))
            audio.save()

            # Renomear arquivo
            safe_artist = re.sub(r'[\\/*?:"<>|]', "", artist_name)
            safe_track = re.sub(r'[\\/*?:"<>|]', "", track_name)
            new_filename = f"{safe_artist} - {safe_track}.mp3"
            new_path = os.path.join(downloads_folder, new_filename)
            os.rename(mp3_file, new_path)
            mp3_file = new_path

            st.success(f"✅ Download concluído!\nArquivo salvo em: {downloads_folder}\nNome do arquivo: {new_filename}")
        except Exception as e:
            st.error(f"❌ Falha no download ou processamento:\n{e}")
