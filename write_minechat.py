import asyncio
import argparse
import sys
import logging
import json
import os
import aiofiles


class MyLogsHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        print(log_entry)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(MyLogsHandler())


def create_parcer():
    parser = argparse.ArgumentParser()
    
    parser.add_argument('--host', type=str, default='minechat.dvmn.org')
    parser.add_argument('--nickname', type=str, default='')
    parser.add_argument('--port', type=int, default=5050)
    parser.add_argument('--key', type=str, default="token.txt")
    parser.add_argument('--message', type=str, default="Hello world")
    
    return parser.parse_args()


async def register(key, host, port, nickname):
    reader, writer = await asyncio.open_connection(
        host, port)

    data = await reader.readuntil(b'\n')
    logger.debug(f'DEBUG:Received: {data.decode()!r}')

    writer.write(f"\n".encode())
    await writer.drain()
    logger.debug(f'DEBUG:Send: ')

    data = await reader.readuntil(b'\n')
    logger.debug(f'DEBUG:Received: {data.decode()!r}')
    
    writer.write(f"{nickname}\n".encode())
    logger.debug(f'DEBUG:Send: {nickname!r}')

    data = await reader.readuntil(b'\n')
    data = json.loads(data.decode())
    logger.debug(f'DEBUG:Received: {data}')

    async with aiofiles.open(key, "w") as file:
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


# async def tcp_echo_client(key, host, port, token, nickname="", registration=False):
#     message = "123"
#     reader, writer = await asyncio.open_connection(
#         host, port)

#     data = await reader.readuntil(b'\n')
#     logger.debug(f'DEBUG:Received: {data.decode()!r}')

#     writer.write(f"{token}\n".encode())
#     await writer.drain()
#     logger.debug(f'DEBUG:Send: {token!r}')

#     if registration:
#         data = await reader.readuntil(b'\n')
#         logger.debug(f'DEBUG:Received: {data.decode()!r}')
#         writer.write(f"{nickname}\n".encode())
#         logger.debug(f'DEBUG:Send: {nickname!r}')

#     data = await reader.readuntil(b'\n')
#     data = json.loads(data.decode())
    
#     if not data:
#         print("Неизвестный токен. Проверьте его или зарегистрируйте заново.")
#         return

#     if registration:
#         logger.debug(f'DEBUG:Received: {data}')
#         async with aiofiles.open(key, "w") as file:
#             await file.write(data.get("account_hash"))
#         return

#     logger.debug(f'DEBUG:Received: {data}')

#     data = await reader.readuntil(b'\n')
#     logger.debug(f'DEBUG:Received: {data.decode()!r}')

#     writer.write(f"{message}\n\n".encode())
#     await writer.drain()
#     logger.debug(f'DEBUG:Send: {message!r}')

#     writer.close()
#     await writer.wait_closed()


async def main():
    args = create_parcer()
    if not os.path.exists(args.key):
        await register(args.key, args.host, args.port, args.nickname)
    
    async with aiofiles.open(args.key, "r", encoding="utf-8") as file:
        token = await file.read()
    
    writer = await authorise(args.host, args.port, token)
    if not writer:
        print("Неизвестный токен. Проверьте его или зарегистрируйте заново.")
        return

    await submit_message(writer, args.message)

    writer.close()
    await writer.wait_closed()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
