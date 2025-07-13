import pytest
import os
from unittest.mock import patch, mock_open, MagicMock, ANY
from transcriber import transcribe_audio_in_chunks, get_audio_duration, load_faster_whisper_model
from pydub import AudioSegment
import speech_recognition as sr
import json

@pytest.fixture
def create_dummy_wav_file(tmp_path):
    def _create_dummy_wav_file(filename, duration_ms=1000, content="dummy content"):
        file_path = tmp_path / filename
        # Create a minimal valid WAV file header + dummy data
        # This is a very basic header for a 1-second, 16-bit, mono, 44.1kHz WAV
        header = b'RIFF' + (36 + len(content)).to_bytes(4, 'little') + \
                 b'WAVEfmt ' + (16).to_bytes(4, 'little') + \
                 (1).to_bytes(2, 'little') + (1).to_bytes(2, 'little') + \
                 (44100).to_bytes(4, 'little') + (44100 * 2).to_bytes(4, 'little') + \
                 (2).to_bytes(2, 'little') + (16).to_bytes(2, 'little') + \
                 b'data' + (len(content)).to_bytes(4, 'little')
        file_path.write_bytes(header + content.encode())
        return str(file_path)
    return _create_dummy_wav_file

@patch('speech_recognition.Recognizer.recognize_google', return_value="hello world")
@patch('pydub.AudioSegment.from_wav')
def test_transcribe_audio_in_chunks_success(mock_from_wav, mock_recognize_google, create_dummy_wav_file, tmp_path):
    wav_path = create_dummy_wav_file("test.wav", duration_ms=120000) # 2 minutes
    mock_from_wav.return_value = AudioSegment.silent(duration=120000) # Mock 2 minutes of audio

    chunks = transcribe_audio_in_chunks(wav_path, chunk_duration=60, language="en-US", engine="google", temp_dir=tmp_path)

    assert chunks is not None
    assert len(chunks) == 2
    assert chunks[0]["text"] == "hello world"
    assert chunks[0]["start_time"] == 0.0
    assert chunks[0]["end_time"] == 60.0
    assert chunks[1]["text"] == "hello world"
    assert chunks[1]["start_time"] == 60.0
    assert chunks[1]["end_time"] == 120.0
    mock_recognize_google.call_count == 2

@patch('speech_recognition.Recognizer.recognize_google', side_effect=sr.UnknownValueError)
@patch('pydub.AudioSegment.from_wav')
def test_transcribe_audio_in_chunks_unknown_value_error(mock_from_wav, mock_recognize_google, create_dummy_wav_file, tmp_path):
    wav_path = create_dummy_wav_file("test.wav", duration_ms=60000)
    mock_from_wav.return_value = AudioSegment.silent(duration=60000)

    chunks = transcribe_audio_in_chunks(wav_path, chunk_duration=60, language="en-US", engine="google", temp_dir=tmp_path)

    assert chunks is not None
    assert len(chunks) == 1
    assert chunks[0]["text"] == "[Unrecognized Audio]"

@patch('speech_recognition.Recognizer.recognize_google', side_effect=sr.RequestError("API Limit Exceeded"))
@patch('pydub.AudioSegment.from_wav')
def test_transcribe_audio_in_chunks_request_error(mock_from_wav, mock_recognize_google, create_dummy_wav_file, tmp_path):
    wav_path = create_dummy_wav_file("test.wav", duration_ms=60000)
    mock_from_wav.return_value = AudioSegment.silent(duration=60000)

    chunks = transcribe_audio_in_chunks(wav_path, chunk_duration=60, language="en-US", engine="google", temp_dir=tmp_path)

    assert chunks is not None
    assert len(chunks) == 1
    assert "[RequestError: API Limit Exceeded]" in chunks[0]["text"]

@patch('pydub.AudioSegment.from_wav', side_effect=FileNotFoundError)
def test_transcribe_audio_in_chunks_file_not_found(mock_from_wav, tmp_path):
    with pytest.raises(FileNotFoundError, match="WAV file not found"):
        transcribe_audio_in_chunks("non_existent.wav", engine="google", temp_dir=tmp_path)

@patch('pydub.AudioSegment.from_wav', side_effect=Exception("Pydub error"))
def test_transcribe_audio_in_chunks_pydub_error(mock_from_wav, tmp_path):
    with pytest.raises(ValueError, match="Error loading WAV file"):
        transcribe_audio_in_chunks("test.wav", engine="google", temp_dir=tmp_path)

@patch('pydub.AudioSegment.from_wav')
def test_get_audio_duration_success(mock_from_wav, create_dummy_wav_file):
    wav_path = create_dummy_wav_file("test.wav", duration_ms=12345)
    mock_from_wav.return_value = AudioSegment.silent(duration=12345)
    duration = get_audio_duration(wav_path)
    assert duration == 12.345

def test_get_audio_duration_file_not_found():
    duration = get_audio_duration("non_existent.wav")
    assert duration is None

