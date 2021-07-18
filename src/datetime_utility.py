import datetime
import spacy
from enum import IntEnum
from logging import getLogger
from typing import List


logger = getLogger(__name__)


class Meridiem(IntEnum):
    AM = 0
    PM = 1
    NOT_MERIDIEM = -1


class TimeUnit(IntEnum):
    HOUR = 0
    MINUTES = 1
    SECONDS = 2
 

# 時刻表現をdatetimeへ変換
def time_expression_normalization(root_token: List[spacy.tokens.token.Token]) -> datetime.datetime:
    meridiem_type = Meridiem.NOT_MERIDIEM
    time_list: List[int] = _make_time_unit_list(root_token)

    if meridiem_type == Meridiem.PM and time_list[TimeUnit.HOUR] < 13:
        time_list[TimeUnit.HOUR] += 12
    if 12 <= time_list[TimeUnit.HOUR]:
        meridiem_type = Meridiem.PM

    now = datetime.datetime.now()
    now_time = datetime.timedelta(hours=now.hour, minutes=now.minute, seconds=now.second)
    target_time = datetime.timedelta(hours=time_list[TimeUnit.HOUR], minutes=time_list[TimeUnit.MINUTES], seconds=time_list[TimeUnit.SECONDS])
    while target_time < now_time:
        if meridiem_type == Meridiem.NOT_MERIDIEM:
            time_list[TimeUnit.HOUR] += 12
        else:
            time_list[TimeUnit.HOUR] += 24
        target_time = datetime.timedelta(hours=time_list[TimeUnit.HOUR], minutes=time_list[TimeUnit.MINUTES], seconds=time_list[TimeUnit.SECONDS])
    
    delta = datetime.timedelta(hours=time_list[TimeUnit.HOUR], minutes=time_list[TimeUnit.MINUTES], seconds=time_list[TimeUnit.SECONDS])
    time = datetime.datetime(now.year, now.month, now.day) + delta
    logger.debug(f"{meridiem_type=},{time_list[TimeUnit.HOUR]=}, {time_list[TimeUnit.MINUTES]=}, {time_list[TimeUnit.SECONDS]=}")
    logger.debug(f"現在時刻:{now}")
    logger.info(f"目標時刻:{time}")
    return time


# 午前/午後表現の判定
def is_meridiem(in_text: str) -> Meridiem:
    meridiem = in_text.replace(".", "").lower()
    if meridiem == "am" or meridiem == "午前":
        return Meridiem.AM
    if meridiem == "pm" or meridiem == "午後":
        return Meridiem.PM
    return Meridiem.NOT_MERIDIEM


# 時間表現をdatetimeへ変換
def period_time_expression_normalization(root_token: spacy.tokens.token.Token) -> datetime.datetime:
    time_list: List[int] = _make_time_unit_list(root_token)
    now = datetime.datetime.now()
    delta = datetime.timedelta(hours=time_list[TimeUnit.HOUR], minutes=time_list[TimeUnit.MINUTES], seconds=time_list[TimeUnit.SECONDS])
    time = now + delta
    logger.debug(f"{time_list[TimeUnit.HOUR]=}, {time_list[TimeUnit.MINUTES]=}, {time_list[TimeUnit.SECONDS]=}")
    logger.debug(f"現在時刻:{now}")
    logger.info(f"目標時刻:{time}")
    return time


# 数値の文字列をintへ変換
def time_expression_to_nummeric(in_text: str) -> int:
    # 半を30に変換
    if in_text == "半":
        return 30

    # アラビア数字の場合，全角半角問わずint()で変換
    try:
        ret_value = int(in_text)
        return ret_value
    except:
        pass

    # 漢数字の場合の返還
    if in_text == "〇":
        return 0
    # 正の整数かつ一万未満のみ対応
    NUM_DEF = "〇一二三四五六七八九"
    DIGIT_DEF = "十百千"

    ret_value = 0    # 変換後の整数保持用
    digit = -1      # 桁数（10^n の桁を処理中 => n-1の値が入る）
    for ch in reversed(in_text):
        num  = NUM_DEF.find(ch)
        if -1 < num:
            # 数字の場合，桁数を乗じて足し合わせ
            ret_value += num * pow(10, digit + 1)
            digit = -1 # 桁数も処理したのでリセット
        else:
            # 桁数の場合
            if -1 < digit:
                # 桁数が連続する場合，前の桁数を足し合わせ
                ret_value += pow(10, digit + 1)
            digit = DIGIT_DEF.find(ch)
    # 最上位が桁数で終わっていた場合の足し合わせ
    if -1 < digit:
        ret_value += pow(10, digit + 1)

    # 数字でない場合は負の数を返す
    if ret_value == 0:
        ret_value = -1
    return ret_value


# トークン列から時間/時刻単位ごとの数値を List[int] = [hour, minutes, seconds] となるよう変換
def _make_time_unit_list(root_token: List[spacy.tokens.token.Token]) -> List[int]:
    num_stack: List[int] = []

    # 判別できた時刻表現の保持用
    time_list: List[int] = [-1, -1, -1] # [hour, minute, seconds]
    for token in root_token:
        logger.debug(f"parse: {token.text}")

        # 数値
        _num_temp = time_expression_to_nummeric(token.text)
        if -1 < _num_temp:
            num_stack.append(_num_temp)

        # 時間単位
        if -1 < ":：".find(token.text):
            for i in range(len(time_list)):
                if time_list[i] < 0:
                    time_list[i] = num_stack.pop()
                    logger.debug(f"set: {time_list[i]=}")
                    break

        # 時間単位
        TIME_DEF = ["時", "分", "秒"]#"時間"対応できない
        for i in range(len(TIME_DEF)):
            if -1 < token.text.find(TIME_DEF[i]):
                if not time_list[i] < 0:
                    logger.warning(f"既に「{TIME_DEF[i]}」は設定済み:{time_list[i]}")
                time_list[i] = num_stack.pop()
                logger.debug(f"set {TIME_DEF[i]}: {time_list[i]=}")

    # 最後の数字を未設定の時間単位うち最大となるよう設定
    if num_stack:
        index = -1
        for i in range(len(time_list)-1, -1, -1):
            if -1 < time_list[i]:
                index = i + 1
                break
        for i in range(len(num_stack)):
            time_list[index+i] = num_stack[i]
        num_stack.clear()

    # 未設定の時間単位を0に設定
    for i in range(len(time_list)):
        if time_list[i] < 0:
            time_list[i] = 0

    return time_list
