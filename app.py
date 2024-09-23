import streamlit as st
from PyPDF2 import PdfReader
from gtts import gTTS
import tempfile
import os
import io
import uuid
from pydub import AudioSegment
import requests
import re

st.title("Text-to-Speech - STUDY HELP")

# File uploader
uploaded_file = st.file_uploader("Upload a PDF or Text file", type=["pdf", "txt"])

# Optional: Allow user to input text directly
user_input = st.text_area("Or enter text here:")

# Allow user to set maximum chunk size
max_length = st.number_input("Set maximum characters per chunk:", min_value=1000, max_value=10000, value=5000, step=500)

# Allow user to choose output option
output_option = st.radio("Select output option:", ('Single combined audio file', 'Split audio into chunks'))

def extract_text(file):
    if file.type == "application/pdf":
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
        return text
    elif file.type == "text/plain":
        return str(file.read(), "utf-8")
    else:
        return None

def normalize_text(text):
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    # Remove non-ASCII characters
    text = text.encode('ascii', 'ignore').decode('ascii')
    return text.strip()

def correct_grammar(text):
    url = 'https://api.languagetool.org/v2/check'
    data = {
        'text': text,
        'language': 'en-US'
    }
    response = requests.post(url, data=data)
    result = response.json()
    corrected_text = text
    for match in reversed(result['matches']):
        start = match['offset']
        end = start + match['length']
        if match['replacements']:
            replacement = match['replacements'][0]['value']
            corrected_text = corrected_text[:start] + replacement + corrected_text[end:]
    return corrected_text

def split_text(text, max_length):
    return [text[i:i+max_length] for i in range(0, len(text), max_length)]

def text_to_speech(text, max_length, progress_bar, status_text, output_option):
    text_chunks = split_text(text, max_length)
    total_chunks = len(text_chunks)
    combined = AudioSegment.empty()
    audio_files = []
    for i, chunk in enumerate(text_chunks):
        try:
            tts = gTTS(chunk)
            with io.BytesIO() as f:
                tts.write_to_fp(f)
                f.seek(0)
                audio_segment = AudioSegment.from_file(f, format='mp3')
            if output_option == 'Single combined audio file':
                combined += audio_segment
            else:
                # Save individual audio segment
                temp_file_name = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.mp3")
                audio_segment.export(temp_file_name, format='mp3')
                audio_files.append(temp_file_name)
            # Update progress indicators
            progress = (i + 1) / total_chunks
            progress_bar.progress(progress)
            status_text.text(f"Processing chunk {i+1}/{total_chunks}")
        except Exception as e:
            st.error(f"An error occurred while processing chunk {i+1}: {e}")
            continue
    if output_option == 'Single combined audio file':
        # Save combined audio to a file
        combined_file_name = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.mp3")
        combined.export(combined_file_name, format='mp3')
        return combined_file_name, None
    else:
        return None, audio_files

if uploaded_file is not None:
    text = extract_text(uploaded_file)
    if text:
        # Normalize and correct text
        text = normalize_text(text)
        text = correct_grammar(text)
        st.success("Text extracted and corrected.")
    else:
        st.error("Failed to extract text from the file.")
        st.stop()
elif user_input:
    text = user_input
    # Normalize and correct text
    text = normalize_text(text)
    text = correct_grammar(text)
else:
    text = None

if text:
    st.text_area("Corrected Text", text, height=200)
    if st.button("Convert to Speech"):
        with st.spinner("Converting text to speech..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            try:
                audio_file_path, audio_files = text_to_speech(
                    text, max_length, progress_bar, status_text, output_option
                )
                st.success("Conversion completed!")
            except Exception as e:
                st.error(f"An error occurred during conversion: {e}")
                progress_bar.empty()
                status_text.empty()
                st.stop()
            progress_bar.empty()
            status_text.empty()
            if output_option == 'Single combined audio file':
                # Display audio player and download option
                with open(audio_file_path, 'rb') as audio_file:
                    audio_bytes = audio_file.read()
                    st.audio(audio_bytes, format='audio/mp3')
                    st.download_button('Download Audio', audio_bytes, file_name='output.mp3')
                os.remove(audio_file_path)
            else:
                # Display each audio chunk
                for idx, audio_file_path in enumerate(audio_files):
                    st.write(f"Audio Chunk {idx+1}")
                    with open(audio_file_path, 'rb') as audio_file:
                        audio_bytes = audio_file.read()
                        st.audio(audio_bytes, format='audio/mp3')
                        st.download_button(
                            f'Download Chunk {idx+1}', 
                            audio_bytes, 
                            file_name=f'chunk_{idx+1}.mp3'
                        )
                    os.remove(audio_file_path)
else:
    st.info("Please upload a file or enter text to convert.")
