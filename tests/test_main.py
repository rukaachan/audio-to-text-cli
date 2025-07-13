import pytest
import os
import sys
import json
from unittest.mock import patch, mock_open, MagicMock
import main
import logging
from cli import parse_arguments

@pytest.fixture
def mock_args():
    class MockArgs:
        input_audio = "dummy_input.mp3"
        output_text = "dummy_output.txt"
        chunk = 60
        language = "en-US"
        output_format = "txt"
        resume = None
        engine = "google"
        temp_dir = None
    return MockArgs()

@pytest.fixture
def setup_mock_files(tmp_path):
    # Create a dummy input audio file
    input_audio_path = tmp_path / "test_audio.mp3"
    input_audio_path.write_text("dummy audio content")
    # Create a dummy WAV file for conversion output
    wav_path = tmp_path / "test_audio.mp3_converted.wav"
    wav_path.write_text("dummy wav content")
    return str(input_audio_path), str(wav_path)

def test_main_file_not_found(mock_args, caplog):
    caplog.set_level(logging.ERROR)
    mock_args.input_audio = "non_existent.mp3"
    with pytest.raises(FileNotFoundError):
        main.main(mock_args)
    assert "Input file 'non_existent.mp3' does not exist." in caplog.text

@patch('main._convert_and_prepare_audio')
@patch('main._load_or_initialize_chunks')
@patch('main.transcribe_audio_in_chunks')
@patch('main.convert_to_wav')
@patch('os.path.exists', return_value=True)
@patch('os.path.getsize', return_value=100 * 1024 * 1024)  # 100MB
def test_main_successful_transcription(mock_getsize, mock_exists, mock_convert_to_wav, mock_transcribe_audio_in_chunks, 
                                     mock_load_or_initialize_chunks, 
                                     mock_convert_and_prepare_audio, mock_args, caplog, tmp_path):
    caplog.set_level(logging.INFO)
    mock_load_or_initialize_chunks.return_value = ([], 0)
    converted_wav = str(tmp_path / "converted.wav")
    mock_convert_and_prepare_audio.return_value = (converted_wav, None, lambda: None)
    mock_transcribe_audio_in_chunks.return_value = [{"text": "hello world", "start_time": 0, "end_time": 1}]
    
    with open(mock_args.input_audio, "w") as f:
        f.write("dummy content")
    
    # Create the converted.wav file so cleanup doesn't fail
    with open(converted_wav, "w") as f:
        f.write("dummy wav content")

    main.main(mock_args)

    mock_transcribe_audio_in_chunks.assert_called_once()
    assert mock_transcribe_audio_in_chunks.call_args[1]["chunk_duration"] == mock_args.chunk
    assert mock_transcribe_audio_in_chunks.call_args[1]["language"] == mock_args.language
    assert f"Transcription completed. Output saved to '{mock_args.output_text}'." in caplog.text

@patch('main.convert_to_wav', side_effect=ValueError("Unsupported format"))
@patch('os.path.exists', return_value=True)
@patch('os.path.getsize', return_value=100 * 1024 * 1024)
def test_main_conversion_error(mock_getsize, mock_exists, mock_convert_to_wav, mock_args, caplog):
    caplog.set_level(logging.ERROR)
    # Create input file
    with open(mock_args.input_audio, "w") as f:
        f.write("dummy content")
    with pytest.raises(ValueError) as pytest_wrapped_e:
        main.main(mock_args)
    assert "Unsupported format" in str(pytest_wrapped_e.value)
    assert "Unsupported format" in caplog.text

@patch('main.transcribe_audio_in_chunks', side_effect=Exception("API Error"))
@patch('main.convert_to_wav')
@patch('os.path.exists', return_value=True)
@patch('os.path.getsize', return_value=100 * 1024 * 1024)
def test_main_transcription_error(mock_getsize, mock_exists, mock_convert_to_wav,
                                mock_transcribe_audio_in_chunks, mock_args, caplog, tmp_path):
    caplog.set_level(logging.CRITICAL)
    converted_wav = str(tmp_path / "converted.wav")
    mock_convert_to_wav.return_value = converted_wav
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        main.main(mock_args)
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1
    assert "An unexpected error occurred: API Error" in caplog.text

