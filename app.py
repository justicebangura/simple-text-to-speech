import streamlit as st
from PyPDF2 import PdfReader
from gtts import gTTS
import tempfile
import os
import io
import uuid
from pydub import AudioSegment

st.title("Text-to-Speech")

# File uploader
uploaded_file = st.file_uploader("Upload a PDF or Text file", type=["pdf", "txt"])

# Optional: Allow user to input text directly
user_input = st.text_area("Or enter text here:")

def extract_text(file):
    if file.type == "application/pdf":
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    elif file.type == "text/plain":
        return str(file.read(), "utf-8")
    else:
        return None

def split_text(text, max_length=5000):
    # Split text into chunks of max_length characters
    return [text[i:i+max_length] for i in range(0, len(text), max_length)]

def text_to_speech(text):
    text_chunks = split_text(text)
    combined = AudioSegment.empty()
    for chunk in text_chunks:
        tts = gTTS(chunk)
        with io.BytesIO() as f:
            tts.write_to_fp(f)
            f.seek(0)
            audio_segment = AudioSegment.from_file(f, format='mp3')
            combined += audio_segment
    # Save combined audio to a file
    combined_file_name = os.path.join(tempfile.gettempdir(), str(uuid.uuid4()) + '.mp3')
    combined.export(combined_file_name, format='mp3')
    return combined_file_name

if uploaded_file is not None:
    text = extract_text(uploaded_file)
    if text:
        st.success("Text extracted from the uploaded file.")
    else:
        st.error("Failed to extract text from the file.")
elif user_input:
    text = user_input
else:
    text = None

if text:
    st.text_area("Extracted Text", text, height=200)
    if st.button("Convert to Speech"):
        with st.spinner("Converting text to speech..."):
            audio_file_path = text_to_speech(text)
            st.success("Conversion completed!")
            # Display audio player
            audio_file = open(audio_file_path, 'rb')
            audio_bytes = audio_file.read()
            st.audio(audio_bytes, format='audio/mp3')
            # Provide option to download the audio file
            st.download_button('Download Audio', audio_bytes, file_name='output.mp3')
            # Clean up
            audio_file.close()
            os.remove(audio_file_path)
