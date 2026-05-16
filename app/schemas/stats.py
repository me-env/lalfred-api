from pydantic import BaseModel


class UsageStats(BaseModel):
    window_days: int
    mean_credits_per_day: float
    median_credits_per_day: float
    # Days remaining at the current average rate. None when there's no
    # measurable usage in the window (so no meaningful projection).
    days_remaining_estimate: float | None = None
    # Words per minute across stored STT transcriptions in the window.
    # None when no audio has been transcribed yet (no usable denominator).
    words_per_minute: float | None = None
    total_words: int
    total_audio_seconds: float
