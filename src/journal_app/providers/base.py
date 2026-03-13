from abc import ABC, abstractmethod

import requests


class BaseQuoteProvider(ABC):
    api: str
    _content: str = ''
    _author: str = ''

    def request(self):
        if not self.api:
            raise ValueError('BaseQuoteProvider.api not set')
        return requests.get(self.api, timeout=10)

    @abstractmethod
    def load(self):
        ...

    def content(self) -> str:
        return self._content

    def author(self) -> str:
        return self._author


class BaseStorageProvider(ABC):

    def transform_answer(self, a):
        return a

    def transform_question(self, q):
        return q

    def day_questions(self, journal):
        return list(map(self.transform_question, filter(len, journal.day_questions())))

    def night_questions(self, journal):
        return list(map(self.transform_question, filter(len, journal.night_questions())))

    @abstractmethod
    def save(self, journal, quote):
        ...
