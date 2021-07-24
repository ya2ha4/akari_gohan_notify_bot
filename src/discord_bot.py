import asyncio
import datetime
import json
import logging
import typing
from logging import getLogger

import discord
from discord.ext import commands

import notify_task_list
import text_parsing_process


logger = getLogger(__name__)


class MessageListenerCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self._bot: commands.Bot = bot
        self._tpp: text_parsing_process.TextParsingProcess = text_parsing_process.TextParsingProcess()
        self._response_text_channel_id_list = None


    @commands.Cog.listener(name="on_message")
    async def response_message(self, message: discord.Message) -> None:
        if message.author == self._bot.user:
            return
        
        if self._response_text_channel_id_list is not None:
            needs_response = False
            for id in self._response_text_channel_id_list:
                if id == message.channel.id:
                    needs_response = True
            if not needs_response:
                return

        logger.debug(f"on_message:{message.content=}")
        task = self._tpp.make_task(message.content)
        if task.is_registrable():
            task.register_task(message)


    @commands.Cog.listener(name="on_reaction_add")
    async def response_reaction(self, reaction: discord.Reaction, user: typing.Union[discord.Member, discord.User]) -> None:
        if user == self._bot.user:
            return

        logger.info(f"on_reaction_add:{reaction.emoji=}")
        if reaction.emoji == "❎":

            # cancel(self, reaction, user)
            task = notify_task_list.registered_notify_task_list.find_task(reaction.message.id)
            if task is not None:
                if task._notify_member.id == user.id:
                    logger.info(f"cancel_task")
                    task.cancel()
                    await reaction.message.delete()
                else:
                    logger.info(f"別ユーザのメッセージの為，キャンセルせず")
                    await reaction.remove(user)


    def set_response_text_channel_id_list(self, channel_list: typing.List[int]) -> None:
        self._response_text_channel_id_list = channel_list


if __name__ == "__main__":
    log_format = "[%(asctime)s %(levelname)s %(name)s(%(lineno)s)][%(funcName)s] %(message)s"
    logging.basicConfig(filename=f"logfile.txt", encoding="utf-8", filemode="w", format=log_format)
    #logging.getLogger().setLevel(level=logging.DEBUG)

    intents = discord.Intents.default()
    intents.members = True
    bot = commands.Bot(command_prefix=".", intents=intents)
    message_listener_cog = MessageListenerCog(bot)
    bot.add_cog(message_listener_cog)

    discord_token = None
    with open("config.json", "r") as token_file:
        json_contents = json.load(token_file)
        discord_token = json_contents.get("token")
        message_listener_cog.set_response_text_channel_id_list(json_contents.get("response_text_channel_id_list", None))
    bot.run(discord_token)