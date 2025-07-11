import pytest
import os
import sys
import json
from unittest.mock import patch, mock_open
from main import main

@pytest.fixture
def mock_args():
    class MockArgs:
        input_audio = "test_audio.mp3"
        output_text = "output.txt"
        chunk = 60
        language = "en-US"
        output_format = "txt"
        resume = None
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

def test_main_file_not_found(mock_args, capsys):
    mock_args.input_audio = "non_existent.mp3"
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        main()
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1
    outerr = capsys.readouterr()
    assert "Error: Input file 'non_existent.mp3' does not exist." in outerr.out

@patch('main.convert_to_wav')
@patch('main.transcribe_audio_in_chunks')
@patch('main.get_audio_duration')
@patch('main.format_transcription')
@patch('builtins.open', new_callable=mock_open)
@patch('os.path.exists', return_value=True)
@patch('os.path.getsize', return_value=100 * 1024 * 1024) # 100MB
def test_main_successful_transcription(mock_getsize, mock_exists, mock_open_file, mock_format_transcription, mock_get_audio_duration, mock_transcribe_audio_in_chunks, mock_convert_to_wav, mock_args, capsys, tmp_path):
    mock_convert_to_wav.return_value = str(tmp_path / "converted.wav")
    mock_transcribe_audio_in_chunks.return_value = [{"text": "hello world", "start_time": 0, "end_time": 1}]
    mock_get_audio_duration.return_value = 1.0
    mock_format_transcription.return_value = "formatted transcription"

    main()

    mock_convert_to_wav.assert_called_once_with(mock_args.input_audio)
    mock_transcribe_audio_in_chunks.assert_called_once_with(
        str(tmp_path / "converted.wav"), 
        chunk_duration=mock_args.chunk, 
        language=mock_args.language,
        start_chunk_index=0,
        resume_path=None
    )
    mock_format_transcription.assert_called_once_with([{"text": "hello world", "start_time": 0, "end_time": 1}], mock_args.output_format)
    mock_open_file.assert_called_once_with(mock_args.output_text, "w", encoding="utf-8")
    mock_open_file().write.assert_called_once_with("formatted transcription")
    outerr = capsys.readouterr()
    assert f"Transcription completed. Output saved to '{mock_args.output_text}'." in outerr.out

@patch('main.convert_to_wav', side_effect=ValueError("Unsupported format"))
@patch('os.path.exists', return_value=True)
@patch('os.path.getsize', return_value=100 * 1024 * 1024)
def test_main_conversion_error(mock_getsize, mock_exists, mock_convert_to_wav, mock_args, capsys):
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        main()
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1
    outerr = capsys.readouterr()
    assert "Error: Unsupported format" in outerr.out

@patch('main.convert_to_wav')
@patch('main.transcribe_audio_in_chunks', side_effect=Exception("API Error"))
@patch('os.path.exists', return_value=True)
@patch('os.path.getsize', return_value=100 * 1024 * 1024)
def test_main_transcription_error(mock_getsize, mock_exists, mock_transcribe_audio_in_chunks, mock_convert_to_wav, mock_args, capsys, tmp_path):
    mock_convert_to_wav.return_value = str(tmp_path / "converted.wav")
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        main()
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1
    outerr = capsys.readouterr()
    assert "An unexpected error occurred: API Error" in outerr.out

@patch('main.convert_to_wav')
@patch('main.transcribe_audio_in_chunks')
@patch('main.get_audio_duration')
@patch('main.format_transcription')
@patch('builtins.open', new_callable=mock_open)
@patch('os.path.exists', side_effect=[True, True, False]) # input_audio exists, temp_wav_file exists initially, then not for os.remove
@patch('os.path.getsize', return_value=100 * 1024 * 1024)
@patch('os.remove', side_effect=OSError("Permission denied"))
def test_main_temp_file_removal_error(mock_remove, mock_getsize, mock_exists, mock_open_file, mock_format_transcription, mock_get_audio_duration, mock_transcribe_audio_in_chunks, mock_convert_to_wav, mock_args, capsys, tmp_path):
    mock_convert_to_wav.return_value = str(tmp_path / "converted.wav")
    mock_transcribe_audio_in_chunks.return_value = [{"text": "hello world", "start_time": 0, "end_time": 1}]
    mock_get_audio_duration.return_value = 1.0
    mock_format_transcription.return_value = "formatted transcription"

    main()

    outerr = capsys.readouterr()
    assert f"Warning: Could not remove temporary file '{str(tmp_path / "converted.wav")}': Permission denied" in outerr.out

