import speech_recognition as sr
from pydub import AudioSegment
from tqdm import tqdm

import tempfile
import os
import json

MS_PER_SECOND = 1000

def transcribe_audio_in_chunks(wav_path, chunk_duration=60, language="id-ID", start_chunk_index=0, resume_path=None):
    """
    Transcribes a WAV file in chunks (to avoid overloading the API).
    chunk_duration is in seconds. Returns a list of dictionaries, each containing
    'text', 'start_time', and 'end_time'.
    """
    recognizer = sr.Recognizer()
    transcribed_chunks = []

    try:
        audio = AudioSegment.from_wav(wav_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"WAV file not found: {wav_path}")
    except Exception as e:
        raise ValueError(f"Error loading WAV file {wav_path}: {e}")

    total_duration_ms = len(audio)  # Total duration in milliseconds
    chunk_duration_ms = chunk_duration * MS_PER_SECOND

    # Calculate number of chunks
    num_chunks = int(total_duration_ms / chunk_duration_ms) + (1 if total_duration_ms % chunk_duration_ms > 0 else 0)

    # Process each chunk for recognition
    for i in tqdm(range(start_chunk_index, num_chunks), unit="chunk", desc="Transcribing"):
        start_ms = i * chunk_duration_ms
        end_ms = min((i + 1) * chunk_duration_ms, total_duration_ms)
        
        chunk_audio = audio[start_ms:end_ms]
        
        # Export chunk to a temporary WAV file for SpeechRecognition
        temp_chunk_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_chunk_path = temp_chunk_file.name
        temp_chunk_file.close()
        chunk_audio.export(temp_chunk_path, format="wav")

        try:
            try:
                with sr.AudioFile(temp_chunk_path) as chunk_source:
                    audio_data = recognizer.record(chunk_source)
                    text = recognizer.recognize_google(audio_data, language=language)
                    transcribed_chunks.append({
                        "text": text,
                        "start_time": start_ms / 1000.0,  # Convert to seconds
                        "end_time": end_ms / 1000.0       # Convert to seconds
                    })
            except sr.UnknownValueError:
                transcribed_chunks.append({
                    "text": "[Unrecognized Audio]",
                    "start_time": start_ms / 1000.0,
                    "end_time": end_ms / 1000.0
                })
            except sr.RequestError as e:
                transcribed_chunks.append({
                    "text": f"[RequestError: {e}]",
                    "start_time": start_ms / 1000.0,
                    "end_time": end_ms / 1000.0
                })
            except Exception as e:
                transcribed_chunks.append({
                    "text": f"[Error during chunk transcription: {e}]",
                    "start_time": start_ms / 1000.0,
                    "end_time": end_ms / 1000.0
                })
        finally:
            # Clean up temporary chunk file
            try:
                if os.path.exists(temp_chunk_path):
                    os.remove(temp_chunk_path)
            except Exception as cleanup_error:
                print(f"Warning: Could not remove temporary file {temp_chunk_path}: {cleanup_error}")
        # Save progress after each chunk if resume_path is provided
        if resume_path:
            progress_data = {
                'transcribed_chunks': transcribed_chunks,
                'last_chunk_index': i
            }
def get_audio_duration(wav_path):
    """
    Returns the duration of the audio file in seconds.
    """
    try:
        audio = AudioSegment.from_wav(wav_path)
        return len(audio) / MS_PER_SECOND
    except FileNotFoundError:
        print(f"Warning: Audio file not found for duration check: {wav_path}")
        return None
    except Exception as e:
        print(f"Warning: Could not get audio duration for {wav_path}: {e}")
        return None




