import asyncio
import argparse
import sys
import logging
import json
import os
import aiofiles


TOKEN_KEY = "token.txt"


class MyLogsHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        print(log_entry)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(MyLogsHandler())


def create_parcer():
    parser = argparse.ArgumentParser(
                 prog='write_minechat',
                 description='Скрипт отправки сообщения в чат',
             )    
    parser.add_argument(
        '--host',
        type=str,
        default='minechat.dvmn.org',
        help="Имя хоста",
    )
    parser.add_argument(
        '-n',
        '--nickname',
        type=str,
        default='',
        help="Псевдоним пользователя",
    )
    parser.add_argument(
        '-p',
        '--port',
        type=int,
        default=5050,
        help="Номер порта",
    )
    parser.add_argument(
        '-t',
        '--token',
        type=str,
        default="",
        help="Уникальный токен пользователя",
    )
    parser.add_argument(
        '-m',
        '--message',
        required=True,
        type=str,
        help="Сообщение",
    )
    
    return parser.parse_args()


async def register(TOKEN_KEY, host, port, nickname):
    reader, writer = await asyncio.open_connection(
        host, port)

    data = await reader.readuntil(b'\n')
    logger.debug(f'DEBUG:Received: {data.decode()!r}')

    writer.write("\n".encode())
    await writer.drain()
    logger.debug('DEBUG:Send: ')

    data = await reader.readuntil(b'\n')
    logger.debug(f'DEBUG:Received: {data.decode()!r}')
    
    writer.write(f"{nickname}\n".encode())
    logger.debug(f'DEBUG:Send: {nickname!r}')

    data = await reader.readuntil(b'\n')
    data = json.loads(data.decode())
    logger.debug(f'DEBUG:Received: {data}')

    async with aiofiles.open(TOKEN_KEY, "w") as file:
        await file.write(data.get("account_hash"))


async def authorise(host, port, token):
    reader, writer = await asyncio.open_connection(
        host, port)

    data = await reader.readuntil(b'\n')
    logger.debug(f'DEBUG:Received: {data.decode()!r}')

    writer.write(f"{token}\n".encode())
    await writer.drain()
    logger.debug(f'DEBUG:Send: {token!r}')

    data = await reader.readuntil(b'\n')
    data = json.loads(data.decode())

    if not data:
        writer.close()
        await writer.wait_closed()
        return None

    logger.debug(f'DEBUG:Received: {data}')

    data = await reader.readuntil(b'\n')
    logger.debug(f'DEBUG:Received: {data.decode()!r}')

    return writer


async def submit_message(writer, message):
    writer.write(f"{message}\n\n".encode())
    await writer.drain()
    logger.debug(f'DEBUG:Send: {message!r}')


async def main():
    args = create_parcer()
    token = args.token
    if not os.path.exists(TOKEN_KEY) and not token:
        nickname = args.nickname.replace("\n", " ")
        await register(TOKEN_KEY, args.host, args.port, nickname)
    
    if not token:
        async with aiofiles.open(TOKEN_KEY, "r", encoding="utf-8") as file:
            token = await file.read()
    
    writer = await authorise(args.host, args.port, token)
    if not writer:
        logger.info("Неизвестный токен. Проверьте его или зарегистрируйте заново.")
        return

    message = args.message.replace("\n", " ")
    await submit_message(writer, message)

    writer.close()
    await writer.wait_closed()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
