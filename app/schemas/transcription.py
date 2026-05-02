from enum import StrEnum

from pydantic import BaseModel


class WordType(StrEnum):
    WORD = "word"
    SPACING = "spacing"
    AUDIO_EVENT = "audio_event"


class TranscriptionWord(BaseModel):
    text: str
    start: float | None = None
    end: float | None = None
    type: WordType
    speaker_id: str | None = None
    logprob: float


class TranscriptionResult(BaseModel):
    language_code: str
    language_probability: float
    text: str
    words: list[TranscriptionWord]
    audio_duration_secs: float | None = None
    transcription_id: str | None = None
