import streamlit as st
import numpy as np
from transformers import pipeline
import io
import wave

@st.cache_resource
def load_whisper_pipeline():
    pipe = pipeline(
        "automatic-speech-recognition",
        model="./whisper-tiny",
        tokenizer="./whisper-tiny"
    )
    return pipe

def transcribe_with_wave(audio_bytes, pipe):
    """Using Python's built-in wave module - no external dependencies"""
    try:
        # Create a BytesIO object from audio bytes
        audio_io = io.BytesIO(audio_bytes)
        
        # Open with wave module
        with wave.open(audio_io, 'rb') as wav_file:
            # Get audio parameters
            frames = wav_file.getnframes()
            sample_rate = wav_file.getframerate()
            sample_width = wav_file.getsampwidth()
            channels = wav_file.getnchannels()
            
            # Read raw audio data
            raw_audio = wav_file.readframes(frames)
        
        # Convert to numpy array
        if sample_width == 1:  # 8-bit
            audio_data = np.frombuffer(raw_audio, dtype=np.uint8).astype(np.float32)
            audio_data = (audio_data - 128) / 128.0
        elif sample_width == 2:  # 16-bit
            audio_data = np.frombuffer(raw_audio, dtype=np.int16).astype(np.float32)
            audio_data = audio_data / 32768.0
        elif sample_width == 4:  # 32-bit
            audio_data = np.frombuffer(raw_audio, dtype=np.int32).astype(np.float32)
            audio_data = audio_data / 2147483648.0
        
        # Handle stereo to mono conversion
        if channels == 2:
            audio_data = audio_data.reshape(-1, 2).mean(axis=1)
        
        # Simple resampling to 16kHz if needed
        if sample_rate != 16000:
            duration = len(audio_data) / sample_rate
            new_length = int(duration * 16000)
            audio_data = np.interp(
                np.linspace(0, len(audio_data), new_length),
                np.arange(len(audio_data)),
                audio_data
            )
        
        # Transcribe
        result = pipe(audio_data)
        return result["text"].strip()
        
    except Exception as e:
        st.error(f"Transcription error: {e}")
        return ""

# Load pipeline
pipe = load_whisper_pipeline()

audio = st.audio_input(label="Record some audio to transcribe")

if audio:
    with st.spinner("Transcribing audio..."):
        audio_bytes = audio.getvalue()
        transcription = transcribe_with_wave(audio_bytes, pipe)
        
        if transcription:
            st.write("**Transcription:**")
            st.write(transcription)
