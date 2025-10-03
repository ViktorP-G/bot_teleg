from src.bot import TelegramBot
from sekret_kode import Telegram_Token

if __name__ == "__main__":
    bot = TelegramBot(Telegram_Token)
    bot.run()
