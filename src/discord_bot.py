import asyncio
import datetime
import json

import discord
from discord.ext import commands

import TextParsingProcess


class MessageListenerCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self._bot: commands.Bot = bot
        self._tpp: TextParsingProcess.TextParsingProcess = TextParsingProcess.TextParsingProcess()


    @commands.Cog.listener(name="on_message")
    async def ResponseMessage(self, message: discord.Message) -> None:
        if message.author == self._bot.user:
            return

        task = self._tpp.MakeTask(message.content)
        if task.IsRegistrable():
            # お知らせ用パラメータ設定
            task.SetNotifyMember(message.author)
            task.SetNotifyTextChannel(message.channel)

            # お知らせ実行処理の登録
            loop = asyncio.get_event_loop()
            loop.call_later((task._param._time - datetime.datetime.now()).total_seconds(), task.Notify)

            # お知らせ登録完了メッセージの送信
            await message.channel.send(content=task._param.MakeRegistrationCompleteMessage())


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