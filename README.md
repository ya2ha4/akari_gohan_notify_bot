# akari_gohan_notify_bot
akari_gohan_notify_bot は Discord のテキストチャットで『「いつ」何かを「教えて」』というような入力をすると指定した時刻にメッセージと音声で通知をしてくれるbotです。</br>


## 出来ること
### テキストチャットによる通知の登録
テキストチャットに『「いつ（時刻または時間）」になったら「教えて」』というような文を入力することで通知を登録出来ます。</br>
登録が成功した場合、いつ通知をするかのメッセージが書き込まれます。</br>

<img src="screenshots/image_notify.png" width="480px">

通知登録のメッセージ例（登録方法の詳細は****を参照して下さい）
- ごはんを炊き始めたから19時30分になったら教えて
- ごはんを炊き始めたから午後七時半になったら教えて
- カップ麺にお湯を入れた。3分後になったら教えて。
- チャーシュー煮込み始めたし二時間後になったら教えてほしい


### リアクションによる通知のキャンセル
通知の登録後に送られてくるメッセージのリアクションで通知を取り消すことが出来ます。</br>


### メンションおよび音声による通知
通知の時刻になるとメンション付きで時間になった旨を伝えるメッセージが送られてきます。</br>
また、通知の時刻に任意のボイスチャンネルに接続していると通知音声を再生するようになっています。</br>


## セットアップ方法
セットアップには以下の作業が必要です
- Discord botアカウントの作成
- Discordサーバの設定
- bot起動用設定ファイル (config.json) 編集
- ボットの実行環境作成


### Discord botアカウントの作成
1. 開発者サイトにログイン
	- Discord Developer Portal https://discordapp.com/developers/applications/
1. "Applications" タブの ”New Application" を選択しアプリケーションを作成、</br>
	"My Applications" から作成したアプリケーションを選択
	- "General Information" タブで以下の項目を設定
		- APP ICON：ボットのアイコン（設定は任意です）
		- NAME：ボットのユーザ名
	- "Bot" タブで "Add Bot" を選択、以下の項目を設定
		- PRESENCE INTENT：有効
		- SERVER MEMBERS INTENT：有効


### Discordサーバの設定
1. ボットアカウントの追加</br>
	1. "My Applications" から作成したアプリケーションの</br>
		"OAuth2" タブの "OAuth2 URL Generator" にある "bot" にチェックを入れ、下に表示されるURLをコピー
	1. コピーしたURLにアクセスし、"サーバーに追加" からボットを追加したいサーバを選択し "承認" を選択
1. ボットアカウントに "管理者" または以下の権限があるロールを付与
    - チャンネルを見る
	- メッセージを送信
	- メッセージの管理
	- メッセージ履歴を読む
	- リアクションの追加
	- すべてのロールにメンション
	- 接続
	- 発言


### bot起動用設定ファイル (config.json) 編集
config_template.json をコピーし名前を config.json に変更して以下の編集を行って下さい
- トークン (token)
	1. [開発者サイト](https://discordapp.com/developers/applications/) のボット用アプリケーション "Bot" タブの</br>
	"TOKEN" 項目にある "COPY" を選択（トークンは他人に知られないよう管理して下さい）
	1. "token" の行、 " " の""中にコピーしたトークン文字列を貼り付け
- bot反応テキストチャットのリスト (response_text_channel_id_list)
	1. botが反応するテキストチャンネルを右クリックして "IDをコピー" を選択
	1. "response_text_channel_id_list" の行、 [ ] の内側にコピーしたIDを貼り付け
		- 複数のテキストチャットで反応させたい場合 , で区切ってIDを貼り付けて下さい
			- [テキストチャンネルID_1, テキストチャンネルID_2, ... テキストチャンネルID_N]

<summary>config.json のサンプル</summary>

<pre>
{
    "token": "AbCD1EFgH2IKLm3nOPQ4RsTU.VWxYZ5.ABCd6eFGH7IjKL8MNOp9qRST_UvWX1YZ",
    "response_text_channel_id_list": [12345678901234567890, 12345678901234567891]
}
</pre>


### ボット動作環境作成
1. Python のインストール
	- Pythonのインストーラをダウンロードしインストール（本ボットは3.9.*系で動作確認しています）
		- インストールする際 "Add Python *.* to PATH" の項目にチェックを付けて下さい
		- Python公式 https://www.python.org/
1. pipenv のインストール
	- コマンドプロンプトやターミナルなどで ```pip install pipenv``` または ```pip3 install pipenv``` を実行
	- 環境変数 ```PIPENV_VENV_IN_PROJECT``` に ```true``` を設定
1. 実行に必要なパッケージのインストール
	- MuteAll_ex がある場所でコマンドプロンプトやターミナルなどを開き ```pipenv install``` を実行


## ボットの起動方法
- akari_gohan_notify_bot がある場所でコマンドプロンプトやターミナルなどを開き ```pipenv run src\discord_bot.py``` を実行
	- ボットのアカウントがオンラインになればOK


## 注意点
### AM, PMや : でうまく反応しない場合がある
時刻表示で"AM", "p.m" などの表記を使うと正しく判定しない場合があります。</br>
その場合は、"午前", "午後" または24時間表記で入力して下さい。</br>
</br>
時刻、時間の表記で時分などを表現する際に : の表記を使うと正しく判定しない場合があります。</br>
その場合は、"時", "分", "秒" で入力して下さい。</br>


### 一度botを停止させると登録していた通知予約が消える
登録した通知情報は外部に保存していない為botを停止させると通知情報は消えてしまします。</br>


## Links
### 使用ライブラリなどのライセンス
- discord.py</br>
Copyright (c) 2015-present Rapptz</br>
https://github.com/Rapptz/discord.py/blob/master/LICENSE</br>

- ginza</br>
Copyright (c) 2019 Megagon Labs</br>
https://github.com/megagonlabs/ginza/blob/develop/LICENSE</br>
