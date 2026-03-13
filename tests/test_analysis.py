from journal_app.analysis.schemas import (
    EmotionScores,
    JournalAnalysis,
    SectionAnalysis,
    SentimentResult,
)


class TestSentimentResult:
    def test_to_dict(self):
        s = SentimentResult(label="POSITIVE", score=0.9234)
        d = s.to_dict()
        assert d["label"] == "POSITIVE"
        assert d["score"] == 0.9234

    def test_from_dict(self):
        d = {"label": "NEGATIVE", "score": 0.85}
        s = SentimentResult.from_dict(d)
        assert s.label == "NEGATIVE"
        assert s.score == 0.85

    def test_roundtrip(self):
        original = SentimentResult(label="POSITIVE", score=0.91)
        restored = SentimentResult.from_dict(original.to_dict())
        assert restored.label == original.label
        assert restored.score == original.score


class TestEmotionScores:
    def test_dominant(self):
        e = EmotionScores(joy=0.7, sadness=0.1, neutral=0.2)
        assert e.dominant() == "joy"
        assert e.dominant_score() == 0.7

    def test_to_dict(self):
        e = EmotionScores(anger=0.1, joy=0.9)
        d = e.to_dict()
        assert d["anger"] == 0.1
        assert d["joy"] == 0.9
        assert "neutral" in d

    def test_roundtrip(self):
        original = EmotionScores(joy=0.6, sadness=0.2, neutral=0.1, anger=0.05, fear=0.05)
        restored = EmotionScores.from_dict(original.to_dict())
        assert restored.joy == original.joy
        assert restored.sadness == original.sadness


class TestSectionAnalysis:
    def test_to_dict(self):
        sa = SectionAnalysis(
            sentiment=SentimentResult("POSITIVE", 0.9),
            emotions=EmotionScores(joy=0.8),
            keywords=["family", "work"],
        )
        d = sa.to_dict()
        assert d["sentiment"]["label"] == "POSITIVE"
        assert d["emotions"]["joy"] == 0.8
        assert d["keywords"] == ["family", "work"]

    def test_roundtrip(self):
        original = SectionAnalysis(
            sentiment=SentimentResult("POSITIVE", 0.9),
            emotions=EmotionScores(joy=0.8, sadness=0.1),
            keywords=["test"],
        )
        restored = SectionAnalysis.from_dict(original.to_dict())
        assert restored.sentiment.label == original.sentiment.label
        assert restored.emotions.joy == original.emotions.joy
        assert restored.keywords == original.keywords


class TestJournalAnalysis:
    def test_from_dict(self, sample_analysis_json):
        analysis = JournalAnalysis.from_dict(sample_analysis_json)
        assert analysis.version == "1.0.0"
        assert analysis.entry_date == "2023-06-28"
        assert "morning" in analysis.sections
        assert "evening" in analysis.sections
        assert analysis.overall.sentiment.label == "POSITIVE"

    def test_roundtrip(self, sample_analysis_json):
        original = JournalAnalysis.from_dict(sample_analysis_json)
        restored = JournalAnalysis.from_dict(original.to_dict())
        assert restored.version == original.version
        assert restored.entry_date == original.entry_date
        assert restored.overall.sentiment.score == original.overall.sentiment.score
        assert len(restored.sections) == len(original.sections)


class TestJournalAnalyzer:
    def test_analyze_text_with_mocked_models(self, mock_sentiment, mock_emotion):
        from journal_app.analysis.analyzer import JournalAnalyzer

        analyzer = JournalAnalyzer()
        analyzer._sentiment_pipeline = mock_sentiment
        analyzer._emotion_pipeline = mock_emotion

        result = analyzer.analyze_text("I am grateful for my family and health.")
        assert result.sentiment.label == "POSITIVE"
        assert result.sentiment.score == 0.92
        assert result.emotions.joy == 0.65

    def test_analyze_empty_text(self):
        from journal_app.analysis.analyzer import JournalAnalyzer

        analyzer = JournalAnalyzer()
        result = analyzer.analyze_text("")
        assert result.sentiment.label == "NEUTRAL"
        assert result.emotions.neutral == 1.0

    def test_compute_overall_single_section(self, mock_sentiment, mock_emotion):
        from journal_app.analysis.analyzer import JournalAnalyzer

        analyzer = JournalAnalyzer()
        analyzer._sentiment_pipeline = mock_sentiment
        analyzer._emotion_pipeline = mock_emotion

        section = analyzer.analyze_text("I love my life")
        result = analyzer.compute_overall({"morning": section})
        assert result.sentiment.label == section.sentiment.label

    def test_analyze_entry_with_mocked_models(
        self, sample_full_entry, mock_sentiment, mock_emotion
    ):
        from journal_app.analysis.analyzer import JournalAnalyzer

        analyzer = JournalAnalyzer()
        analyzer._sentiment_pipeline = mock_sentiment
        analyzer._emotion_pipeline = mock_emotion

        analysis = analyzer.analyze_entry(sample_full_entry, "2023-06-28")
        assert analysis.version == "1.0.0"
        assert analysis.entry_date == "2023-06-28"
        assert "morning" in analysis.sections
        assert "evening" in analysis.sections
        assert analysis.overall is not None
