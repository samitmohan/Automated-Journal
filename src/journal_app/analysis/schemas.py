from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SentimentResult:
    label: str
    score: float

    def to_dict(self) -> dict:
        return {"label": self.label, "score": round(self.score, 4)}

    @classmethod
    def from_dict(cls, data: dict) -> "SentimentResult":
        return cls(label=data["label"], score=data["score"])


@dataclass
class EmotionScores:
    anger: float = 0.0
    disgust: float = 0.0
    fear: float = 0.0
    joy: float = 0.0
    neutral: float = 0.0
    sadness: float = 0.0
    surprise: float = 0.0

    def to_dict(self) -> dict:
        return {k: round(v, 4) for k, v in self.__dict__.items()}

    @classmethod
    def from_dict(cls, data: dict) -> "EmotionScores":
        return cls(**data)

    def dominant(self) -> str:
        scores = self.__dict__
        return max(scores, key=scores.get)

    def dominant_score(self) -> float:
        scores = self.__dict__
        return scores[self.dominant()]


@dataclass
class SectionAnalysis:
    sentiment: SentimentResult
    emotions: EmotionScores
    keywords: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "sentiment": self.sentiment.to_dict(),
            "emotions": self.emotions.to_dict(),
            "keywords": self.keywords,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SectionAnalysis":
        return cls(
            sentiment=SentimentResult.from_dict(data["sentiment"]),
            emotions=EmotionScores.from_dict(data["emotions"]),
            keywords=data.get("keywords", []),
        )


@dataclass
class JournalAnalysis:
    version: str
    analyzed_at: str
    entry_date: str
    sections: dict[str, SectionAnalysis]
    overall: SectionAnalysis

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "analyzed_at": self.analyzed_at,
            "entry_date": self.entry_date,
            "sections": {k: v.to_dict() for k, v in self.sections.items()},
            "overall": self.overall.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "JournalAnalysis":
        return cls(
            version=data["version"],
            analyzed_at=data["analyzed_at"],
            entry_date=data["entry_date"],
            sections={k: SectionAnalysis.from_dict(v) for k, v in data["sections"].items()},
            overall=SectionAnalysis.from_dict(data["overall"]),
        )

    @staticmethod
    def timestamp() -> str:
        return datetime.now().isoformat()
