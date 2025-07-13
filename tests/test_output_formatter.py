import pytest
from output_formatter import format_transcription, to_srt, to_vtt, _format_time

@pytest.fixture
def sample_transcribed_chunks():
    return [
        {"text": "Hello world.", "start_time": 0.0, "end_time": 1.5},
        {"text": "This is a test.", "start_time": 1.5, "end_time": 3.0}
    ]

def test_format_transcription_txt(sample_transcribed_chunks):
    result = format_transcription(sample_transcribed_chunks, "txt")
    assert result == "Hello world. This is a test."

def test_format_transcription_srt(sample_transcribed_chunks):
    result = format_transcription(sample_transcribed_chunks, "srt")
    expected = (
        "1\n00:00:00,000 --> 00:00:01,500\nHello world.\n\n"
        "2\n00:00:01,500 --> 00:00:03,000\nThis is a test.\n"
    )
    assert result.strip() == expected.strip()

def test_format_transcription_vtt(sample_transcribed_chunks):
    result = format_transcription(sample_transcribed_chunks, "vtt")
    expected = (
        "WEBVTT\n\n"
        "00:00:00.000 --> 00:00:01.500\nHello world.\n\n"
        "00:00:01.500 --> 00:00:03.000\nThis is a test.\n"
    )
    assert result.strip() == expected.strip()

def test_format_transcription_unsupported_format(sample_transcribed_chunks):
    with pytest.raises(ValueError, match="Unsupported output format: xyz"):
        format_transcription(sample_transcribed_chunks, "xyz")

def test_format_time():
    assert _format_time(0) == "00:00:00,000"
    assert _format_time(1.5) == "00:00:01,500"
    assert _format_time(3661.123) == "01:01:01,123"

def test_to_srt_empty_chunks():
    assert to_srt([]) == ""

def test_to_vtt_empty_chunks():
    assert to_vtt([]) == "WEBVTT\n"

def test_to_srt_missing_keys():
    with pytest.raises(KeyError):
        to_srt([{"text": "test"}])

def test_to_vtt_missing_keys():
    with pytest.raises(KeyError):
        to_vtt([{"text": "test"}])
