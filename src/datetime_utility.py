import datetime
import spacy
from enum import Enum
from typing import List


class Meridiem(Enum):
    AM = 0
    PM = 1
    NOT_MERIDIEM = -1


# 時刻表現をdatetimeへ変換
def time_expression_normalization(root_token: List[spacy.tokens.token.Token]) -> datetime.datetime:
    # 対応文字列
    # (午前午後)?(時)?(分)?(程度)?
    # 午前午後： [午前|午後|AM|PM|A.M.|am|...]
    # 時　　　： [0-24][:：時]
    # 分　　　：([0-59][分]?)|[半]
    num_temp = -1

    # 判別できた時刻表現の保持用
    meridiem_type = Meridiem.NOT_MERIDIEM
    hour = -1
    minute = -1
    for token in root_token:
        # 午前，午後
        _meridiem_type = is_meridiem(token.text)
        if _meridiem_type is not Meridiem.NOT_MERIDIEM:
            meridiem_type = _meridiem_type

        # 数値
        _num_temp = time_expression_to_nummeric(token.text)
        if -1 < _num_temp:
            num_temp = _num_temp

        # 時
        if -1 < "時：:".find(token.text):
            # 既に ":" が出現している場合，秒記述の可能性がある為，処理をスキップ
            if not hour < 0:
                break
            hour = num_temp
            num_temp = -1
    # 分
    if -1 < num_temp:
        minute = num_temp
    else:
        # todo 時分共に情報が取得できなかった場合の処理は未実装
        minute = 0

    if meridiem_type == Meridiem.PM and hour < 13:
        hour += 12
    if 12 <= hour:
        meridiem_type = Meridiem.PM

    now = datetime.datetime.now()
    now_time = datetime.timedelta(hours=now.hour, minutes=now.minute, seconds=now.second)
    target_time = datetime.timedelta(hours=hour, minutes=minute)
    while target_time < now_time:
        if meridiem_type == Meridiem.NOT_MERIDIEM:
            hour += 12
        else:
            hour += 24
        target_time = datetime.timedelta(hours=hour, minutes=minute)
    
    # print(f"{meridiem_type=},{hour=},{minute=}")
    delta = datetime.timedelta(hours=hour, minutes=minute)
    time = datetime.datetime(now.year, now.month, now.day) + delta
    print(f"現在時刻:{now}")
    print(f"目標時刻:{time}")
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
    # 対応文字列
    # (時)?(分)?(程度)?
    # 時　　　： [0-9]*[:|：|時間]
    # 分　　　：([0-9]*[分]?)|[半]
    num_temp = -1

    # 判別できた時刻表現の保持用
    hour = -1
    minute = -1
    for token in root_token:
        # 数値
        _num_temp = time_expression_to_nummeric(token.text)
        if -1 < _num_temp:
            num_temp = _num_temp

        # 時
        if -1 < "時：:".find(token.text[0]):
            # 既に ":" が出現している場合，秒記述の可能性がある為，処理をスキップ
            if not hour < 0:
                break
            hour = num_temp
            num_temp = -1
    # 分
    if -1 < num_temp:
        minute = num_temp
    else:
        # todo 時分共に情報が取得できなかった場合の処理は未実装
        minute = 0

    if hour < 0:
        hour = 0

    now = datetime.datetime.now()
    delta = datetime.timedelta(hours=hour, minutes=minute)
    time = now + delta
    print(f"現在時刻:{now}")
    print(f"目標時刻:{time}")
    return time


# 時刻表現をdatetimeへ変換
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
