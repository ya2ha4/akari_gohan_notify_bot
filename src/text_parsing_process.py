import discord
import ginza
import spacy
from pprint import pprint
from typing import List

import datetime_utility
import notify


# テキストから情報の抽出を行う
class TextParsingProcess():
    def __init__(self) -> None:
        self._nlp = spacy.load('ja_ginza')
        ginza.set_split_mode(self._nlp, "A")


    # 入力文章から情報の抽出を行い抽出情報を表示
    def make_task(self, message: str) -> notify.NotifyTask:
        doc = self._nlp(message)
        param = notify.NotifyParam()

        commands = self._nlp("教える")  # コマンド（仮）の定義
        command_sentence_index = 0
        root_tokens = []
        print("----")
        for sent_index, sent in enumerate(doc.sents):
            # 一文ごとの意味情報を抽出
            root = None         # ROOT（文章の趣旨，係り起点）
            verb = None         # VERB（ROOTの係り受け動詞候補）
            time = None         # TIME（時刻）
            period_time = None   # PERIOD_TIME（時間）
            for token in sent:
                if self.is_root_token(token):
                    root = token
                    root_tokens.append(root)
                    verb = self.get_syntactic_dependency_token_from_tag(token, "動詞-一般")
                    period_time = self.get_syntactic_dependency_token_from_ent_type(token, "Period_Time")
                    time = self.get_syntactic_dependency_token_from_ent_type(token, "Time")
                self.disp_token_attrs(token)

            # NotifyTask用のパラメータがあれば格納
            lemma_token = self._nlp(root.lemma_)
            is_command_sentence = False
            if commands[0].lemma == lemma_token[0].lemma:
                is_command_sentence = True
            # コマンド（仮）に似た単語ならコマンド実行用文章と判断
            elif commands[0].has_vector and lemma_token[0].has_vector:
                if 0.5 <= commands[0].similarity(lemma_token[0]):
                    is_command_sentence = True

            if is_command_sentence:
                param._root = root
                command_sentence_index = sent_index
            
            if period_time is not None:
                param._time = datetime_utility.period_time_expression_normalization(self.get_period_time_tokens(period_time))
            if time is not None:
                param._time = datetime_utility.time_expression_normalization(self.get_time_tokens(time))

            # 以下，デバッグ表示処理
            # 入力文表示
            print(f"入力{sent_index} => {sent.text}")

            # 単語とコマンド（仮）の類似度表示
            def disp_token(token, disp_label) -> None:
                if token is not None:
                    print(f"{disp_label}:{token.lemma_}")
                    lemma_token = self._nlp(token.lemma_)
                    if commands[0].has_vector and lemma_token[0].has_vector:
                        print(f"「{commands[0].text}」との類似度：{commands[0].similarity(lemma_token[0])}")
            disp_token(root, "ROOT")
            disp_token(verb, "VERB")

            # 時間，時刻のTokenから同じ意味合いのlist[Token]を抽出し表示
            def disp_time_tokens(token, dispLabel) -> None:
                if token is not None:
                    period_time_tokens = self.get_period_time_tokens(token)
                    if period_time_tokens is not None:
                        print("時間")
                        pprint(period_time_tokens)
                        datetime_utility.period_time_expression_normalization(period_time_tokens)
                    time_tokens = self.get_time_tokens(token)
                    if time_tokens is not None:
                        print("時刻")
                        pprint(time_tokens)
                        datetime_utility.time_expression_normalization(time_tokens)
            disp_time_tokens(period_time, "Period_Time")
            disp_time_tokens(time, "Time")

            print()
        print("----")

        # コマンド（仮）にかかっている VERB をコマンド（仮）がある文からさかのぼって調べる
        # コマンド（仮）の文の後にかかる VERB が存在するケースは考慮していない
        verb = self.get_syntactic_dependency_token_from_tag(root_tokens[command_sentence_index], "動詞-一般")
        if verb is not None:
            param._verb = verb
        else:
            for i in range(1, command_sentence_index+1):
                verb = self.get_syntactic_dependency_token_from_tag(root_tokens[command_sentence_index-i], "動詞-一般")
                if verb is not None:
                    param._verb = verb
                    break
                verb = self.get_syntactic_dependency_token_from_tag(root_tokens[command_sentence_index-i], "動詞-一般", True)
                if verb is not None:
                    param._verb = verb
                    break
        return notify.NotifyTask(param)
        

    # TokenのROOT判定
    def is_root_token(self, token: spacy.tokens.token.Token) -> bool:
        return (token.dep_ == "ROOT")


    # 時刻のTokenから隣接する時刻Tokenを抽出しリストとして返す
    def get_time_tokens(self, token: spacy.tokens.token.Token) -> List[spacy.tokens.token.Token]:
        return self.get_identical_adjacent_tokens(token, "Time")


    # 時間のTokenから隣接する時間Tokenを抽出しリストとして返す
    def get_period_time_tokens(self, token: spacy.tokens.token.Token) -> List[spacy.tokens.token.Token]:
        return self.get_identical_adjacent_tokens(token, "Period_Time")


    # 隣接する同一固有表現ノードのリストを取得
    def get_identical_adjacent_tokens(self, token: spacy.tokens.token.Token, target: str) -> List[spacy.tokens.token.Token]:
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
    def get_syntactic_dependency_token_from_tag(self, root_token: spacy.tokens.token.Token, target: str, is_check_self: bool=False) -> spacy.tokens.token.Token:
        return self.get_syntactic_dependency_token(root_token, lambda token, target: token.tag_ == target, target, is_check_self)


    # 条件を満たす係り受けトークンを取得（条件：固有表現）
    def get_syntactic_dependency_token_from_ent_type(self, root_token: spacy.tokens.token.Token, target: str, is_check_self: bool=False) -> spacy.tokens.token.Token:
        return self.get_syntactic_dependency_token(root_token, lambda token, target: token.ent_type_ == target, target, is_check_self)


    # 条件を満たす係り受けトークンを取得
    # @param rootToken: 取得元トークン
    # @param checkLambda: トークンのチェック条件
    # @param target: 対象の要素
    # @param isCheckSelf: rootTokenを取得対象とするか
    def get_syntactic_dependency_token(self, root_token: spacy.tokens.token.Token, check_lambda, target: str, is_check_self: bool=False) -> spacy.tokens.token.Token:
        for token in root_token.lefts:
            if check_lambda(token, target):
                return token

        # 見つからなかった場合はさらに係り受け先をチェック
        for token in root_token.lefts:
            ret = self.get_syntactic_dependency_token(token, check_lambda, target)
            if ret is not None:
                return ret

        # 見つからなかった場合、自身をチェック
        if is_check_self and check_lambda(root_token, target):
            return root_token
        return None


    # トークンの要素表示
    def disp_token_attrs(self, token: spacy.tokens.token.Token) -> None:
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
        task = tpp.make_task(input_line)
        print(task._param.make_registration_complete_message())
