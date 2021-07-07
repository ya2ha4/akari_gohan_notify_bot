import asyncio
import datetime
import json
import typing

import discord
from discord.ext import commands

import text_parsing_process


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

        task = self._tpp.make_task(message.content)
        if task.is_registrable():
            # お知らせ用パラメータ設定
            task.set_notify_member(message.author)
            task.set_notify_text_channel(message.channel)

            # お知らせ実行処理の登録
            loop = asyncio.get_event_loop()
            loop.call_later((task._param._time - datetime.datetime.now()).total_seconds(), task.notify)

            # お知らせ登録完了メッセージの送信
            await message.channel.send(content=task._param.make_registration_complete_message())
    
    def set_response_text_channel_id_list(self, channel_list: typing.List[int]) -> None:
        self._response_text_channel_id_list = channel_list


if __name__ == "__main__":
    intents = discord.Intents.default()
    intents.members = True
    bot = commands.Bot(command_prefix=".", intents=intents)
    message_listener_cog = MessageListenerCog(bot)
    bot.add_cog(message_listener_cog)

    discord_token = None
    with open("token.json", "r") as token_file:
        json_contents = json.load(token_file)
        discord_token = json_contents.get("token")
        message_listener_cog.set_response_text_channel_id_list(json_contents.get("response_text_channel_id_list", None))
    bot.run(discord_token)