"""
guardrails.py – Topic enforcement and off-topic detection for the interview chatbot.
"""

import re

# Keywords that indicate the message is interview-relevant
INTERVIEW_KEYWORDS = {
    "yes", "no", "yeah", "nope", "yep", "sure", "absolutely", "i can", "i do",
    "i am", "i'm", "i have", "i don't", "i cannot", "i can't",
    "drive", "driver", "driving", "license", "delivery", "deliver", "package",
    "truck", "vehicle", "route", "fedex", "courier", "shipping",
    "lift", "heavy", "pounds", "lbs", "weight", "physical",
    "weekend", "shift", "hours", "schedule", "available", "availability",
    "experience", "job", "work", "worked", "working", "years", "months",
    "background", "drug", "screening", "test", "check",
    "clean", "record", "violation", "accident",
    "management", "time", "organize", "independent", "independently",
    "customer", "service", "professional",
    "apply", "position", "role", "hire", "hiring",
    "pay", "salary", "benefits", "training", "bonus",
    "age", "old", "21",
    "tampa", "florida", "tsavo",
}

# Patterns that strongly indicate off-topic / prompt injection attempts
OFF_TOPIC_PATTERNS = [
    r"(?i)ignore\s+(previous|all|above)\s+(instructions?|prompts?)",
    r"(?i)you\s+are\s+now\s+a",
    r"(?i)pretend\s+(to\s+be|you\s+are)",
    r"(?i)forget\s+(everything|your\s+instructions)",
    r"(?i)what\s+is\s+(the\s+)?(capital|president|weather|meaning\s+of\s+life)",
    r"(?i)tell\s+me\s+(a\s+joke|about\s+(yourself|AI|politics|sports))",
    r"(?i)write\s+(me\s+)?(a\s+)?(poem|story|essay|code|script|song)",
    r"(?i)help\s+me\s+with\s+(my\s+)?(homework|math|science|coding)",
    r"(?i)what\s+do\s+you\s+think\s+about\s+(politics|religion|war)",
    r"(?i)who\s+(won|is\s+winning)\s+(the|in)\s+",
    r"(?i)can\s+you\s+(search|browse|google|look\s+up)",
    r"(?i)translate\s+.+\s+to\s+",
    r"(?i)system\s*prompt",
    r"(?i)reveal\s+(your|the)\s+(instructions|prompt|system)",
]

# Short answers are almost always valid responses to interview questions
MIN_LENGTH_FOR_CHECK = 15


def is_on_topic(message: str) -> bool:
    """
    Check whether a candidate's message is on-topic for the interview.
    Returns True if the message is on-topic, False if off-topic.
    """
    message = message.strip()

    # Very short messages are almost always direct answers (Yes/No etc.)
    if len(message) < MIN_LENGTH_FOR_CHECK:
        return True

    # Check for prompt injection / manipulation patterns
    for pattern in OFF_TOPIC_PATTERNS:
        if re.search(pattern, message):
            return False

    # Tokenize and check for interview-relevant keywords
    words = set(re.findall(r"[a-z\']+", message.lower()))

    # If the message contains at least one interview keyword, accept it
    if words & INTERVIEW_KEYWORDS:
        return True

    # For longer messages with no interview keywords, flag as potentially off-topic
    if len(message) > 80 and not (words & INTERVIEW_KEYWORDS):
        return False

    # Default: allow (benefit of the doubt for medium-length messages)
    return True


def is_prompt_injection(message: str) -> bool:
    """Check specifically for prompt injection attempts."""
    for pattern in OFF_TOPIC_PATTERNS[:6]:  # First 6 patterns are injection-related
        if re.search(pattern, message):
            return True
    return False
