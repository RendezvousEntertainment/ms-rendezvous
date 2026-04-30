import logging

import aiohttp
import discord
from discord.ext import commands
from gitlab_api import fetch_titles
from refs import build_reference_lines, find_issues, find_merge_requests
from settings import Settings

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
    logging.info("Version 0.1.0")


@bot.event
async def on_message(message: discord.Message):
    """Scan messages for #nnn / !nnn refs and reply with a linked embed."""
    if message.author.bot:
        return

    issues = find_issues(message.content)
    mrs = find_merge_requests(message.content)
    titles: dict[tuple[str, str], str] = {}
    if (issues or mrs) and settings.gitlab_token:
        async with aiohttp.ClientSession() as session:
            titles = await fetch_titles(
                session,
                settings.domain,
                settings.repo,
                issues,
                mrs,
                settings.gitlab_token,
            )

    lines = build_reference_lines(message.content, settings.repo_url, titles)
    if lines:
        embed = discord.Embed(description="\n".join(lines))
        await message.reply(embed=embed, mention_author=False)

    await bot.process_commands(message)


@bot.command()  # type: ignore
async def ping(ctx: commands.Context):
    """A simple command to ping the bot and check if it's working."""
    await ctx.reply("Pong!")


@bot.command()  # type: ignore
async def hello(ctx: commands.Context):
    """Say hello, the bot will say hello back!"""
    await ctx.reply(f"Hello, {ctx.author.name}, my name is {settings.name}!")
