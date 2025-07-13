# Audio-to-Text CLI Tool

This is a command-line interface (CLI) tool that converts voice or recorded audio files (up to 1GB) into text. It supports multiple audio formats and uses transcription engines like Google Speech Recognition or the local, high-accuracy Faster Whisper. The tool is designed to be modular and easily extensible for future improvements, with a focus on performance, lightweightness, and robust error handling.

## Features

- **Multiple Transcription Engines:** Supports both Google's Speech Recognition API and the local `faster-whisper` model for high-accuracy, offline transcription.
- **Multiple Audio Formats:** Supports WAV, MP3, FLAC, OGG, M4A.
- **Automatic Conversion:** Converts non-WAV files to WAV format before transcription.
- **Chunk Processing:** Handles large audio files by splitting them into manageable 60-second chunks.
- **Improved Error Handling:** Provides more specific and actionable error messages for unsupported formats, network issues, and transcription errors.
- **Robust Temporary File Management:** Uses Python's `tempfile` module for secure and automatic cleanup of temporary WAV files.
- **Transcription Progress Indicator:** Displays a progress bar during transcription for better user experience.
- **Customizable:** Options to change chunk duration, transcription language, and transcription engine.
- **Structured Output Options:** Supports output in plain text, SRT, and VTT formats.
- **Resume Functionality:** Allows resuming interrupted transcriptions from the last successfully processed chunk.

## Requirements

- **FFmpeg/libav:** `pydub` requires FFmpeg or libav to be installed and accessible in your system's PATH. You can download it from [ffmpeg.org](https://ffmpeg.org/download.html) or install via your system's package manager (e.g., `sudo apt-get install ffmpeg` on Debian/Ubuntu, `brew install ffmpeg` on macOS).

- Python 3.x
- [SpeechRecognition](https://pypi.org/project/SpeechRecognition/) (for Google engine)
- [faster-whisper](https://pypi.org/project/faster-whisper/) (for Whisper engine)
    *   **Note on Python 3.13 Compatibility**: Users of Python 3.13 may encounter a `DeprecationWarning` related to the `aifc` module from the `speech_recognition` library. While tests currently pass despite this warning, for full compatibility and to avoid potential future issues, consider using Python 3.12 or earlier if you experience unexpected behavior.
- [PyDub](https://pypi.org/project/pydub/)
- [tqdm](https://pypi.org/project/tqdm/) (for progress bar)
- [pytest](https://docs.pytest.org/en/stable/) (for running tests)
- [pytest-mock](https://pytest-mock.readthedocs.io/en/latest/) (for testing)

## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/rukaachan/audio-to-text-cli # Or your forked repository URL
   cd audio-to-text-cli
   ```

2. **Set Up a Virtual Environment (Recommended):**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the CLI tool using the following command:

```bash
python main.py input_audio_file output_text_file
```

For example, if you have an audio file named `dummy_audio.mp3` (provided in the repository):

```bash
python main.py dummy_audio.mp3 output_text.txt
```
*Note: `output_text.txt` is a general placeholder for your output file. A specific example output file, `dummy_output.txt`, is ignored by Git.*

### Optional Arguments

- `--chunk`: Specify the chunk duration in seconds (default: 60).
- `--language`: Specify the language code for transcription (default: `id-ID` for Indonesian).
- `--engine`: Specify the transcription engine to use (`google`, `faster-whisper`) (default: `google`).
- `--output-format`: Specify the output format (txt, srt, vtt) (default: `txt`).
- `--resume`: Path to a progress file (e.g., `progress.json`) to resume transcription from. This JSON file is generated during a previous run and contains information about processed chunks.

Example with optional parameters:

```bash
python main.py dummy_input.mp3 output_text.txt --chunk 45 --language en-US --output-format srt --engine faster-whisper
```

To resume a transcription:

```bash
python main.py dummy_audio.mp3 output_text.txt --resume progress.json
```

- `--temp-dir`: Specify a custom temporary directory for audio processing (optional).

Example using `--temp-dir`:

```bash
python main.py dummy_audio.mp3 output_text.txt --temp-dir /tmp/my_audio_temp
```

## Running Tests

To run the tests, navigate to the project root directory and execute:

```bash
pytest
```
