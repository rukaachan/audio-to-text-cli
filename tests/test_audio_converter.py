import pytest
import os
from pydub import AudioSegment
from audio_converter import convert_to_wav, SUPPORTED_FORMATS

@pytest.fixture
def create_dummy_audio_file(tmp_path):
    def _create_dummy_audio_file(filename, format, content="dummy content"):
        file_path = tmp_path / filename
        if format == "wav":
            header = b'RIFF' + (36 + len(content)).to_bytes(4, 'little') + \
                     b'WAVEfmt ' + (16).to_bytes(4, 'little') + \
                     (1).to_bytes(2, 'little') + (1).to_bytes(2, 'little') + \
                     (44100).to_bytes(4, 'little') + (44100 * 2).to_bytes(4, 'little') + \
                     (2).to_bytes(2, 'little') + (16).to_bytes(2, 'little') + \
                     b'data' + (len(content)).to_bytes(4, 'little')
            file_path.write_bytes(header + content.encode())
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

def test_convert_to_wav_mp3_to_wav(create_dummy_audio_file, mocker):
    mp3_path = create_dummy_audio_file("test.mp3", "mp3")
    mock_audio_segment = mocker.patch('pydub.AudioSegment.from_file')
    mock_audio_segment.return_value.export.return_value = None

    converted_path = convert_to_wav(mp3_path)
    if isinstance(converted_path, tuple):
        converted_path = converted_path[0]
    assert converted_path.endswith("_converted.wav")
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
