# coding: utf-8

import asyncio
from datetime import datetime, timedelta
from contextlib import closing
import discord
import psycopg2
import os

DELTA_JST = timedelta(hours=9)
TOKEN = 'NjY1NTA3ODc2NjIxNTE2ODAw.XhnFhA.Nvbh4jFERg-f1CqD0WGUaNb3BxY'
client = discord.Client()
GUILD_ID = 665506952591179781
dsn = os.environ('DATABASE_URL')


# message イベント
@client.event
async def on_message(message):
    # Bot は無視する
    if message.author.bot:
        pass

    # ログを更新する
    else:
        user_id = message.author.id
        time = utc_to_jst(message.created_at)
        msg_log = (user_id, time)
        write(msg_log)

# ---commands---
    # activelog を表示する
    if message.content.startswith('.activelog'):
        await message.channel.send(read_all())
    # 本人の前回ログからの経過秒数を表示する
    if message.content.startswith('.term'):
        now = datetime.utcnow() + DELTA_JST
        for row in read_all():
            term = now - str_to_datetime(row[1])
            await message.channel.send(term.total_seconds())
# --------------


# join イベント
@client.event
async def on_member_join(member):
    # Bot は無視する
    if member.bot:
        pass

    # ログを更新する
    else:
        user_id = member.id
        time = member.joined_at
        msg_log = (user_id, time)
        write(msg_log)


# ready イベント
@client.event
async def on_ready():
    await kicker()


# 一定時間ごとに、一定期間ログが更新されなかったユーザーをキックする
async def kicker():
    while True:
        # 現在時刻を取得する
        now = datetime.utcnow() + DELTA_JST
        # データベースを参照する
        for row in read_all():
            # 非アクティブ期間を求める
            term = now - str_to_datetime(row[1])
            if term.days > 5:
                target = get_member_profile(row[0])
                # ターゲットをキックし、データベースから消去する
                try:
                    await target.kick()
                    print('Kicked ' + target.name)
                    delete(row[0])
                # ターゲットをキックできなかったとき、エラーメッセージを出力する
                except (discord.errors.Forbidden, AttributeError) as error_content:
                    try:
                        print('Failed to kick ' + target.name + ': ' + str(error_content))
                    except AttributeError as error_content:
                        print('Cannot get Username: ' + str(error_content))
        await asyncio.sleep(43200)


# ID から discord.Member 型のプロフィールを生成する
def get_member_profile(user_id):
    guild = client.get_guild(GUILD_ID)
    return guild.get_member(user_id)


# UTC 時間を JST 時間に変換する
def utc_to_jst(timestamp_utc):
    timestamp_jst = timestamp_utc + DELTA_JST
    return timestamp_jst


# string 型を datetime 型に変換する
def str_to_datetime(str_time):
    datetime_time = datetime.strptime(str_time, '%Y-%m-%d %H:%M:%S.%f')
    return datetime_time


# レコードを書き込む
def write(msg_log):
    with closing(psycopg2.connect(dsn)) as conn:
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS log (id PRIMARY KEY, time)')
        c.execute('INSERT OR REPLACE INTO log VALUES (?, ?)', msg_log)
        conn.commit()


# レコードを読み込む
def read_all():
    with closing(psycopg2.connect(dsn)) as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM log')
        return c.fetchall()


# レコードを削除する
def delete(user_id):
    with closing(psycopg2.connect(dsn)) as conn:
        c = conn.cursor()
        c.execute('DELETE FROM log WHERE id=?', (user_id, ))
        conn.commit()


client.run(TOKEN)

