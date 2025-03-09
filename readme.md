# Audio-to-Text CLI Tool

This is a command-line interface (CLI) tool that converts voice or recorded audio files (up to 1GB) into text. It supports multiple audio formats and uses the Google Speech Recognition API for transcription. The tool is designed to be modular and easily extensible for future improvements.

## Features

- **Multiple Audio Formats:** Supports WAV, MP3, FLAC, OGG, M4A.
- **Automatic Conversion:** Converts non-WAV files to WAV format before transcription.
- **Chunk Processing:** Handles large audio files by splitting them into manageable 60-second chunks.
- **Error Handling:** Provides informative error messages for unsupported formats, network issues, and transcription errors.
- **Customizable:** Options to change chunk duration and transcription language.

## Requirements

- Python 3.x
- [SpeechRecognition](https://pypi.org/project/SpeechRecognition/)
- [PyDub](https://pypi.org/project/pydub/)
- [PyAudio](https://pypi.org/project/PyAudio/) (may require additional system dependencies)

## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/rukaachan/audio-to-text-cli
   cd audio-to-text-cli
   ```

2. **Set Up a Virtual Environment (Recommended):**

   ```bash
   python -m venv myenv
   source myenv/bin/activate  # On Windows: myenv\Scripts\activate
   ```

3. **Install Dependencies:**

   You can install the required libraries using pip:

   ```bash
   pip install SpeechRecognition pydub pyaudio
   ```

   Alternatively, you may create a `requirements.txt` file with the following content:

   ```text
   SpeechRecognition
   pydub
   pyaudio
   ```

   And install with:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the CLI tool using the following command:

```bash
python index.py input_audio_file output_text_file
```

For example, if you have an audio file named `audio.mp3`:

```bash
python index.py audio.mp3 output_text.txt
```

### Optional Arguments

- `--chunk`: Specify the chunk duration in seconds (default: 60).
- `--language`: Specify the language code for transcription (default: `id-ID` for Indonesian).

Example with optional parameters:

```bash
python index.py audio.mp3 output_text.txt --chunk 45 --language id-ID
```
