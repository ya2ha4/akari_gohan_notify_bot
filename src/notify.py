import asyncio
import datetime
import wave

import discord
import ginza
import spacy


class NotifyParam():
    def __init__(self, root: spacy.tokens.token.Token=None, verb: spacy.tokens.token.Token=None, time: datetime.datetime=None) -> None:
        self._root: spacy.tokens.token.Token = root
        self._verb: spacy.tokens.token.Token = verb
        self._time: datetime.datetime = time


    def MakeRegistrationCompleteMessage(self) -> str:
        return f"{self.MakeDatetimeText()} に「{self.MakeVerbText()}」をお知らせするよ"


    def MakeNotifyMessage(self) -> str:
        return f"「{self.MakeVerbText()}」に対するお知らせ時間になったよ"


    def MakeDatetimeText(self) -> str:
        if self._time is None:
            return None
        return self._time.strftime("%m/%d(%a) %H:%M:%S")


    def MakeVerbText(self) -> str:
        if self._verb is None:
            return None
        return f"{''.join([token.text for token in ginza.phrase(self._verb, join_func=lambda tokens: tokens)])}"


class NotifyTask():
    def __init__(self) -> None:
        self._param: NotifyParam = NotifyParam()
        self._notifyMember: discord.Member = None
        self._notifyTextChannel: discord.TextChannel = None


    def __init__(self, param: NotifyParam) -> None:
        self._param: NotifyParam = param
        self._notifyMember: discord.Member = None
        self._notifyTextChannel: discord.TextChannel = None


    def IsRegistrable(self) -> bool:
        if self._param is None:
            return False
        return self._param._root is not None and self._param._time is not None


    def Notify(self) -> None:
        loop = asyncio.get_event_loop()
        loop.create_task(self._NotifyProcess())


    async def _NotifyProcess(self) -> None:
        # テキストチャンネルにお知らせメッセージを送信
        await self._notifyTextChannel.send(f"{self._notifyMember.mention} "+self._param.MakeNotifyMessage())

        # ユーザがボイスチャンネルに接続中の場合，音声でのお知らせを実行
        if self._notifyMember.voice:
            voiceClient = await self._notifyMember.voice.channel.connect()
            voiceClient.play(discord.FFmpegPCMAudio("voice/test.wav"))
            wavPlayTime = 0.0
            with wave.open("voice/test.wav", "rb") as wavFile:
                wavPlayTime = float(wavFile.getnframes()) / float(wavFile.getframerate())
            await asyncio.sleep(wavPlayTime)
            await voiceClient.disconnect()


    def SetNotifyMember(self, member: discord.Member) -> None:
        self._notifyMember = member


    def SetNotifyTextChannel(self, channel: discord.TextChannel) -> None:
        self._notifyTextChannel = channel
