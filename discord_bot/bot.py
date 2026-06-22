import logging

import aiohttp
import discord
from discord.ext import commands
from gitlab_api import fetch_ref_info, fetch_open_merge_requests
from refs import RefInfo, build_reference_lines, find_issues, find_merge_requests
from settings import Settings
import re

# bots need the message content intent to read messages
# https://discordpy.readthedocs.io/en/stable/intents.html
intents = discord.Intents.default()
intents.message_content = True

settings = Settings()

# create our bot
bot = commands.Bot(command_prefix="!", intents=intents)

# register some callbacks and commands


@bot.event
async def on_ready():
    """This callback is triggered when the bot is ready"""
    logging.info(f"Logged in as {bot.user}")
    logging.info(str(bot.user))
    logging.info("Version 0.2.1")


@bot.event
async def on_message(message: discord.Message):
    """Scan messages for #nnn / !nnn refs and reply with a linked embed."""
    if message.author.bot:
        return

    issues = find_issues(message.content)
    mrs = find_merge_requests(message.content)
    wants_open = re.search(r"(?<!\S)!open\b", message.content) is not None

    info: dict[tuple[str, str], RefInfo] = {}
    if settings.gitlab_token and (issues or mrs or wants_open):
        async with aiohttp.ClientSession() as session:
            if wants_open:
                open_mrs = await fetch_open_merge_requests(
                    session, settings.domain, settings.repo, settings.gitlab_token
                )
                for n in open_mrs:
                    if n not in mrs:
                        mrs.append(n)
            if issues or mrs:
                info = await fetch_ref_info(
                    session,
                    settings.domain,
                    settings.repo,
                    issues,
                    mrs,
                    settings.gitlab_token,
                )

    lines = build_reference_lines(issues, mrs, settings.repo_url, info)
    if lines:
        embed = discord.Embed(description="\n".join(lines))
        await message.reply(embed=embed, mention_author=False)

