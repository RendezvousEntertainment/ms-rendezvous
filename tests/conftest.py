import sys
from pathlib import Path

# The bot is run as `python3 discord_bot`, which puts `discord_bot/` itself on
# sys.path. Mirror that here so `import refs` works under pytest from the repo
# root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "discord_bot"))
