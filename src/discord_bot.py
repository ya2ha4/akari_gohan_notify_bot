import asyncio
import datetime
import json

import discord
from discord.ext import commands

import text_parsing_process


class MessageListenerCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self._bot: commands.Bot = bot
        self._tpp: text_parsing_process.TextParsingProcess = text_parsing_process.TextParsingProcess()


    @commands.Cog.listener(name="on_message")
    async def response_message(self, message: discord.Message) -> None:
        if message.author == self._bot.user:
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


if __name__ == "__main__":
    intents = discord.Intents.default()
    intents.members = True
    bot = commands.Bot(command_prefix=".", intents=intents)
    bot.add_cog(MessageListenerCog(bot))

    discord_token = None
    with open("token.json", "r") as token_file:
        json_contents = json.load(token_file)
        discord_token = json_contents.get("token")
    bot.run(discord_token)