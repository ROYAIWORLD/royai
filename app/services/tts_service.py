"""TTS 연동 스텁. MVP는 클라이언트에서 Web Speech Synthesis 사용 권장."""


def synthesize_stub(_text: str) -> bytes | None:
    return None
