"""STT 연동 스텁. 브라우저 Web Speech API는 클라이언트에서 수행 후 텍스트만 전달."""


def transcribe_audio_stub(_audio_bytes: bytes | None = None) -> str:
    """향후 외부 STT API로 교체."""
    return ""
