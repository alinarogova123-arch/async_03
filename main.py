import asyncio
import datetime
import argparse
import aiofiles
import socket
import sys


TIMEOUT = 10


def create_parcer():
    parser = argparse.ArgumentParser()
    
    parser.add_argument('--host', type=str, default='minechat.dvmn.org')
    parser.add_argument('--port', type=int, default=5000)
    parser.add_argument('--history', type=str, default="chat.txt")
    
    return parser.parse_args()


async def tcp_echo_client(host, port, history):
    while True:
        try:
            reader, writer = await asyncio.open_connection(
                host, port)
        
        except socket.gaierror:
            await asyncio.sleep(TIMEOUT)
            continue

        now = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
        async with aiofiles.open(history, "a") as file:
            await file.write(f"[{now}] !!! Установлено соединение !!!\n")
            
        try:
            while True:
                data = await asyncio.wait_for(reader.readuntil(b'\n'), timeout=TIMEOUT)
                if not data:
                    break
                now = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
                async with aiofiles.open(history, "a") as file:
                    await file.write(f"[{now}] {data.decode()}")
                print(data.decode().strip())
        
        except TimeoutError:
            writer.close()
            await writer.wait_closed()


async def main():
    args = create_parcer()
    await tcp_echo_client(args.host, args.port, args.history)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)