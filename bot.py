"""
discordbotの応答に関する関数群
"""

import discord
import os
import traceback
from db import record_urls
from db import smembers
from db import set_values
from db import delete
from db import get_intersection
from utils import response

client = discord.Client()
developer = discord.User(id='314387921757143040')


@client.event
async def on_ready():
    await send2developer(f'Logged on as {client.user.name}!')


@client.event
async def on_message(message):
    try:
        if message.author == developer:
            for data in await parsemsg(message):
                await client.send_message(message.channel, data)
    except Exception:
        await send2developer(traceback.format_exc())


async def send2developer(text):
    """ 開発者にDMを送る """
    await client.send_message(developer, text)


async def parsemsg(message):
    """ メッセージのコマンド種と引数を解析 """
    args = message.content.split()
    count = len(args)
    if count == 1:
        if args[0] == '/clear':
            await clear(message)
        if args[0] == '/eatup':
            await eatup(message)
    if count == 2:
        if args[0] == '/tagging':
            key = args[1]
            await tagging(message, key)
    if count >= 2:
        if args[0] == '/get':
            keys = args[1:]
            data = sorted(get_intersection(keys))
            return data if data else response(404)
        if args[0] == '/del':
            delete(args[1:])
    if count > 2:
        if args[0] == '/set':
            key = args[1]
            values = args[2:]
            set_values(key, values)
    return []


async def clear(message):
    """ チャンネル内メッセージの全削除 """
    while True:
        logs = [log async for log in client.logs_from(message.channel)]
        if len(logs) > 2:
            await client.delete_messages(logs)
        else:
            return


async def eatup(message):
    """ チャンネル内メッセージの情報記録と削除 """
    async for log in client.logs_from(message.channel):
        urls = record_urls(log.content)
        for url in urls:
            await send2developer(f'RECORDED {url}')
        await client.delete_message(log)


async def tagging(message, key):
    """ インタラクティブにタグ付けする """
    for url in smembers(key):
        elements = ' '.join([f'`{i}`' for i in smembers(url)])
        await client.send_message(message.channel, f'{url}\n{elements}')
        while True:
            message = await client.wait_for_message(
                timeout=60,
                author=message.author)
            if message.content == 'p':
                break
            if message.content == 'e':
                return
            set_values(url, message.content.split())
    await client.send_message(message.channel, 'データがありません')


client.run(os.getenv('DISCORD_BOT_TOKEN'))
