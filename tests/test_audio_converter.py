import pytest
import os
from pydub import AudioSegment
from audio_converter import convert_to_wav, SUPPORTED_FORMATS
from unittest.mock import MagicMock

@pytest.fixture
def create_dummy_audio_file(tmp_path):
    def _create_dummy_audio_file(filename, format, content="dummy content"):
        file_path = tmp_path / filename
        if format == "wav":
            # Create a minimal valid WAV file header + dummy data
            # This is a very basic header for a 1-second, 16-bit, mono, 44.1kHz WAV
            # For an empty content, we still need a valid header size.
            # The 44 is the size of the WAV header.
            wav_content = content.encode() if content else b'\0' * 44100 # Add some dummy data if content is empty
            header = b'RIFF' + (36 + len(wav_content)).to_bytes(4, 'little') + \
                     b'WAVEfmt ' + (16).to_bytes(4, 'little') + \
                     (1).to_bytes(2, 'little') + (1).to_bytes(2, 'little') + \
                     (44100).to_bytes(4, 'little') + (44100 * 2).to_bytes(4, 'little') + \
                     (2).to_bytes(2, 'little') + (16).to_bytes(2, 'little') + \
                     b'data' + (len(wav_content)).to_bytes(4, 'little')
            file_path.write_bytes(header + wav_content)
        else:
            file_path.write_text(content)
        return str(file_path)
    return _create_dummy_audio_file

def test_convert_to_wav_already_wav(create_dummy_audio_file):
    wav_path = create_dummy_audio_file("test.wav", "wav")
    converted_path = convert_to_wav(wav_path)
    if isinstance(converted_path, tuple):
        converted_path = converted_path[0]
    assert converted_path == wav_path
    assert os.path.exists(converted_path)

def test_convert_to_wav_mp3_to_wav(create_dummy_audio_file, mocker, tmp_path):
    mp3_path = create_dummy_audio_file("test.mp3", "mp3")
    mock_audio_segment = mocker.patch('pydub.AudioSegment.from_file')
    mock_audio_segment.return_value.export = MagicMock(return_value=None)

    converted_path, cleanup_func = convert_to_wav(mp3_path)
    assert isinstance(converted_path, str)
    assert converted_path.endswith(".wav")
    assert os.path.exists(converted_path)
    assert callable(cleanup_func)
    mock_audio_segment.assert_called_once_with(mp3_path, format="mp3")
    mock_audio_segment.return_value.export.assert_called_once_with(converted_path, format="wav")

def test_convert_to_wav_unsupported_format(create_dummy_audio_file):
    unsupported_path = create_dummy_audio_file("test.xyz", "xyz")
    with pytest.raises(ValueError, match=f"Unsupported audio format: 'xyz'. Supported formats: {', '.join(SUPPORTED_FORMATS)}"):
        convert_to_wav(unsupported_path)

def test_convert_to_wav_file_not_found(mocker):
    mocker.patch('pydub.AudioSegment.from_file', side_effect=FileNotFoundError)
    with pytest.raises(FileNotFoundError, match="Input audio file not found"):
        convert_to_wav("non_existent.mp3")

def test_convert_to_wav_pydub_error(mocker):
    mocker.patch('pydub.AudioSegment.from_file', side_effect=Exception("Pydub internal error"))
    with pytest.raises(ValueError, match="Failed to convert audio file"):
        convert_to_wav("test.mp3")

def test_convert_to_wav_empty_file(create_dummy_audio_file, mocker):
    empty_mp3_path = create_dummy_audio_file("empty.mp3", "mp3", content="")
    mocker.patch('pydub.AudioSegment.from_file', side_effect=Exception("Invalid audio file"))

    with pytest.raises(ValueError, match="Failed to convert audio file"):
        convert_to_wav(empty_mp3_path)