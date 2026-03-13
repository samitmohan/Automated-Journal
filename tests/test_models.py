from journal_app.models import Answer, Journal, Question


class TestAnswer:
    def test_creation(self):
        a = Answer(1, "hello world")
        assert a.id() == 1
        assert a.content() == "hello world"

    def test_str(self):
        a = Answer(1, "test")
        assert 'id=1' in str(a)
        assert 'test' in str(a)


class TestQuestion:
    def test_creation(self):
        q = Question("What are you grateful for?", total_answers=3)
        assert q.content() == "What are you grateful for?"
        assert q.total_answers == 3
        assert len(q) == 0

    def test_answer_nonempty(self):
        q = Question("test")
        q.answer(1, "something")
        assert len(q) == 1
        assert q.answers()[0].content() == "something"

    def test_answer_empty_ignored(self):
        q = Question("test")
        q.answer(1, "")
        assert len(q) == 0

    def test_multiple_answers(self):
        q = Question("test", total_answers=3)
        q.answer(1, "first")
        q.answer(2, "second")
        q.answer(3, "third")
        assert len(q) == 3


class TestJournal:
    def test_creation(self):
        j = Journal("5MJ", "Test Journal", ["Q1", "Q2"], ["Q3"])
        assert j.namespace() == "5MJ"
        assert j.title() == "Test Journal"
        assert len(j.day_questions()) == 2
        assert len(j.night_questions()) == 1

    def test_id_format(self):
        j = Journal("5MJ", "Test", ["Q1"], ["Q2"])
        journal_id = j.id()
        assert journal_id.startswith("5MJ-")
        # Should contain a date in YYYY-MM-DD format
        parts = journal_id.split("-")
        assert len(parts) == 4  # 5MJ, YYYY, MM, DD

    def test_len(self):
        j = Journal("5MJ", "Test", ["Q1", "Q2"], ["Q3", "Q4", "Q5"])
        assert len(j) == 5

    def test_header_title(self):
        j = Journal("5MJ", "My Journal", ["Q1"], [])
        header = j.header_title()
        assert "My Journal" in header

    def test_default_total_answers(self):
        j = Journal("5MJ", "Test", ["Q1"], [], default_total_answers=5)
        assert j.day_questions()[0].total_answers == 5