@patch('main._convert_and_prepare_audio')
@patch('main._load_or_initialize_chunks')
@patch('main._save_transcription_output')
@patch('main.transcribe_audio_in_chunks')
@patch('os.path.exists', return_value=True)
@patch('os.path.getsize', return_value=2 * 1024 * 1024 * 1024)  # 2GB
def test_main_large_file_warning(mock_getsize, mock_exists, mock_transcribe_audio_in_chunks,
                               mock_save_transcription_output, mock_load_or_initialize_chunks,
                               mock_convert_and_prepare_audio, mock_args, caplog, tmp_path):
    caplog.set_level(logging.WARNING)
    mock_load_or_initialize_chunks.return_value = ([], 0)
    mock_convert_and_prepare_audio.return_value = (str(tmp_path / "converted.wav"), str(tmp_path / "converted.wav"), lambda: None)
    mock_transcribe_audio_in_chunks.return_value = [{"text": "hello world", "start_time": 0, "end_time": 1}]
    mock_save_transcription_output.return_value = None

    main.main(mock_args)

    assert "File is larger than 1GB. Processing may be slow or problematic." in caplog.text

@patch('cli.parse_arguments')
@patch('os.path.exists', return_value=True)
@patch('os.path.getsize', return_value=100 * 1024 * 1024)
@patch('json.load', side_effect=json.JSONDecodeError("Invalid JSON", "", 0))
def test_main_resume_json_error(mock_json_load, mock_getsize, mock_exists, mock_parse_arguments,
                              mock_args, caplog, tmp_path):
    caplog.set_level(logging.WARNING)
    mock_args.resume = str(tmp_path / "corrupt.json")
    mock_parse_arguments.return_value = mock_args

    with patch('main._convert_and_prepare_audio') as mock_convert:
        mock_convert.return_value = (str(tmp_path / "converted.wav"), str(tmp_path / "converted.wav"), lambda: None)
        with patch('main.transcribe_audio_in_chunks') as mock_transcribe:
            mock_transcribe.return_value = [{"text": "new chunk", "start_time": 0, "end_time": 1}]
            with patch('main._save_transcription_output'):
                main.main(mock_args)

    assert "Could not load progress file" in caplog.text
    assert "Starting new transcription." in caplog.text

@patch('cli.parse_arguments')
@patch('os.path.exists')
@patch('os.path.getsize', return_value=100 * 1024 * 1024)
def test_main_resume_file_not_found(mock_getsize, mock_exists, mock_parse_arguments,
                                  mock_args, caplog, tmp_path):
    caplog.set_level(logging.WARNING)
    mock_args.resume = "non_existent_progress.json"
    mock_parse_arguments.return_value = mock_args
    # Make input file exist but resume file not exist
    mock_exists.side_effect = lambda x: x != "non_existent_progress.json"

    with patch('main._convert_and_prepare_audio') as mock_convert:
        mock_convert.return_value = (str(tmp_path / "converted.wav"), str(tmp_path / "converted.wav"), lambda: None)
        with patch('main.transcribe_audio_in_chunks') as mock_transcribe:
            mock_transcribe.return_value = [{"text": "new chunk", "start_time": 0, "end_time": 1}]
            with patch('main._save_transcription_output'):
                main.main(mock_args)

    assert "Progress file 'non_existent_progress.json' not found" in caplog.text
    assert "Starting new transcription." in caplog.text

@patch('cli.parse_arguments')
@patch('os.path.exists')
@patch('os.path.getsize', return_value=100 * 1024 * 1024)
@patch('json.load')
def test_main_resume_successful(mock_json_load, mock_getsize, mock_exists, mock_parse_arguments,
                              mock_args, caplog, tmp_path):
    caplog.set_level(logging.INFO)
    progress_file = str(tmp_path / "progress.json")
    mock_args.resume = progress_file
    mock_parse_arguments.return_value = mock_args

    def exists_side_effect(path):
        return path == mock_args.input_audio or path == progress_file
    mock_exists.side_effect = exists_side_effect

    mock_json_load.return_value = {
        'transcribed_chunks': [{"text": "resumed", "start_time": 0, "end_time": 1}],
        'last_chunk_index': 1
    }

    # Create input file
    with open(mock_args.input_audio, "w") as f:
        f.write("dummy content")

    # Create progress file
    os.makedirs(os.path.dirname(progress_file), exist_ok=True)
    with open(progress_file, "w") as f:
        f.write('{"transcribed_chunks": [], "last_chunk_index": 1}')

    with patch('main._convert_and_prepare_audio') as mock_convert:
        converted_wav = str(tmp_path / "converted.wav")
        mock_convert.return_value = (converted_wav, None, lambda: None)
        with patch('main.transcribe_audio_in_chunks') as mock_transcribe:
            mock_transcribe.return_value = [
                {"text": "resumed", "start_time": 0, "end_time": 1},
                {"text": "new chunk", "start_time": 1, "end_time": 2}
            ]
            with patch('main._save_transcription_output'):
                # Create converted.wav to prevent cleanup error
                with open(converted_wav, "w") as f:
                    f.write("dummy wav content")
                main.main(mock_args)

    assert f"Resuming transcription from chunk 2 using progress file '{progress_file}'" in caplog.text
    assert mock_transcribe.call_args[1]["start_chunk_index"] == 2