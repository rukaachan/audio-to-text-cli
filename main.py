import os
import sys
import tempfile
import json
import logging
from audio_converter import convert_to_wav
from transcriber import transcribe_audio_in_chunks
from cli import parse_arguments
from output_formatter import format_transcription

FILE_SIZE_WARNING_THRESHOLD = 1 * 1024 * 1024 * 1024  # 1GB

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def handle_resume(resume_path):
    """Handles resuming a transcription from a progress file."""
    transcribed_chunks = []
    start_chunk_index = 0
    if resume_path and os.path.exists(resume_path):
        try:
            with open(resume_path, 'r') as f:
                progress_data = json.load(f)
                transcribed_chunks = progress_data.get('transcribed_chunks', [])
                start_chunk_index = progress_data.get('last_chunk_index', 0) + 1
            logger.info(f"Resuming transcription from chunk {start_chunk_index} using progress file '{resume_path}'")
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Could not load progress file '{resume_path}': {e}. Starting new transcription.")
    elif resume_path:
        logger.warning(f"Progress file '{resume_path}' not found. Starting new transcription.")
    return transcribed_chunks, start_chunk_index

def _load_or_initialize_chunks(resume_path):
    """Loads existing transcribed chunks from a resume file or initializes them."""
    return handle_resume(resume_path)

def _convert_and_prepare_audio(input_audio_path):
    """Converts audio to WAV and returns the path and cleanup function."""
    result = convert_to_wav(input_audio_path)
    if isinstance(result, tuple):
        wav_path, cleanup_func = result
        temp_wav_file = wav_path
    else:
        wav_path = result
        cleanup_func = lambda: None
        temp_wav_file = None
    return wav_path, temp_wav_file, cleanup_func

def _transcribe_and_append_chunks(wav_path, chunk_duration, language, start_chunk_index, resume_path, engine, transcribed_chunks, temp_dir):
    """Transcribes audio chunks and appends them to the main list."""
    logger.info("Transcribing audio... This may take some time.")
    new_chunks = transcribe_audio_in_chunks(
        wav_path,
        chunk_duration=chunk_duration,
        language=language,
        start_chunk_index=start_chunk_index,
        resume_path=resume_path,
        engine=engine,
        temp_dir=temp_dir,
        existing_chunks=transcribed_chunks
    )
    if new_chunks is not None:
        transcribed_chunks[:] = new_chunks  # Update in place to maintain reference

def _save_transcription_output(transcribed_chunks, output_text_path, output_format):
    """Formats and saves the transcribed text to the output file."""
    formatted_transcription = format_transcription(transcribed_chunks, output_format)
    with open(output_text_path, "w", encoding="utf-8") as outfile:
        outfile.write(formatted_transcription)
    logger.info(f"Transcription completed. Output saved to '{output_text_path}'.")

def process_audio(input_audio_path, output_text_path, chunk_duration, language, output_format, resume_path, engine, temp_dir):
    """Converts, transcribes, and formats the audio."""
    temp_wav_file = None
    try:
        transcribed_chunks, start_chunk_index = _load_or_initialize_chunks(resume_path)
        wav_path, temp_wav_file, cleanup_func = _convert_and_prepare_audio(input_audio_path)
        _transcribe_and_append_chunks(wav_path, chunk_duration, language, start_chunk_index, resume_path, engine, transcribed_chunks, temp_dir)
        _save_transcription_output(transcribed_chunks, output_text_path, output_format)
    finally:
        if temp_wav_file and isinstance(temp_wav_file, str) and os.path.exists(temp_wav_file):
            try:
                os.remove(temp_wav_file)
            except OSError as e:
                logger.warning(f"Could not remove temporary file '{temp_wav_file}': {e}")

def main(args=None):
    """
    Main function of the application.
    Args:
        args: Optional parsed command line arguments. If None, arguments will be parsed from sys.argv.
    """
    if args is None:
        args = parse_arguments()

    input_audio_path = args.input_audio

    if not os.path.exists(input_audio_path):
        logger.error(f"Input file '{input_audio_path}' does not exist.")
        raise FileNotFoundError(f"Input file '{input_audio_path}' does not exist.")

    file_size = os.path.getsize(input_audio_path)
    if file_size > FILE_SIZE_WARNING_THRESHOLD:
        logger.warning(f"File is larger than {FILE_SIZE_WARNING_THRESHOLD // (1024 * 1024 * 1024)}GB. "
              "Processing may be slow or problematic. Consider splitting the file.")

    try:
        process_audio(
            args.input_audio,
            args.output_text,
            args.chunk,
            args.language,
            args.output_format,
            args.resume,
            args.engine,
            args.temp_dir
        )
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"{str(e)}")
        raise
    except Exception as e:
        logger.critical(f"An unexpected error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()