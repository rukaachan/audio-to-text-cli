import argparse

def parse_arguments():
    """
    Parses command-line arguments.
    """
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
    parser.add_argument("--output-format", type=str, default="txt", choices=["txt", "srt", "vtt"],
                        help="Output format for the transcription (default: txt)")
    parser.add_argument("--resume", type=str, help="Path to a progress file to resume transcription from.")
    parser.add_argument("--engine", type=str, default="google", choices=["google"],
                        help="Transcription engine to use (default: google)")
    
    return parser.parse_args()
