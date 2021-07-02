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


    def make_registration_complete_message(self) -> str:
        return f"{self.make_datetime_text()} に「{self.make_verb_text()}」をお知らせするよ"


    def make_notify_message(self) -> str:
        return f"「{self.make_verb_text()}」に対するお知らせ時間になったよ"


    def make_datetime_text(self) -> str:
        if self._time is None:
            return None
        return self._time.strftime("%m/%d(%a) %H:%M:%S")


    def make_verb_text(self) -> str:
        if self._verb is None:
            return None
        return f"{''.join([token.text for token in ginza.phrase(self._verb, join_func=lambda tokens: tokens)])}"


class NotifyTask():
    def __init__(self) -> None:
        self._param: NotifyParam = NotifyParam()
        self._notify_member: discord.Member = None
        self._notify_text_channel: discord.TextChannel = None


    def __init__(self, param: NotifyParam) -> None:
        self._param: NotifyParam = param
        self._notify_member: discord.Member = None
        self._notify_text_channel: discord.TextChannel = None


    def is_registrable(self) -> bool:
        if self._param is None:
            return False
        return self._param._root is not None and self._param._time is not None


    def notify(self) -> None:
        loop = asyncio.get_event_loop()
        loop.create_task(self._notify_process())


    async def _notify_process(self) -> None:
        # テキストチャンネルにお知らせメッセージを送信
        await self._notify_text_channel.send(f"{self._notify_member.mention} "+self._param.make_notify_message())

        # ユーザがボイスチャンネルに接続中の場合，音声でのお知らせを実行
        if self._notify_member.voice:
            voice_client = await self._notify_member.voice.channel.connect()
            voice_client.play(discord.FFmpegPCMAudio("voice/test.wav"))
            wav_play_time = 0.0
            with wave.open("voice/test.wav", "rb") as wav_file:
                wav_play_time = float(wav_file.getnframes()) / float(wav_file.getframerate())
            await asyncio.sleep(wav_play_time)
            await voice_client.disconnect()


    def set_notify_member(self, member: discord.Member) -> None:
        self._notify_member = member


    def set_notify_text_channel(self, channel: discord.TextChannel) -> None:
        self._notify_text_channel = channel
