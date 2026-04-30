import logging

from bot import bot
from settings import Settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

bot.run(Settings().token)
