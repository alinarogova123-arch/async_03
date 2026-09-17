import asyncio
import argparse
import sys


def create_parcer():
    parser = argparse.ArgumentParser()
    
    parser.add_argument('--host', type=str, default='minechat.dvmn.org')
    parser.add_argument('--port', type=int, default=5050)
    parser.add_argument('--token', type=str, default="")
    
    return parser.parse_args()


async def tcp_echo_client(host, port, token):
    message = "123"
    reader, writer = await asyncio.open_connection(
        host, port)

    # data = await reader.readuntil(b'\n')
    # print(f'Received: {data.decode()!r}')

    writer.write(f"{token}\n".encode())
    await writer.drain()
    print(f'Send: {token!r}')

    # data = await reader.readuntil(b'\n')
    # print(f'Received: {data.decode()!r}')
    # data = await reader.readuntil(b'\n')
    # print(f'Received: {data.decode()!r}')

    writer.write(f"{message}\n\n".encode())
    await writer.drain()
    print(f'Send: {message!r}')

    writer.close()
    await writer.wait_closed()


async def main():
    args = create_parcer()
    await tcp_echo_client(args.host, args.port, args.token)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)

