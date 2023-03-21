import config
from providers.markdown_storage_provider import MarkdownStorageProvider
from providers.zen_quote_provider import ZenQuoteProvider
from py_two_minute_journal import Journal, JournalCommandLine


def main():
    journal = Journal(
        config.NAMESPACE,
        config.TITLE,
        config.DAY_QUESTIONS,
        config.NIGHT_QUESTIONS,
        config.DEFAULT_TOTAL_ANSWERS
    )

    storage = MarkdownStorageProvider(
        config.ROOT_DIR,
        config.OUTPUT_DIR,
        config.HEADER_TEMPLATE,
        config.QUESTION_TEMPLATE
    )

    quote = ZenQuoteProvider()

    quote_cli = JournalCommandLine(
        journal,
        quote,
        storage,
        config.MESSAGES
    )

    quote_cli.prompt()

    quote_cli.save()


if __name__ == '__main__':
    main()
