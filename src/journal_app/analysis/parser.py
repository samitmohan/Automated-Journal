import re
from dataclasses import dataclass, field


@dataclass
class ParsedSection:
    name: str
    time: str
    questions: dict[str, list[str]] = field(default_factory=dict)

    @property
    def text(self) -> str:
        """Concatenate all answers into a single text block for NLP input."""
        parts = []
        for answers in self.questions.values():
            parts.extend(answers)
        return " ".join(parts)


class JournalParser:
    SECTION_SPLIT = re.compile(r'^---\s*$', re.MULTILINE)
    TIME_PATTERN = re.compile(r'^\s*(\d{1,2}:\d{2}\s*(?:AM|PM))\s*$', re.MULTILINE)
    QUESTION_HEADING = re.compile(r'^###\s+(.+)$', re.MULTILINE)
    ANSWER_LINE = re.compile(r'^\s*\d+\.\s+(.+)$', re.MULTILINE)

    @classmethod
    def parse(cls, content: str) -> list[ParsedSection]:
        """Parse a journal markdown file into structured sections."""
        raw_sections = cls.SECTION_SPLIT.split(content)

        sections = []
        for i, raw in enumerate(raw_sections):
            raw = raw.strip()
            if not raw:
                continue

            time_match = cls.TIME_PATTERN.search(raw)
            if not time_match:
                continue

            time_str = time_match.group(1).strip()
            section_name = "morning" if len(sections) == 0 else "evening"

            parsed = ParsedSection(name=section_name, time=time_str)

            question_blocks = cls.QUESTION_HEADING.split(raw)
            # question_blocks[0] is text before first heading (time stamp etc.)
            # then alternating: heading text, content after heading
            for j in range(1, len(question_blocks), 2):
                question_text = question_blocks[j].strip()
                if j + 1 < len(question_blocks):
                    answer_block = question_blocks[j + 1]
                    answers = cls.ANSWER_LINE.findall(answer_block)
                    answers = [a.strip() for a in answers if a.strip()]
                else:
                    answers = []
                parsed.questions[question_text] = answers

            if parsed.questions:
                sections.append(parsed)

        return sections

    @classmethod
    def parse_file(cls, filepath: str) -> list[ParsedSection]:
        """Parse a journal markdown file from disk."""
        with open(filepath) as f:
            return cls.parse(f.read())

    @classmethod
    def extract_date_from_filename(cls, filename: str) -> str | None:
        """Extract date from filename like 5MJ-2023-06-28.md."""
        match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        return match.group(1) if match else None