@patch('main.convert_to_wav')
@patch('main.transcribe_audio_in_chunks')
@patch('main.get_audio_duration')
@patch('main.format_transcription')
@patch('builtins.open', new_callable=mock_open)
@patch('os.path.exists', return_value=True)
@patch('os.path.getsize', return_value=2 * 1024 * 1024 * 1024) # 2GB
def test_main_large_file_warning(mock_getsize, mock_exists, mock_open_file, mock_format_transcription, mock_get_audio_duration, mock_transcribe_audio_in_chunks, mock_convert_to_wav, mock_args, capsys, tmp_path):
    mock_convert_to_wav.return_value = str(tmp_path / "converted.wav")
    mock_transcribe_audio_in_chunks.return_value = [{"text": "hello world", "start_time": 0, "end_time": 1}]
    mock_get_audio_duration.return_value = 1.0
    mock_format_transcription.return_value = "formatted transcription"

    main()

    outerr = capsys.readouterr()
    assert "Warning: File is larger than 1GB. Processing may be slow or problematic." in outerr.out

@patch('main.convert_to_wav')
@patch('main.transcribe_audio_in_chunks')
@patch('main.get_audio_duration')
@patch('main.format_transcription')
@patch('builtins.open', new_callable=mock_open)
@patch('os.path.exists', side_effect=[True, True, True]) # input_audio exists, resume_path exists, temp_wav_file exists
@patch('os.path.getsize', return_value=100 * 1024 * 1024)
@patch('json.load', return_value={'transcribed_chunks': [{"text": "resumed", "start_time": 0, "end_time": 1}], 'last_chunk_index': 0})
def test_main_resume_successful(mock_json_load, mock_getsize, mock_exists, mock_open_file, mock_format_transcription, mock_get_audio_duration, mock_transcribe_audio_in_chunks, mock_convert_to_wav, mock_args, capsys, tmp_path):
    mock_args.resume = str(tmp_path / "progress.json")
    mock_convert_to_wav.return_value = str(tmp_path / "converted.wav")
    mock_transcribe_audio_in_chunks.return_value = [{"text": "new chunk", "start_time": 1, "end_time": 2}]
    mock_get_audio_duration.return_value = 2.0
    mock_format_transcription.return_value = "resumed formatted transcription"

    main()

    mock_transcribe_audio_in_chunks.assert_called_once_with(
        str(tmp_path / "converted.wav"), 
        chunk_duration=mock_args.chunk, 
        language=mock_args.language,
        start_chunk_index=1,
        resume_path=mock_args.resume
    )
    outerr = capsys.readouterr()
    assert "Resuming transcription from chunk 1 using progress file" in outerr.out
    assert "Transcription completed. Output saved to" in outerr.out

@patch('main.convert_to_wav')
@patch('main.transcribe_audio_in_chunks')
@patch('main.get_audio_duration')
@patch('main.format_transcription')
@patch('builtins.open', new_callable=mock_open)
@patch('os.path.exists', side_effect=[True, True, True])
@patch('os.path.getsize', return_value=100 * 1024 * 1024)
@patch('json.load', side_effect=json.JSONDecodeError("Expecting value", "doc", 0))
def test_main_resume_json_error(mock_json_load, mock_getsize, mock_exists, mock_open_file, mock_format_transcription, mock_get_audio_duration, mock_transcribe_audio_in_chunks, mock_convert_to_wav, mock_args, capsys, tmp_path):
    mock_args.resume = str(tmp_path / "corrupt.json")
    mock_convert_to_wav.return_value = str(tmp_path / "converted.wav")
    mock_transcribe_audio_in_chunks.return_value = [{"text": "new chunk", "start_time": 0, "end_time": 1}]
    mock_get_audio_duration.return_value = 1.0
    mock_format_transcription.return_value = "formatted transcription"

    main()

    outerr = capsys.readouterr()
    assert "Warning: Could not decode JSON from progress file" in outerr.out
    assert "Starting new transcription." in outerr.out

@patch('main.convert_to_wav')
@patch('main.transcribe_audio_in_chunks')
@patch('main.get_audio_duration')
@patch('main.format_transcription')
@patch('builtins.open', new_callable=mock_open)
@patch('os.path.exists', side_effect=[True, False]) # input_audio exists, resume_path does not
@patch('os.path.getsize', return_value=100 * 1024 * 1024)
def test_main_resume_file_not_found(mock_getsize, mock_exists, mock_open_file, mock_format_transcription, mock_get_audio_duration, mock_transcribe_audio_in_chunks, mock_convert_to_wav, mock_args, capsys, tmp_path):
    mock_args.resume = "non_existent_progress.json"
    mock_convert_to_wav.return_value = str(tmp_path / "converted.wav")
    mock_transcribe_audio_in_chunks.return_value = [{"text": "new chunk", "start_time": 0, "end_time": 1}]
    mock_get_audio_duration.return_value = 1.0
    mock_format_transcription.return_value = "formatted transcription"

    main()

    outerr = capsys.readouterr()
    assert "Warning: Progress file 'non_existent_progress.json' not found. Starting new transcription." in outerr.out
