import logging
from datetime import datetime

from journal_app.analysis.parser import JournalParser, ParsedSection
from journal_app.analysis.schemas import (
    EmotionScores,
    JournalAnalysis,
    SectionAnalysis,
    SentimentResult,
)

logger = logging.getLogger(__name__)

ANALYSIS_VERSION = "1.0.0"

SENTIMENT_MODEL = "distilbert-base-uncased-finetuned-sst-2-english"
EMOTION_MODEL = "j-hartmann/emotion-english-distilroberta-base"

EMOTION_LABELS = ["anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise"]


class JournalAnalyzer:
    """NLP analysis pipeline using HuggingFace transformers and YAKE."""

    def __init__(self):
        self._sentiment_pipeline = None
        self._emotion_pipeline = None
        self._keyword_extractor = None

    def _load_sentiment(self):
        if self._sentiment_pipeline is None:
            from transformers import pipeline
            logger.info("Loading sentiment model: %s", SENTIMENT_MODEL)
            self._sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model=SENTIMENT_MODEL,
                truncation=True,
                max_length=512,
            )
        return self._sentiment_pipeline

    def _load_emotion(self):
        if self._emotion_pipeline is None:
            from transformers import pipeline
            logger.info("Loading emotion model: %s", EMOTION_MODEL)
            self._emotion_pipeline = pipeline(
                "text-classification",
                model=EMOTION_MODEL,
                top_k=None,
                truncation=True,
                max_length=512,
            )
        return self._emotion_pipeline

    def _load_keywords(self):
        if self._keyword_extractor is None:
            import yake
            self._keyword_extractor = yake.KeywordExtractor(
                lan="en",
                n=2,
                top=10,
                dedupLim=0.7,
            )
        return self._keyword_extractor

    def analyze_text(self, text: str) -> SectionAnalysis:
        """Run sentiment, emotion, and keyword analysis on a text block."""
        if not text.strip():
            return SectionAnalysis(
                sentiment=SentimentResult(label="NEUTRAL", score=0.5),
                emotions=EmotionScores(neutral=1.0),
                keywords=[],
            )

        sentiment = self._analyze_sentiment(text)
        emotions = self._analyze_emotions(text)
        keywords = self._extract_keywords(text)

        return SectionAnalysis(
            sentiment=sentiment,
            emotions=emotions,
            keywords=keywords,
        )

    def _analyze_sentiment(self, text: str) -> SentimentResult:
        pipe = self._load_sentiment()
        result = pipe(text)[0]
        return SentimentResult(label=result["label"], score=result["score"])

    def _analyze_emotions(self, text: str) -> EmotionScores:
        pipe = self._load_emotion()
        results = pipe(text)[0]
        scores = {r["label"]: r["score"] for r in results}
        return EmotionScores(**{label: scores.get(label, 0.0) for label in EMOTION_LABELS})

    def _extract_keywords(self, text: str) -> list[str]:
        extractor = self._load_keywords()
        keywords = extractor.extract_keywords(text)
        return [kw for kw, _score in sorted(keywords, key=lambda x: x[1])[:10]]

    def analyze_sections(self, sections: list[ParsedSection]) -> dict[str, SectionAnalysis]:
        """Analyze each parsed section."""
        results = {}
        for section in sections:
            text = section.text
            if text:
                results[section.name] = self.analyze_text(text)
        return results

    def compute_overall(self, section_analyses: dict[str, SectionAnalysis]) -> SectionAnalysis:
        """Compute an aggregate analysis across all sections."""
        if not section_analyses:
            return SectionAnalysis(
                sentiment=SentimentResult(label="NEUTRAL", score=0.5),
                emotions=EmotionScores(neutral=1.0),
                keywords=[],
            )

        if len(section_analyses) == 1:
            return list(section_analyses.values())[0]

        analyses = list(section_analyses.values())

        # Average sentiment score
        avg_score = sum(a.sentiment.score for a in analyses) / len(analyses)
        pos_count = sum(1 for a in analyses if a.sentiment.label == "POSITIVE")
        overall_label = "POSITIVE" if pos_count >= len(analyses) / 2 else "NEGATIVE"

        # Average emotion scores
        avg_emotions = {}
        for label in EMOTION_LABELS:
            avg_emotions[label] = sum(getattr(a.emotions, label) for a in analyses) / len(analyses)

        # Merge keywords (deduplicate, keep order)
        seen = set()
        merged_keywords = []
        for a in analyses:
            for kw in a.keywords:
                if kw.lower() not in seen:
                    seen.add(kw.lower())
                    merged_keywords.append(kw)

        return SectionAnalysis(
            sentiment=SentimentResult(label=overall_label, score=avg_score),
            emotions=EmotionScores(**avg_emotions),
            keywords=merged_keywords[:10],
        )

    def analyze_entry(self, content: str, entry_date: str) -> JournalAnalysis:
        """Full analysis pipeline for a journal entry."""
        sections = JournalParser.parse(content)
        section_analyses = self.analyze_sections(sections)
        overall = self.compute_overall(section_analyses)

        return JournalAnalysis(
            version=ANALYSIS_VERSION,
            analyzed_at=datetime.now().isoformat(),
            entry_date=entry_date,
            sections=section_analyses,
            overall=overall,
        )

    def analyze_file(self, filepath: str) -> JournalAnalysis:
        """Analyze a journal markdown file from disk."""
        with open(filepath) as f:
            content = f.read()

        entry_date = JournalParser.extract_date_from_filename(filepath) or "unknown"
        return self.analyze_entry(content, entry_date)
