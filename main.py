import asyncio

async def tcp_echo_client(message):
    reader, writer = await asyncio.open_connection(
        'minechat.dvmn.org', 5000)

    # print(f'Send: {message!r}')
    # writer.write(message.encode())
    # await writer.drain()
    
    while True:
        data = await reader.readuntil(b'\n')
        print(data.decode())

    # print('Close the connection')
    # writer.close()
    # await writer.wait_closed()

asyncio.run(tcp_echo_client('Hello World!'))