import asyncio
import datetime
import wave
from logging import getLogger

import discord
import ginza
import spacy


logger = getLogger(__name__)


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
    _play_voice_lock: asyncio.Lock = asyncio.Lock()

    def __init__(self) -> None:
        self._param: NotifyParam = NotifyParam()
        self._notify_member: discord.Member = None
        self._notify_text_channel: discord.TextChannel = None
        self._notify_time_handler: asyncio.TimerHandle = None
        self._register_send_message: discord.Message = None


    def __init__(self, param: NotifyParam) -> None:
        self._param: NotifyParam = param
        self._notify_member: discord.Member = None
        self._notify_text_channel: discord.TextChannel = None
        self._notify_time_handler: asyncio.TimerHandle = None
        self._register_send_message: discord.Message = None


    def is_registrable(self) -> bool:
        if self._param is None:
            return False
        return self._param._root is not None and self._param._time is not None


    def register_task(self, message: discord.Message) -> None:
        loop = asyncio.get_event_loop()
        loop.create_task(self._register_task_process(message))


    async def _register_task_process(self, message: discord.Message) -> None:
        # お知らせ用パラメータ設定
        self.set_notify_member(message.author)
        self.set_notify_text_channel(message.channel)

        # お知らせ実行処理の登録
        loop = asyncio.get_event_loop()
        self._notify_time_handler = loop.call_later((self._param._time - datetime.datetime.now()).total_seconds(), self.notify)

        # お知らせ登録完了メッセージの送信
        embed_text =  f":negative_squared_cross_mark: お知らせのキャンセル\n"
        embed = discord.Embed()
        embed.add_field(name="リアクションで操作が出来ます", value=embed_text, inline=False)
        send_message = await message.channel.send(content=self._param.make_registration_complete_message(), embed=embed)
        await send_message.add_reaction("❎")
        logger.info(f"registered:{self._param._verb=}, {self._param._time=}")

        self._register_send_message = send_message
        import notify_task_list
        notify_task_list.registered_notify_task_list.append_task(self)


    def notify(self) -> None:
        loop = asyncio.get_event_loop()
        loop.create_task(self._notify_process())


    async def _notify_process(self) -> None:
        logger.debug(f"start _notify_process")
        # テキストチャンネルにお知らせメッセージを送信
        await self._notify_text_channel.send(f"{self._notify_member.mention} "+self._param.make_notify_message())

        async with NotifyTask._play_voice_lock:
            # ユーザがボイスチャンネルに接続中の場合，音声でのお知らせを実行
            if self._notify_member.voice:
                voice_client = await self._notify_member.voice.channel.connect()
                file_name = "voice/notify.wav"
                voice_client.play(discord.FFmpegPCMAudio(file_name))
                logger.debug(f"play: {file_name}")
                wav_play_time = 0.0
                with wave.open(file_name, "rb") as wav_file:
                    wav_play_time = float(wav_file.getnframes()) / float(wav_file.getframerate())
                await asyncio.sleep(wav_play_time)
                await voice_client.disconnect()

        import notify_task_list
        notify_task_list.registered_notify_task_list.remove_task(self)
        logger.info(f"finish _notify_process")


    def cancel(self) -> None:
        self._notify_time_handler.cancel()


    def set_notify_member(self, member: discord.Member) -> None:
        self._notify_member = member


    def set_notify_text_channel(self, channel: discord.TextChannel) -> None:
        self._notify_text_channel = channel