def test_get_audio_duration_error(mocker):
    mocker.patch('pydub.AudioSegment.from_wav', side_effect=Exception("Error getting duration"))
    duration = get_audio_duration("test.wav")
    assert duration is None

@patch('speech_recognition.Recognizer.recognize_google', return_value="resumed text")
@patch('pydub.AudioSegment.from_wav')
def test_transcribe_audio_in_chunks_resume(mock_from_wav, mock_recognize_google, create_dummy_wav_file, tmp_path):
    wav_path = create_dummy_wav_file("test.wav", duration_ms=180000) # 3 minutes
    mock_from_wav.return_value = AudioSegment.silent(duration=180000)
    resume_file = tmp_path / "progress.json"

    # Simulate a previous run that completed 1 chunk
    initial_progress = {
        "transcribed_chunks": [{
            "text": "first chunk",
            "start_time": 0.0,
            "end_time": 60.0
        }],
        "last_chunk_index": 0
    }
    with open(resume_file, 'w') as f:
        json.dump(initial_progress, f)

    # Call transcribe_audio_in_chunks with resume parameters
    chunk_duration = 60
    chunks = transcribe_audio_in_chunks(wav_path, chunk_duration=chunk_duration, language="en-US", 
                                        start_chunk_index=1, resume_path=str(resume_file), engine="google", temp_dir=tmp_path, existing_chunks=initial_progress["transcribed_chunks"])

    # Expect only the remaining chunks to be transcribed
    assert chunks is not None
    assert len(chunks) == 3 # Should transcribe chunk 1 and 2
    assert chunks[0]["text"] == "first chunk"
    assert chunks[0]["start_time"] == 0.0
    assert chunks[0]["end_time"] == 60.0
    assert chunks[0]["text"] == "first chunk"
    assert chunks[1]["start_time"] == 60.0
    assert chunks[1]["end_time"] == 2 * chunk_duration
    assert mock_recognize_google.call_count == 2 # Only 2 new calls

    # Verify progress file was updated
    with open(resume_file, 'r') as f:
        updated_progress = json.load(f)
        assert updated_progress["last_chunk_index"] == 2 # Last chunk index should be 2 (0-indexed)
        assert len(updated_progress["transcribed_chunks"]) == 3 # Original + 2 new

@patch('transcriber.load_faster_whisper_model')
@patch('pydub.AudioSegment.from_wav')
def test_transcribe_audio_in_chunks_faster_whisper_success(mock_from_wav, mock_load_faster_whisper_model, create_dummy_wav_file, tmp_path):
    wav_path = create_dummy_wav_file("test.wav", duration_ms=60000)
    mock_from_wav.return_value = AudioSegment.silent(duration=60000)
    
    mock_model_instance = MagicMock()
    mock_load_faster_whisper_model.return_value = mock_model_instance
    mock_model_instance.transcribe.return_value = ([MagicMock(text="faster whisper transcription")], MagicMock())

    chunks = transcribe_audio_in_chunks(wav_path, chunk_duration=60, language="en-US", engine="faster-whisper", temp_dir=tmp_path)

    assert chunks is not None
    assert len(chunks) == 1
    assert chunks[0]["text"] == "faster whisper transcription"
    mock_load_faster_whisper_model.assert_called_once()
    mock_model_instance.transcribe.assert_called_once_with(ANY, beam_size=5, language="en-US")

@patch('pydub.AudioSegment.from_wav')
def test_transcribe_audio_in_chunks_empty_audio(mock_from_wav, create_dummy_wav_file, tmp_path):
    wav_path = create_dummy_wav_file("empty.wav", duration_ms=0)
    mock_from_wav.return_value = AudioSegment.empty()

    chunks = transcribe_audio_in_chunks(wav_path, chunk_duration=60, language="en-US", engine="google", temp_dir=tmp_path)
    assert chunks == []

@patch('pydub.AudioSegment.from_wav')
def test_transcribe_audio_in_chunks_short_audio(mock_from_wav, create_dummy_wav_file, mocker, tmp_path):
    wav_path = create_dummy_wav_file("short.wav", duration_ms=30000) # 30 seconds
    mock_from_wav.return_value = AudioSegment.silent(duration=30000)
    mocker.patch('speech_recognition.Recognizer.recognize_google', return_value="short audio")

    chunks = transcribe_audio_in_chunks(wav_path, chunk_duration=60, language="en-US", engine="google", temp_dir=tmp_path)
    assert len(chunks) == 1
    assert chunks[0]["text"] == "short audio"
    assert chunks[0]["start_time"] == 0.0
    assert chunks[0]["end_time"] == 30.0

def test_transcribe_audio_in_chunks_unsupported_engine(create_dummy_wav_file, tmp_path):
    wav_path = create_dummy_wav_file("test.wav")
    with pytest.raises(ValueError, match="Unsupported transcription engine: unsupported_engine"):
        transcribe_audio_in_chunks(wav_path, engine="unsupported_engine", temp_dir=tmp_path)
