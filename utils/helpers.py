import uuid

def generate_survey_id() -> str:
    """Generate clean 8-character unique survey identifier."""
    return uuid.uuid4().hex[:8]

def create_progress_bar(percentage: float, length: int = 10) -> str:
    """Create ASCII visual progress bar."""
    filled = int(round(length * (percentage / 100)))
    bar = "█" * filled + "░" * (length - filled)
    return f"[{bar}] {percentage:.1f}%"
