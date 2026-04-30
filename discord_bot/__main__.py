import logging
import sys

from bot import bot
from settings import Settings

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    stream=sys.stdout,
    force=True,
)
logging.getLogger().setLevel(logging.DEBUG)

bot.run(Settings().token)
