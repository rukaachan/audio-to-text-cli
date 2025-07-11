# Audio-to-Text CLI Tool

This is a command-line interface (CLI) tool that converts voice or recorded audio files (up to 1GB) into text. It supports multiple audio formats and uses the Google Speech Recognition API for transcription. The tool is designed to be modular and easily extensible for future improvements, with a focus on performance, lightweightness, and robust error handling.

## Features

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

- Python 3.x
- [SpeechRecognition](https://pypi.org/project/SpeechRecognition/)
- [PyDub](https://pypi.org/project/pydub/)
- [tqdm](https://pypi.org/project/tqdm/) (for progress bar)
- [pytest](https://docs.pytest.org/en/stable/) (for running tests)
- [pytest-mock](https://pytest-mock.readthedocs.io/en/latest/) (for testing)

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

   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the CLI tool using the following command:

```bash
python main.py input_audio_file output_text_file
```

For example, if you have an audio file named `audio.mp3`:

```bash
python main.py audio.mp3 output_text.txt
```

### Optional Arguments

- `--chunk`: Specify the chunk duration in seconds (default: 60).
- `--language`: Specify the language code for transcription (default: `id-ID` for Indonesian).
- `--engine`: Specify the transcription engine to use (google) (default: `google`).
- `--output-format`: Specify the output format (txt, srt, vtt) (default: `txt`).
- `--resume`: Path to a progress file to resume transcription from.

Example with optional parameters:

```bash
python main.py audio.mp3 output_text.txt --chunk 45 --language en-US --output-format srt
```

To resume a transcription:

```bash
python main.py audio.mp3 output_text.txt --resume progress.json
```

## Running Tests

To run the tests, navigate to the project root directory and execute:

```bash
pytest
```
