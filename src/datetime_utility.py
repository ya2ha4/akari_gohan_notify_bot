import datetime
import spacy
from enum import Enum
from typing import List


class Meridiem(Enum):
    AM = 0
    PM = 1
    NOT_MERIDIEM = -1


# 時刻表現をdatetimeへ変換
def TimeExpressionNormalization(rootToken: List[spacy.tokens.token.Token]) -> datetime.datetime:
    # 対応文字列
    # (午前午後)?(時)?(分)?(程度)?
    # 午前午後： [午前|午後|AM|PM|A.M.|am|...]
    # 時　　　： [0-24][:：時]
    # 分　　　：([0-59][分]?)|[半]
    numTemp = -1

    # 判別できた時刻表現の保持用
    meridiemType = Meridiem.NOT_MERIDIEM
    hour = -1
    minute = -1
    for token in rootToken:
        # 午前，午後
        _meridiemType = IsMeridiem(token.text)
        if _meridiemType is not Meridiem.NOT_MERIDIEM:
            meridiemType = _meridiemType

        # 数値
        _numTemp = TimeExpressionToNummeric(token.text)
        if -1 < _numTemp:
            numTemp = _numTemp

        # 時
        if -1 < "時：:".find(token.text):
            # 既に ":" が出現している場合，秒記述の可能性がある為，処理をスキップ
            if not hour < 0:
                break
            hour = numTemp
            numTemp = -1
    # 分
    if -1 < numTemp:
        minute = numTemp
    else:
        # todo 時分共に情報が取得できなかった場合の処理は未実装
        minute = 0

    if meridiemType == Meridiem.PM and hour < 13:
        hour += 12
    if 12 <= hour:
        meridiemType = Meridiem.PM

    now = datetime.datetime.now()
    nowTime = datetime.timedelta(hours=now.hour, minutes=now.minute, seconds=now.second)
    targetTime = datetime.timedelta(hours=hour, minutes=minute)
    while targetTime < nowTime:
        if meridiemType == Meridiem.NOT_MERIDIEM:
            hour += 12
        else:
            hour += 24
        targetTime = datetime.timedelta(hours=hour, minutes=minute)
    
    # print(f"meridiemType:{meridiemType},hour:{hour},minute:{minute}")
    delta = datetime.timedelta(hours=hour, minutes=minute)
    time = datetime.datetime(now.year, now.month, now.day) + delta
    print(f"現在時刻:{now}")
    print(f"目標時刻:{time}")
    return time


# 午前/午後表現の判定
def IsMeridiem(inText: str) -> Meridiem:
    meridiem = inText.replace(".", "").lower()
    if meridiem == "am" or meridiem == "午前":
        return Meridiem.AM
    if meridiem == "pm" or meridiem == "午後":
        return Meridiem.PM
    return Meridiem.NOT_MERIDIEM


# 時間表現をdatetimeへ変換
def PeriodTimeExpressionNormalization(rootToken: spacy.tokens.token.Token) -> datetime.datetime:
    # 対応文字列
    # (時)?(分)?(程度)?
    # 時　　　： [0-9]*[:|：|時間]
    # 分　　　：([0-9]*[分]?)|[半]
    numTemp = -1

    # 判別できた時刻表現の保持用
    hour = -1
    minute = -1
    for token in rootToken:
        # 数値
        _numTemp = TimeExpressionToNummeric(token.text)
        if -1 < _numTemp:
            numTemp = _numTemp

        # 時
        if -1 < "時：:".find(token.text[0]):
            # 既に ":" が出現している場合，秒記述の可能性がある為，処理をスキップ
            if not hour < 0:
                break
            hour = numTemp
            numTemp = -1
    # 分
    if -1 < numTemp:
        minute = numTemp
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
def TimeExpressionToNummeric(inText: str) -> int:
    # 半を30に変換
    if inText == "半":
        return 30

    # アラビア数字の場合，全角半角問わずint()で変換
    try:
        retValue = int(inText)
        return retValue
    except:
        pass

    # 漢数字の場合の返還
    if inText == "〇":
        return 0
    # 正の整数かつ一万未満のみ対応
    numDef = "〇一二三四五六七八九"
    digitDef = "十百千"

    retValue = 0    # 変換後の整数保持用
    digit = -1      # 桁数（10^n の桁を処理中 => n-1の値が入る）
    for ch in reversed(inText):
        num  = numDef.find(ch)
        if -1 < num:
            # 数字の場合，桁数を乗じて足し合わせ
            retValue += num * pow(10, digit + 1)
            digit = -1 # 桁数も処理したのでリセット
        else:
            # 桁数の場合
            if -1 < digit:
                # 桁数が連続する場合，前の桁数を足し合わせ
                retValue += pow(10, digit + 1)
            digit = digitDef.find(ch)
    # 最上位が桁数で終わっていた場合の足し合わせ
    if -1 < digit:
        retValue += pow(10, digit + 1)

    # 数字でない場合は負の数を返す
    if retValue == 0:
        retValue = -1
    return retValue
