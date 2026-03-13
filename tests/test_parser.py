from journal_app.analysis.parser import JournalParser


class TestJournalParser:
    def test_parse_morning_section(self, sample_morning_entry):
        sections = JournalParser.parse(sample_morning_entry)
        assert len(sections) == 1
        assert sections[0].name == "morning"
        assert sections[0].time == "08:30 AM"

    def test_parse_morning_questions(self, sample_morning_entry):
        sections = JournalParser.parse(sample_morning_entry)
        morning = sections[0]
        assert "I am grateful for..." in morning.questions
        assert "What would make today great?" in morning.questions
        assert "Daily affirmations" in morning.questions

    def test_parse_morning_answers(self, sample_morning_entry):
        sections = JournalParser.parse(sample_morning_entry)
        morning = sections[0]
        grateful = morning.questions["I am grateful for..."]
        assert len(grateful) == 3
        assert "My family" in grateful
        assert "Good health" in grateful

    def test_parse_full_entry(self, sample_full_entry):
        sections = JournalParser.parse(sample_full_entry)
        assert len(sections) == 2
        assert sections[0].name == "morning"
        assert sections[1].name == "evening"

    def test_parse_evening_section(self, sample_full_entry):
        sections = JournalParser.parse(sample_full_entry)
        evening = sections[1]
        assert evening.time == "09:30 PM"
        assert "Highlights of the day" in evening.questions
        assert "What did I learn today?" in evening.questions

    def test_section_text_property(self, sample_morning_entry):
        sections = JournalParser.parse(sample_morning_entry)
        text = sections[0].text
        assert "My family" in text
        assert "Finishing the project" in text
        assert len(text) > 50

    def test_parse_empty_string(self):
        sections = JournalParser.parse("")
        assert sections == []

    def test_parse_no_sections(self):
        content = "Just some random text\nwith no structure"
        sections = JournalParser.parse(content)
        assert sections == []

    def test_extract_date_from_filename(self):
        assert JournalParser.extract_date_from_filename("5MJ-2023-06-28.md") == "2023-06-28"
        assert JournalParser.extract_date_from_filename("5MJ-2024-01-15.md") == "2024-01-15"

    def test_extract_date_from_filename_no_date(self):
        assert JournalParser.extract_date_from_filename("random.md") is None

    def test_parse_file(self, tmp_path, sample_full_entry):
        filepath = tmp_path / "test.md"
        filepath.write_text(sample_full_entry)
        sections = JournalParser.parse_file(str(filepath))
        assert len(sections) == 2
