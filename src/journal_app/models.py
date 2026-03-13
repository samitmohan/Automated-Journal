from datetime import datetime


class Journal:

    def __init__(
        self,
        namespace: str,
        title: str,
        day_questions: list,
        night_questions: list,
        default_total_answers: int = 3,
    ) -> None:
        self._title = title
        self._datetime = datetime.today()
        self._namespace = namespace
        self._default_total_answers = default_total_answers
        self._day_questions = list(map(self.add_question, day_questions))
        self._night_questions = list(map(self.add_question, night_questions))

    def add_question(self, question: str):
        return Question(question=question, total_answers=self._default_total_answers)

    def namespace(self) -> str:
        return self._namespace

    def id(self) -> str:
        return f'{self.namespace()}-{self.iso_date()}'

    def title(self) -> str:
        return self._title

    def year(self) -> int:
        return self._datetime.year

    def iso_date(self) -> str:
        return self._datetime.strftime("%Y-%m-%d")

    def iso_time(self) -> str:
        return self._datetime.strftime('%I:%M %p')

    def pretty_date(self) -> str:
        return self._datetime.strftime('%A, %b %d %Y')

    def header_title(self) -> str:
        return f'{self._title} | {self.pretty_date()}'

    def day_questions(self):
        return self._day_questions

    def night_questions(self):
        return self._night_questions

    def __len__(self):
        return len(self.day_questions()) + len(self.night_questions())


class Question:

    def __init__(self, question, total_answers=3) -> None:
        self.question = question
        self.total_answers = total_answers
        self._quote = None
        self._answers = []

    def answer(self, id: str, answer: str):
        if len(answer) > 0:
            self._answers.append(Answer(id, answer))

    def content(self):
        return self.question

    def answers(self):
        return self._answers

    def __str__(self) -> str:
        answers = '\n '.join(map(str, self._answers))
        return f"<Question content='{self.content()}'>\n {answers}\n</Question>"

    def __len__(self):
        return len(self._answers)


class Answer:

    def __init__(self, id, answer) -> None:
        self._id = id
        self._answer = answer

    def id(self):
        return self._id

    def content(self):
        return self._answer

    def __str__(self) -> str:
        return f'<Answer id={self.id()} content="{self.content()}"/>'
