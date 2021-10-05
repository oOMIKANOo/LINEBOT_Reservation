from djreservation.views import ProductReservationView
from re import match, split
from urllib import parse
from django.shortcuts import render
# 自分で追加した分
from django.views.decorators.csrf import csrf_exempt
from linebot import LineBotApi, WebhookHandler
from django.http import HttpResponseForbidden, HttpResponse
from linebot.exceptions import InvalidSignatureError

# linebot.modelsから処理したいイベントをimport
from linebot.models import (
    MessageEvent, TextMessage, FollowEvent, UnfollowEvent,
    TextSendMessage, PostbackEvent, FlexSendMessage,
)

from reserve_system.models import reservation

# モデル
from .models import User, Reservation

from urllib.parse import parse_qs

from .chat_session import ChatSession

from django.utils.timezone import make_aware
import datetime


import os
from os.path import join, dirname
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv(verbose=True)
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

CHANNEL_ACCESS_TOKEN = os.environ.get("CHANNEL_ACCESS_TOKEN")
LINE_ACCESS_SECRET = os.environ.get("LINE_ACCESS_SECRET")


# 各クライアントライブラリのインスタンス作成
line_bot_api = LineBotApi(channel_access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(channel_secret=LINE_ACCESS_SECRET)

"""
class MyObjectReservation(ProductReservationView):
    base_model = book     # required
    amount_field = 'quantity'  # required
"""

@csrf_exempt
def callback(request):
    if request.method == "GET":
        return HttpResponse("please POST access")

    else:
        # リクエストヘッダーから署名検証のための値を取得
        signature = request.META['HTTP_X_LINE_SIGNATURE']
        # リクエストボディを取得
        body = request.body.decode('utf-8')
        try:
            # 署名を検証し、問題なければhandleに定義されている関数を呼び出す
            handler.handle(body, signature)
        except InvalidSignatureError:
            # 署名検証で失敗したときは例外をあげる
            HttpResponseForbidden()
            print(
                "Invalid signature. Please check your channel access token/channel secret.")
        # handleの処理を終えればOK
        return HttpResponse('OK', status=200)


# addメソッドの引数にはイベントのモデルを入れる
# 関数名は自由
# フォローイベントの場合の処理
@handler.add(FollowEvent)
def handle_follow(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text='なかもり歯科医院公式LINEに登録いただきありがとうございます。')
    )
    # ユーザ新規登録処理
    user_id = event.source.user_id
    user = User.objects.filter(user_id=user_id)
    if(user):
        user.update(deleted_flag=False)
    else:
        profile = line_bot_api.get_profile(user_id)
        display_name = profile.display_name
        User(user_id=user_id, display_name=display_name).save()


# フォローを外されたときの処理
@handler.add(UnfollowEvent)
def handle_unfollow(event):
    user_id = event.source.user_id
    user = User.objects.filter(user_id=user_id)
    user.update(deleted_flag=True)


# メッセージイベントの場合の処理
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    # メッセージでもテキストの場合はオウム返しする
    """
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text='あ'+event.message.text)
    )
    """
    text = event.message.text
    user_id = event.source.user_id
    # session = ChatSession(UserId=user_id)

    """
    print("送信内容：", text)
    print("ユーザID：", user_id)
    """
    # print(event)

    # 処理分け
    if text == "予約":

        line_bot_api.reply_message(
            event.reply_token, messages=select_menu())

    if text == "予約内容の確認":
        line_bot_api.reply_message(
            event.reply_token,
            messages=info(event))

    if text == "あとどれくらい？":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='あとどれくらい'+event.message.text)
        )


