import logging

from journal_app.providers.base import BaseQuoteProvider

logger = logging.getLogger(__name__)


class ZenQuoteProvider(BaseQuoteProvider):
    api = 'https://zenquotes.io/api/today'

    def load(self):
        try:
            data = self.request().json()
            self._content = data[0]['q']
            self._author = data[0]['a']
        except Exception as e:
            logger.warning("Failed to fetch quote: %s", e)
            self._content = ''
            self._author = ''
        return self
