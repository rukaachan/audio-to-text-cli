import argparse
import os
import sys
import speech_recognition as sr
from pydub import AudioSegment

# Supported input audio formats
SUPPORTED_FORMATS = ['wav', 'mp3', 'flac', 'ogg', 'm4a']

def convert_to_wav(input_path):
    """
    Converts an audio file to WAV format if needed.
    Returns the path to the WAV file.
    """
    file_extension = os.path.splitext(input_path)[1][1:].lower()
    if file_extension not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported audio format: '{file_extension}'. "
            f"Supported formats: {', '.join(SUPPORTED_FORMATS)}"
        )
    # If already WAV, return as-is.
    if file_extension == "wav":
        return input_path

    try:
        audio = AudioSegment.from_file(input_path, format=file_extension)
        wav_path = input_path + "_converted.wav"
        audio.export(wav_path, format="wav")
        return wav_path
    except Exception as e:
        raise Exception(f"Failed to convert audio file: {e}")

def transcribe_audio_in_chunks(wav_path, chunk_duration=60, language="id-ID"):
    """
    Transcribes a WAV file in chunks (to avoid overloading the API).
    chunk_duration is in seconds. Returns the full transcription.
    """
    recognizer = sr.Recognizer()
    transcription = ""

    try:
        audio = AudioSegment.from_wav(wav_path)
    except Exception as e:
        raise Exception(f"Error loading WAV file: {e}")

    total_duration = len(audio) / 1000.0  # Convert milliseconds to seconds

    # Open the audio file for recognition
    with sr.AudioFile(wav_path) as source:
        current_offset = 0
        while current_offset < total_duration:
            try:
                # Record a chunk from the source
                audio_data = recognizer.record(source, duration=chunk_duration)
                # Use Google Speech Recognition API with the desired language (Indonesian)
                text = recognizer.recognize_google(audio_data, language=language)
                transcription += text + " "
            except sr.UnknownValueError:
                transcription += "[Unrecognized Audio] "
            except sr.RequestError as e:
                transcription += f"[RequestError: {e}] "
            except Exception as e:
                transcription += f"[Error: {e}] "
            current_offset += chunk_duration

    return transcription.strip()

def get_audio_duration(wav_path):
    """
    Returns the duration of the audio file in seconds.
    """
    try:
        audio = AudioSegment.from_wav(wav_path)
        return len(audio) / 1000.0
    except Exception:
        return None

def main():
    parser = argparse.ArgumentParser(
        description="CLI tool to convert audio files to text using speech recognition. "
                    "Supported formats: wav, mp3, flac, ogg, m4a. "
                    "If necessary, the tool converts the file to WAV."
    )
    parser.add_argument("input_audio", help="Path to the input audio file")
    parser.add_argument("output_text", help="Path to the output text file")
    parser.add_argument("--chunk", type=int, default=60,
                        help="Chunk duration in seconds (default: 60)")
    parser.add_argument("--language", type=str, default="id-ID",
                        help="Language code for transcription (default: id-ID for Indonesian)")
    args = parser.parse_args()

    input_audio_path = args.input_audio
    output_text_path = args.output_text
    chunk_duration = args.chunk
    language = args.language

    if not os.path.exists(input_audio_path):
        print(f"Error: Input file '{input_audio_path}' does not exist.")
        sys.exit(1)

    # Warn if file is larger than 1GB
    file_size = os.path.getsize(input_audio_path)
    if file_size > 1 * 1024 * 1024 * 1024:
        print("Warning: File is larger than 1GB. Processing may be slow or problematic. "
              "Consider splitting the file.")

    try:
        # Convert input file to WAV if necessary
        wav_path = convert_to_wav(input_audio_path)
        print("Transcribing audio... This may take some time.")

        transcription = transcribe_audio_in_chunks(wav_path, chunk_duration=chunk_duration, language=language)
        duration = get_audio_duration(wav_path)

        # Write transcription and metadata to output file
        with open(output_text_path, "w", encoding="utf-8") as outfile:
            outfile.write("Transcription:\n")
            outfile.write(transcription)
            if duration is not None:
                outfile.write(f"\n\nAudio Duration (seconds): {duration:.2f}")
        
        print(f"Transcription completed. Output saved to '{output_text_path}'.")
    except Exception as error:
        print(f"Error: {error}")
        sys.exit(1)
    finally:
        # Remove temporary WAV file if a conversion was done
        if wav_path != input_audio_path and os.path.exists(wav_path):
            try:
                os.remove(wav_path)
            except Exception:
                print(f"Warning: Could not remove temporary file '{wav_path}'.")

if __name__ == "__main__":
    main()
