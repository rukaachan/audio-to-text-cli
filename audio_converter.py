import os
import tempfile
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
        # Create a temporary WAV file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav_file:
            wav_path = temp_wav_file.name

        audio = AudioSegment.from_file(input_path, format=file_extension)
        audio.export(wav_path, format="wav")

        def cleanup():
            try:
                os.remove(wav_path)
            except OSError:
                pass

        return wav_path, cleanup
    except FileNotFoundError:
        raise FileNotFoundError(f"Input audio file not found: '{input_path}'")
    except Exception as e:
        raise ValueError(f"Failed to convert audio file '{input_path}': {e}")
