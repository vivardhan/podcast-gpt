# Package Imports
from google_client_provider import GoogleClientProvider
from qa_bot.qa_bot import QABot

def main():
    gc_provider = GoogleClientProvider()
    bot = QABot(gc_provider)
    bot.answer_questions()

if __name__ == "__main__":
    main()