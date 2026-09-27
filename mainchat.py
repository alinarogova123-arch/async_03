import asyncio
import gui
import time
import sys
import argparse
import socket
import datetime
import json
import aiofiles
import os
import socket
import logging
from tkinter import messagebox
from anyio import create_task_group


TOKEN_KEY = "token.txt"

RECONNECT_TIMEOUT = 3

PING_TIMEOUT = 2

SHORT_RECONNECT_DELAY = 1

LONG_RECONNECT_DELAY = 10


class MyLogsHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        print(log_entry)

watchdog_logger = logging.getLogger(__name__)
watchdog_logger.setLevel(logging.DEBUG)
watchdog_logger.addHandler(MyLogsHandler())


def create_parcer():
    parser = argparse.ArgumentParser(
                 prog='minechat',
                 description='Запуск интерфейса чата',
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
        '-lp',
        '--listen_port',
        type=int,
        default=5000,
        help="Номер порта для чтения чата",
    )
    parser.add_argument(
        '-sp',
        '--sending_port',
        type=int,
        default=5050,
        help="Номер порта для отправки сообщений",
    )
    parser.add_argument(
        '--filepath',
        type=str,
        default="history.txt",
        help="История сообщений",
    )
    
    return parser.parse_args()


async def get_connection(host, port):
    attempt = 0
    while True:
        try:
            reader, writer = await asyncio.open_connection(
                host, port)       
        except socket.gaierror:
            attempt =+ 1
            if attempt > 10:
                await asyncio.sleep(LONG_RECONNECT_DELAY)
            else:
                await asyncio.sleep(SHORT_RECONNECT_DELAY)
            continue
        else:
            attempt = 0
            break

    return reader, writer


async def send_msgs(
    host,
    port,
    token,
    status_updates_queue,
    sending_queue,
    watchdog_queue
):
    status_updates_queue.put_nowait(gui.SendingConnectionStateChanged.INITIATED)
    reader, writer = await get_connection(host, port)

    data = await reader.readuntil(b'\n')
    
    writer.write(f"{token}\n".encode())
    await writer.drain()
    
    account_info = await reader.readuntil(b'\n')
    account_info = json.loads(account_info.decode())
    watchdog_queue.put_nowait("Prompt before auth")
    
    if not account_info:
        messagebox.showinfo(
            "Неверный токен",
            "Проверьте токен или зарегистрируйтесь заново."
        )
        writer.close()
        await writer.wait_closed()
        return

    watchdog_queue.put_nowait("Authorization done")    
    event = gui.NicknameReceived(account_info.get("nickname"))
    status_updates_queue.put_nowait(event)
    status_updates_queue.put_nowait(gui.SendingConnectionStateChanged.ESTABLISHED)

    while True:
        try:
            async with asyncio.timeout(PING_TIMEOUT) as cm:
                msg = await sending_queue.get()
                writer.write(f"{msg}\n\n".encode())
                await writer.drain()
                watchdog_queue.put_nowait("Message sent")
        except TimeoutError:
            if cm.expired:
                writer.write(f"\n".encode())
                await writer.drain()
                watchdog_queue.put_nowait("Ping message sent")
            else:
                raise ConnectionResetError

        data = await reader.readuntil(b'\n')
        watchdog_queue.put_nowait("Pong message recived")


async def read_msgs(
    host,
    port,
    messages_queue,
    history_queue,
    history,
    status_updates_queue,
    watchdog_queue
):
    if history:
        for message in history.split("\n"):
            messages_queue.put_nowait(message)

    status_updates_queue.put_nowait(gui.ReadConnectionStateChanged.INITIATED)
    reader, writer = await get_connection(host, port)
    status_updates_queue.put_nowait(gui.ReadConnectionStateChanged.ESTABLISHED)

    while True:
        msg = await reader.readuntil(b'\n')
        if not msg:
            break
        watchdog_queue.put_nowait("New message in chat")
        messages_queue.put_nowait(msg.decode().strip())
        history_queue.put_nowait(msg.decode().strip())
    
    writer.close()
    await writer.wait_closed()


async def watch_for_connection(watchdog_queue):
    while True:
        try:
            async with asyncio.timeout(RECONNECT_TIMEOUT) as cm:
                msg = await watchdog_queue.get()
        except TimeoutError:
            if cm.expired:
                watchdog_logger.debug(f"[{int(time.time())}] 3s timeout is elapsed")
                raise ConnectionResetError
            else:
                watchdog_logger.debug(f"[{int(time.time())}] The 3-second timeout has not expired")
                raise ConnectionResetError
        else:
            watchdog_logger.debug(f"[{int(time.time())}] Connection is alive. {msg}")


async def handle_connection(
    watchdog_queue,
    sending_queue,
    messages_queue,
    history_queue,
    status_updates_queue,
    token,
    history
):
    args = create_parcer()
    while True:
        try:
            async with create_task_group() as tg:
                tg.start_soon(
                    watch_for_connection,
                    watchdog_queue
                )
                tg.start_soon(
                    send_msgs,
                    args.host,
                    args.sending_port,
                    token,
                    status_updates_queue,
                    sending_queue,
                    watchdog_queue
                )
                tg.start_soon(
                    read_msgs,
                    args.host,
                    args.listen_port,
                    messages_queue,
                    history_queue,
                    history,
                    status_updates_queue,
                    watchdog_queue
                )
        except* ConnectionResetError:
            status_updates_queue.put_nowait(gui.ReadConnectionStateChanged.CLOSED)
            status_updates_queue.put_nowait(gui.SendingConnectionStateChanged.CLOSED)


async def save_messages(filepath, history_queue):
    while True:
        msg = await history_queue.get()
        async with aiofiles.open(filepath, "a") as file:
            await file.write(f"{msg}\n")


async def main():
    watchdog_queue = asyncio.Queue()
    history_queue = asyncio.Queue()
    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()
    
    args = create_parcer()

    if os.path.exists(args.filepath):
        async with aiofiles.open(args.filepath, "r") as file:
            history = await file.read()
    else:
        history = None

    if not os.path.exists(TOKEN_KEY):
        messagebox.showinfo(
            "Токен не найден",
            "Запустите registration.py для регистрации и получения токена"
        )
        sys.exit(0)

    async with aiofiles.open(TOKEN_KEY, "r") as file:
        token = await file.read()
    
    try:
        async with create_task_group() as tg:
            tg.start_soon(
                handle_connection,
                watchdog_queue,
                sending_queue,
                messages_queue,
                history_queue,
                status_updates_queue,
                token,
                history
            )
            tg.start_soon(
                save_messages,
                args.filepath,
                history_queue
            )
            tg.start_soon(
                gui.draw,
                messages_queue,
                sending_queue,
                status_updates_queue
            )
    except* gui.TkAppClosed:
        raise gui.TkAppClosed()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, gui.TkAppClosed):
        sys.exit(0)
