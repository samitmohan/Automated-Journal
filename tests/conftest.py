import pytest

SAMPLE_MORNING_ENTRY = """\
Two Minute Journal | Friday, Jun 28 2023

> "The only way to do great work is to love what you do."
>
> ~ Steve Jobs


---
08:30 AM

### I am grateful for...
1. My family
2. Good health
3. A new day

### What would make today great?
1. Finishing the project
2. Going for a run
3. Reading a chapter

### Daily affirmations
1. I am capable and strong
2. I will be productive today
3. I am grateful for every moment
"""

SAMPLE_FULL_ENTRY = """\
Two Minute Journal | Friday, Jun 28 2023

> "The only way to do great work is to love what you do."
>
> ~ Steve Jobs


---
08:30 AM

### I am grateful for...
1. My family
2. Good health
3. A new day

### What would make today great?
1. Finishing the project
2. Going for a run
3. Reading a chapter

### Daily affirmations
1. I am capable and strong
2. I will be productive today
3. I am grateful for every moment

---
09:30 PM

### Highlights of the day
1. Completed the feature
2. Had a great workout
3. Spent time with family

### What did I learn today?
1. Patience is important
2. Small steps add up
3. Rest is productive too
"""

SAMPLE_ANALYSIS_JSON = {
    "version": "1.0.0",
    "analyzed_at": "2023-06-28T22:00:00",
    "entry_date": "2023-06-28",
    "sections": {
        "morning": {
            "sentiment": {"label": "POSITIVE", "score": 0.95},
            "emotions": {
                "anger": 0.01,
                "disgust": 0.01,
                "fear": 0.02,
                "joy": 0.72,
                "neutral": 0.15,
                "sadness": 0.05,
                "surprise": 0.04,
            },
            "keywords": ["family", "health", "project"],
        },
        "evening": {
            "sentiment": {"label": "POSITIVE", "score": 0.88},
            "emotions": {
                "anger": 0.01,
                "disgust": 0.01,
                "fear": 0.01,
                "joy": 0.65,
                "neutral": 0.20,
                "sadness": 0.08,
                "surprise": 0.04,
            },
            "keywords": ["feature", "workout", "family"],
        },
    },
    "overall": {
        "sentiment": {"label": "POSITIVE", "score": 0.915},
        "emotions": {
            "anger": 0.01,
            "disgust": 0.01,
            "fear": 0.015,
            "joy": 0.685,
            "neutral": 0.175,
            "sadness": 0.065,
            "surprise": 0.04,
        },
        "keywords": ["family", "health", "project", "feature", "workout"],
    },
}


@pytest.fixture
def sample_morning_entry():
    return SAMPLE_MORNING_ENTRY


@pytest.fixture
def sample_full_entry():
    return SAMPLE_FULL_ENTRY


@pytest.fixture
def sample_analysis_json():
    return SAMPLE_ANALYSIS_JSON


@pytest.fixture
def mock_sentiment():
    """Mock sentiment pipeline that returns POSITIVE."""
    def pipeline_fn(text):
        return [{"label": "POSITIVE", "score": 0.92}]
    return pipeline_fn


@pytest.fixture
def mock_emotion():
    """Mock emotion pipeline that returns all 7 emotions."""
    def pipeline_fn(text):
        return [[
            {"label": "joy", "score": 0.65},
            {"label": "neutral", "score": 0.15},
            {"label": "sadness", "score": 0.08},
            {"label": "surprise", "score": 0.05},
            {"label": "fear", "score": 0.03},
            {"label": "anger", "score": 0.02},
            {"label": "disgust", "score": 0.02},
        ]]
    return pipeline_fn
