def format_transcription(transcribed_chunks, output_format):
    if output_format == "txt":
        return " ".join([chunk["text"] for chunk in transcribed_chunks])
    elif output_format == "srt":
        return to_srt(transcribed_chunks)
    elif output_format == "vtt":
        return to_vtt(transcribed_chunks)
    else:
        raise ValueError(f"Unsupported output format: {output_format}")

def _format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{milliseconds:03}"

def to_srt(transcribed_chunks):
    srt_content = []
    for i, chunk in enumerate(transcribed_chunks):
        if not all(k in chunk for k in ("start_time", "end_time", "text")):
            raise KeyError("Each chunk must contain 'start_time', 'end_time', and 'text' keys.")
        start_time = _format_time(chunk["start_time"])
        end_time = _format_time(chunk["end_time"])
        srt_content.append(f"{i + 1}")
        srt_content.append(f"{start_time} --> {end_time}")
        srt_content.append(chunk["text"])
        srt_content.append("")  # Empty line for separation
    return "\n".join(srt_content)

def to_vtt(transcribed_chunks):
    vtt_content = ["WEBVTT", ""]
    for chunk in transcribed_chunks:
        if not all(k in chunk for k in ("start_time", "end_time", "text")):
            raise KeyError("Each chunk must contain 'start_time', 'end_time', and 'text' keys.")
        start_time = _format_time(chunk["start_time"]).replace(',', '.')
        end_time = _format_time(chunk["end_time"]).replace(',', '.')
        vtt_content.append(f"{start_time} --> {end_time}")
        vtt_content.append(chunk["text"])
        vtt_content.append("")  # Empty line for separation
    return "\n".join(vtt_content)
