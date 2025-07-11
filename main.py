import os
import sys
import tempfile
import json
from audio_converter import convert_to_wav
from transcriber import transcribe_audio_in_chunks, get_audio_duration
from cli import parse_arguments
from output_formatter import format_transcription

FILE_SIZE_WARNING_THRESHOLD = 1 * 1024 * 1024 * 1024  # 1GB

def main():
    """
    Main function of the application.
    """
    args = parse_arguments()

    input_audio_path = args.input_audio
    output_text_path = args.output_text
    chunk_duration = args.chunk
    language = args.language
    output_format = args.output_format
    resume_path = args.resume
    

    if not os.path.exists(input_audio_path):
        print(f"Error: Input file '{input_audio_path}' does not exist.")
    # Warn if file is larger than 1GB
    file_size = os.path.getsize(input_audio_path)
    size_threshold = 1 * 1024 * 1024 * 1024  # 1GB
    if file_size > size_threshold:
        print(f"Warning: File is larger than {size_threshold // (1024 * 1024 * 1024)}GB. Processing may be slow or problematic. "
              "Consider splitting the file.")
        print("Warning: File is larger than 1GB. Processing may be slow or problematic. "
              "Consider splitting the file.")

    temp_wav_file = None
    transcribed_chunks = []
    start_chunk_index = 0

    if resume_path:
        if os.path.exists(resume_path):
            try:
                with open(resume_path, 'r') as f:
                    progress_data = json.load(f)
                    transcribed_chunks = progress_data.get('transcribed_chunks', [])
                    start_chunk_index = progress_data.get('last_chunk_index', 0) + 1
                print(f"Resuming transcription from chunk {start_chunk_index} using progress file '{resume_path}'.")
            except json.JSONDecodeError:
                print(f"Warning: Could not decode JSON from progress file '{resume_path}'. Starting new transcription.")
            except Exception as e:
                print(f"Warning: Error loading progress file '{resume_path}': {e}. Starting new transcription.")
        else:
            print(f"Warning: Progress file '{resume_path}' not found. Starting new transcription.")

    try:
        # Convert input file to WAV if necessary
        wav_path = convert_to_wav(input_audio_path)
        
        # If convert_to_wav returns a tuple, extract the path
        if isinstance(wav_path, tuple):
            wav_path = wav_path[0]
        
        # If convert_to_wav created a temporary file, store its reference
        if wav_path != input_audio_path:
            temp_wav_file = wav_path

        print("Transcribing audio... This may take some time.")

        new_chunks = []
        if args.engine == "google":
            new_chunks = transcribe_audio_in_chunks(wav_path, chunk_duration=chunk_duration, language=language, 
                                                    start_chunk_index=start_chunk_index, resume_path=resume_path)
        
        
        transcribed_chunks.extend(new_chunks if new_chunks is not None else [])

        formatted_transcription = format_transcription(transcribed_chunks, args.output_format)

        # Write transcription and metadata to output file
        with open(output_text_path, "w", encoding="utf-8") as outfile:
            outfile.write(formatted_transcription)
        
        print(f"Transcription completed. Output saved to '{output_text_path}'.")
    except FileNotFoundError:
        print(f"Error: The audio file '{input_audio_path}' was not found.")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)
    finally:
        # Remove temporary WAV file if it was created
        if temp_wav_file and os.path.exists(temp_wav_file):
            try:
                os.remove(temp_wav_file)
            except OSError as e:
                print(f"Warning: Could not remove temporary file '{temp_wav_file}': {e}")

if __name__ == "__main__":
    main()