# 選択肢から選ばれた時(postback)に呼ばれるイベント
@handler.add(PostbackEvent)
def handler_postback(event):
    # インスタンス
    user_id = event.source.user_id
    # session = ChatSession(UserId=user_id)

    # プロフィール名を取得
    profile = line_bot_api.get_profile(user_id)
    display_name = profile.display_name
    # 送信された内容をparse
    postback_data = event.postback.data

    # parsed = parse_qs(postback_data)

    # print(parsed)
    print(postback_data)

    splitdata = postback_data.split('&')

    """
    if splitdata[0] == 'type':
        how_many_times = splitdata[1]
        if how_many_times == '1':
            # session["hospital_num"]="99999999"
            line_bot_api.reply_message(
                event.reply_token,
                messages=select_date()
            )
        elif how_many_times == '2':
            line_bot_api.reply_message(
                event.reply_token,
                messages=select_date()
            )
    """
    if splitdata[0] == "date":
        postback_param = event.postback.params
        # session["date"] = postback_param["date"]

        print(postback_param["date"])
        line_bot_api.reply_message(
            event.reply_token,
            messages=select_time(postback_param["date"])
        )
    elif splitdata[0] == "time":
        print(splitdata[1])  # 例:2021-10-31
        print(splitdata[2])  # 例:17

        line_bot_api.reply_message(
            event.reply_token,
            messages=confirm(splitdata[1], splitdata[2])
        )
    elif splitdata[0] == "yes":

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="予約完了しました。ご来院の際は、LINEのプロフィール名をお伝えください")
        )
        # split_date = splitdata[1].split('-')
        # dt_aware = make_aware(datetime.datetime(int(split_date[0]), int(split_date[1]), int(split_date[2]), int(splitdata[2]), 0, 0, 1000))
        # print(dt_aware)
        # Reservation.objects.create(reservation_date=dt_aware, user=User(user_id=event.source.user_id))

    elif splitdata[0] == "no":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="キャンセルしました。予約は行われておりません。予約を再度行う際は、予約ボタンを押してください")
        )

    elif splitdata[0] == "cancel":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="キャンセルしました。予約は行われておりません。予約を再度行う際は、予約ボタンを押してください")
        )
    elif splitdata[0] == "other":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="予約は行われておりません。")
        )
    elif splitdata[0] == "check":
        line_bot_api.reply_message(
            event.reply_token,
            messages=select_date()
        )


def select_frequently():
    # 初診か再診かを問うflex message
    message_template_times = {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "初診か再診かを選択してください",
                    "size": "md",
                    "align": "center"
                }
            ]
        },
        "hero": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "（1つのみ選択可能です）",
                    "size": "xs",
                    "align": "center"
                },
                {
                    "type": "separator"
                }
            ]
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "button",
                            "action": {
                                "type": "postback",
                                "label": "初診",
                                "data": "type&1"
                            },
                            "margin": "md",
                            "style": "primary",
                            "color": "#999999"
                        },
                        {
                            "type": "button",
                            "action": {
                                "type": "postback",
                                "label": "再診",
                                "data": "type&2"
                            },
                            "margin": "md",
                            "style": "primary",
                            "color": "#999999"
                        }
                    ],
                    "margin": "md"
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": "キャンセル",
                        "data": "cancel"
                    }
                }
            ]
        }
    }

    container_obj = FlexSendMessage(
        alt_text='select', contents=message_template_times)
    return container_obj


def select_date():
    message_template_date = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "来院希望日を選んでください。",
                    "margin": "sm",
                    "align": "center"
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "button",
                    "action": {
                        "type": "datetimepicker",
                        "label": "希望日を選択する",
                        "data": "date",
                        "mode": "date"
                    }
                }
            ]
        }
    }
    container_obj = FlexSendMessage(
        alt_text="date", contents=message_template_date)
    return container_obj


