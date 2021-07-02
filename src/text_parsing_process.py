import ginza
import spacy
from pprint import pprint
from typing import List

import DatetimeUtility
import Notify


# テキストから情報の抽出を行う
class TextParsingProcess():
    def __init__(self) -> None:
        self._nlp = spacy.load('ja_ginza')
        ginza.set_split_mode(self._nlp, "A")


    # 入力文章から情報の抽出を行い抽出情報を表示
    def MakeTask(self, message: str) -> Notify.NotifyTask:
        doc = self._nlp(message)
        param = Notify.NotifyParam()

        commands = self._nlp("教える")  # コマンド（仮）の定義
        commandSentenceIndex = 0
        rootTokens = []
        print("----")
        for sentIndex, sent in enumerate(doc.sents):
            # 一文ごとの意味情報を抽出
            root = None         # ROOT（文章の趣旨，係り起点）
            verb = None         # VERB（ROOTの係り受け動詞候補）
            time = None         # TIME（時刻）
            periodTime = None   # PERIOD_TIME（時間）
            for token in sent:
                if self.IsRootToken(token):
                    root = token
                    rootTokens.append(root)
                    verb = self.GetSyntacticDependencyTokenFromTag(token, "動詞-一般")
                    periodTime = self.GetSyntacticDependencyTokenFromEntType(token, "Period_Time")
                    time = self.GetSyntacticDependencyTokenFromEntType(token, "Time")
                self.DispTokenAttrs(token)

            # NotifyTask用のパラメータがあれば格納
            lemmaToken = self._nlp(root.lemma_)
            isCommandSentence = False
            if commands[0].lemma == lemmaToken[0].lemma:
                isCommandSentence = True
            # コマンド（仮）に似た単語ならコマンド実行用文章と判断
            elif commands[0].has_vector and lemmaToken[0].has_vector:
                if 0.5 <= commands[0].similarity(lemmaToken[0]):
                    isCommandSentence = True

            if isCommandSentence:
                param._root = root
                commandSentenceIndex = sentIndex
            
            if periodTime is not None:
                param._time = DatetimeUtility.PeriodTimeExpressionNormalization(self.GetPeriodTimeTokens(periodTime))
            if time is not None:
                param._time = DatetimeUtility.TimeExpressionNormalization(self.GetTimeTokens(time))

            # 以下，デバッグ表示処理
            # 入力文表示
            print(f"入力{sentIndex} => {sent.text}")

            # 単語とコマンド（仮）の類似度表示
            def dispToken(token, dispLabel) -> None:
                if token is not None:
                    print(f"{dispLabel}:{token.lemma_}")
                    lemmaToken = self._nlp(token.lemma_)
                    if commands[0].has_vector and lemmaToken[0].has_vector:
                        print(f"「{commands[0].text}」との類似度：{commands[0].similarity(lemmaToken[0])}")
            dispToken(root, "ROOT")
            dispToken(verb, "VERB")

            # 時間，時刻のTokenから同じ意味合いのlist[Token]を抽出し表示
            def dispTimeTokens(token, dispLabel) -> None:
                if token is not None:
                    periodTimeTokens = self.GetPeriodTimeTokens(token)
                    if periodTimeTokens is not None:
                        print("時間")
                        pprint(periodTimeTokens)
                        DatetimeUtility.PeriodTimeExpressionNormalization(periodTimeTokens)
                    timeTokens = self.GetTimeTokens(token)
                    if timeTokens is not None:
                        print("時刻")
                        pprint(timeTokens)
                        DatetimeUtility.TimeExpressionNormalization(timeTokens)
            dispTimeTokens(periodTime, "Period_Time")
            dispTimeTokens(time, "Time")

            print()
        print("----")

        # コマンド（仮）にかかっている VERB をコマンド（仮）がある文からさかのぼって調べる
        # コマンド（仮）の文の後にかかる VERB が存在するケースは考慮していない
        verb = self.GetSyntacticDependencyTokenFromTag(rootTokens[commandSentenceIndex], "動詞-一般")
        if verb is not None:
            param._verb = verb
        else:
            for i in range(1, commandSentenceIndex+1):
                verb = self.GetSyntacticDependencyTokenFromTag(rootTokens[commandSentenceIndex-i], "動詞-一般")
                if verb is not None:
                    param._verb = verb
                    break
                verb = self.GetSyntacticDependencyTokenFromTag(rootTokens[commandSentenceIndex-i], "動詞-一般", True)
                if verb is not None:
                    param._verb = verb
                    break
        return Notify.NotifyTask(param)
        

    # TokenのROOT判定
    def IsRootToken(self, token: spacy.tokens.token.Token) -> bool:
        return (token.dep_ == "ROOT")


    # 時刻のTokenから隣接する時刻Tokenを抽出しリストとして返す
    def GetTimeTokens(self, token: spacy.tokens.token.Token) -> List[spacy.tokens.token.Token]:
        return self.GetIdenticalAdjacentTokens(token, "Time")


    # 時間のTokenから隣接する時間Tokenを抽出しリストとして返す
    def GetPeriodTimeTokens(self, token: spacy.tokens.token.Token) -> List[spacy.tokens.token.Token]:
        return self.GetIdenticalAdjacentTokens(token, "Period_Time")


    # 隣接する同一固有表現ノードのリストを取得
    def GetIdenticalAdjacentTokens(self, token: spacy.tokens.token.Token, target: str) -> List[spacy.tokens.token.Token]:
        tokens = list()

        index = token.i
        while 0 <= index and token.doc[index].ent_type_ == target:
            tokens.insert(0, token.doc[index])
            index -= 1

        index = token.i + 1
        while index < len(token.doc) and token.doc[index].ent_type_ == target:
            tokens.append(token.doc[index])
            index += 1

        if len(tokens) == 0:
            return None
        return tokens


    # 条件を満たす係り受けトークンを取得（条件：品詞詳細）
    def GetSyntacticDependencyTokenFromTag(self, rootToken: spacy.tokens.token.Token, target: str, isCheckSelf: bool=False) -> spacy.tokens.token.Token:
        return self.GetSyntacticDependencyToken(rootToken, lambda token, target: token.tag_ == target, target, isCheckSelf)


    # 条件を満たす係り受けトークンを取得（条件：固有表現）
    def GetSyntacticDependencyTokenFromEntType(self, rootToken: spacy.tokens.token.Token, target: str, isCheckSelf: bool=False) -> spacy.tokens.token.Token:
        return self.GetSyntacticDependencyToken(rootToken, lambda token, target: token.ent_type_ == target, target, isCheckSelf)


    # 条件を満たす係り受けトークンを取得
    # @param rootToken: 取得元トークン
    # @param checkLambda: トークンのチェック条件
    # @param target: 対象の要素
    # @param isCheckSelf: rootTokenを取得対象とするか
    def GetSyntacticDependencyToken(self, rootToken: spacy.tokens.token.Token, checkLambda, target: str, isCheckSelf: bool=False) -> spacy.tokens.token.Token:
        for token in rootToken.lefts:
            if checkLambda(token, target):
                return token

        # 見つからなかった場合はさらに係り受け先をチェック
        for token in rootToken.lefts:
            ret = self.GetSyntacticDependencyToken(token, checkLambda, target)
            if ret is not None:
                return ret

        # 見つからなかった場合、自身をチェック
        if isCheckSelf and checkLambda(rootToken, target):
            return rootToken
        return None


    # トークンの要素表示
    def DispTokenAttrs(self, token: spacy.tokens.token.Token) -> None:
        token_attrs = [
            token.i,    # トークン番号
            token.text, # テキスト
            token.lemma_,   # 基本形
            token.pos_, # 品詞
            token.tag_, # 品詞詳細
            token.ent_type_,    # 固有表現
            token.dep_, # 依存関係
            ginza.reading_form(token),  # 読みカナ
            ginza.inflection(token),    # 活用情報
            list(token.lefts),  # 係り受け：左
            list(token.rights)  # 係り受け：右
        ]
        tokenList = [str(a) for a in token_attrs]
        print(tokenList)

if __name__ == "__main__":
    tpp = TextParsingProcess()
    while True:
        print("input>")
        input_line = input()
        task = tpp.MakeTask(input_line)
        print(task._param.MakeRegistrationCompleteMessage())
