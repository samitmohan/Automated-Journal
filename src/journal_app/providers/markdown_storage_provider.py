import json
import logging
import os
import re
import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from journal_app.providers.base import BaseStorageProvider

logger = logging.getLogger(__name__)


class MarkdownStorageProvider(BaseStorageProvider):
    TIME_REGEX = r'---\n(\d{2}:\d{2})'

    def __init__(
        self,
        root_dir: str,
        output_dir: str,
        header_template: str,
        question_template: str,
    ) -> None:
        self._root_dir = root_dir
        self._output_dir = output_dir
        self._template_dir = os.path.join(root_dir, 'templates')
        self.copy_template(header_template)
        self.copy_template(question_template)
        self._env = Environment(
            loader=FileSystemLoader(output_dir),
            autoescape=select_autoescape()
        )
        self._header_template = self._env.get_template(header_template)
        self._question_template = self._env.get_template(question_template)

    def year_path(self, journal):
        return f'{self._output_dir}/{journal.year()}'

    def file_path(self, journal):
        return f'{self.year_path(journal)}/{journal.id()}.md'

    def template_realpath(self, filename: str):
        return os.path.realpath(f'{self._output_dir}/{filename}')

    def has_template(self, filename: str):
        path = Path(self.template_realpath(filename))
        return path.exists()

    def copy_template(self, filename: str):
        if not self.has_template(filename):
            src = os.path.join(self._template_dir, filename)
            dst = self.template_realpath(filename)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)

    def filled_times(self, journal, count: int):
        filepath = self.file_path(journal)
        file = Path(filepath)
        try:
            content = file.read_text()
            matches = re.findall(self.TIME_REGEX, content)
            return len(matches) == count
        except FileNotFoundError:
            return False

    def filled_once(self, journal):
        return self.filled_times(journal, 1)

    def filled_twice(self, journal):
        return self.filled_times(journal, 2)

    def transform_answer(self, a):
        return {
            'id': a.id(),
            'content': a.content()
        }

    def transform_question(self, q):
        return {
            'content': q.content(),
            'answers': map(self.transform_answer, q.answers()),
        }

    def save(self, journal, quote):
        if self.filled_once(journal) and len(journal) > 0:
            self.save_night(journal)
        elif not self.filled_twice(journal) and len(journal) > 0:
            self.save_day(journal, quote)

    def save_day(self, journal, quote):
        output = self._header_template.render(
            author=quote.author(),
            quote=quote.content(),
            title=journal.title(),
            date=journal.pretty_date()
        ) + '\n\n' + self._question_template.render(
            time=journal.iso_time(),
            questions=self.day_questions(journal)
        )

        os.makedirs(self.year_path(journal), exist_ok=True)

        with open(self.file_path(journal), 'w') as f:
            f.write(output)

    def save_night(self, journal):
        output = self._question_template.render(
            time=journal.iso_time(),
            questions=self.night_questions(journal)
        )

        with open(self.file_path(journal), 'a') as f:
            f.write(output)

    def analysis_path(self, journal_path: str) -> str:
        return journal_path.replace('.md', '.analysis.json')

    def save_analysis(self, journal_path: str, analysis_dict: dict) -> str:
        path = self.analysis_path(journal_path)
        with open(path, 'w') as f:
            json.dump(analysis_dict, f, indent=2)
        return path

    def load_analysis(self, journal_path: str) -> dict | None:
        path = self.analysis_path(journal_path)
        try:
            with open(path) as f:
                return json.load(f)
        except FileNotFoundError:
            return None