def select_time(date):

    container_obj = FlexSendMessage(
        alt_text="time", contents={
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "ご希望の時間帯を選択してください。（緑色のボタンは予約可能な時間です。）",
                        "wrap": True,
                        "size": "lg"

                    },
                    {
                        "type": "separator"
                    }
                ]
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "button",
                                "action": {
                                    "type": "postback",
                                    "label": "9時～",
                                    "data": "time&"+date+"&9"
                                },
                                "margin": "sm",
                                "style": "primary",
                                "color": "#009933"
                            },
                            {
                                "type": "button",
                                "action": {
                                    "type": "postback",
                                    "label": "10時～",
                                    "data": "time&"+date+"&10"
                                },
                                "margin": "sm",
                                "style": "primary",
                                "color": "#009933"
                            },
                            {
                                "type": "button",
                                "action": {
                                    "type": "postback",
                                    "label": "11時～",
                                    "data": "time&"+date+"&11"
                                },
                                "margin": "sm",
                                "style": "primary",
                                "color": "#009933"
                            }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "button",
                                "action": {
                                    "type": "postback",
                                    "label": "15時～",
                                    "data": "time&"+date+"&15"
                                },
                                "color": "#009933",
                                "style": "primary",
                                "margin": "sm"
                            },
                            {
                                "type": "button",
                                "action": {
                                    "type": "postback",
                                    "label": "16時～",
                                    "data": "time&"+date+"&16"
                                },
                                "margin": "sm",
                                "style": "primary",
                                "color": "#009933"
                            },
                            {
                                "type": "button",
                                "action": {
                                    "type": "postback",
                                    "label": "17時～",
                                    "data": "time&"+date+"&17"
                                },
                                "margin": "sm",
                                "style": "primary",
                                "color": "#009933"
                            }
                        ],
                        "margin": "sm"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "button",
                                "action": {
                                    "type": "postback",
                                    "label": "18時～",
                                    "data": "time&"+date+"&18"
                                },
                                "margin": "sm",
                                "style": "primary",
                                "color": "#009933"
                            },
                            {
                                "type": "button",
                                "action": {
                                    "type": "postback",
                                    "label": "終了",
                                    "data": "cancel"
                                },
                                "margin": "sm",
                                "style": "primary",
                                "color": "#0033CC"
                            }
                        ]
                    }
                ]
            }
        }

    )
    return container_obj


def confirm(date, time):
    date_split = date.split('-')
    year = date_split[0]
    month = date_split[1]
    day = date_split[2]
    container_obj = FlexSendMessage(
        alt_text="confirm",
        contents={
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "来院希望は"+year+"年"+month+"月"+day+"日"+time+"時からでよろしいですか？",
                        "wrap": True,
                        "size": "md"
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "postback",
                            "label": "はい",
                            "data": "yes&"+date+"&"+time
                        },
                        "margin": "sm"
                    },
                    {
                        "type": "button",
                        "action": {
                            "type": "postback",
                            "label": "いいえ",
                            "data": "no&"+date+"&"+time
                        },
                        "margin": "sm"
                    }
                ]
            }
        }
    )
    return container_obj


def info(event):
    user_id = event.source.user_id
    reserve = Reservation.objects.filter(
        user=User(user_id=user_id)).order_by('reservation_date')
    print(reserve[0])
    year = reserve[0].reservation_date
    print(year)
    container_obj = FlexSendMessage(
        alt_text='info',
        contents={
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "ご予約状況",
                        "size": "lg",
                        "decoration": "underline",
                        "align": "center",
                        "wrap": False
                    }
                ]
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "wrap": True,
                        "text": "ご予約はxx年xx月xx日xx時からでお取りしています。",
                        "size": "md",
                        "align": "start"
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "なかもり歯科医院",
                        "size": "sm",
                        "align": "center"
                    }
                ]
            }
        }
    )
    return container_obj


def select_menu():
    container_obj = FlexSendMessage(
        alt_text="menu",
        contents={
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "ご来院の理由を選択してください",
                        "margin": "md",
                        "align": "center",
                        "wrap": True
                    }
                ]
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "postback",
                            "label": "定期健診",
                            "data": "check"
                        },
                        "margin": "md"
                    },
                    {
                        "type": "button",
                        "action": {
                            "type": "postback",
                            "label": "治療・その他",
                            "data": "other"
                        },
                        "margin": "md"
                    },
                    {
                        "type": "separator",
                        "margin": "xxl"
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                            "type": "postback",
                            "label": "キャンセル",
                            "data": "cancel"
                        },
                        "margin": "md"
                    }
                ]
            }
        }
    )
    return container_obj
