import asyncio
import datetime
import aiofiles
import socket
import sys


TIMEOUT = 10


async def tcp_echo_client(message):
    while True:
        try:
            reader, writer = await asyncio.open_connection(
                'minechat.dvmn.org', 5000)
        
        except socket.gaierror:
            await asyncio.sleep(TIMEOUT)
            continue

            now = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
            async with aiofiles.open("test.txt", "a") as file:
                await file.write(f"[{now}] Установлено соединение\n")
            
        try:
            while True:
                data = await asyncio.wait_for(reader.readuntil(b'\n'), timeout=TIMEOUT)
                if not data:
                    break
                now = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
                async with aiofiles.open("test.txt", "a") as file:
                    await file.write(f"[{now}] {data.decode().strip()}")
                print(data.decode())
        
        except TimeoutError:
            if writer:
                writer.close()
                await writer.wait_closed()

try:
    asyncio.run(tcp_echo_client('Hello World!'))
except KeyboardInterrupt:
    sys.exit(0)