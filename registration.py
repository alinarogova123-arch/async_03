import tkinter as tk
import asyncio
import argparse
import sys
import logging
import json
import os
import aiofiles


TOKEN_KEY = "token.txt"

HOST = "minechat.dvmn.org"

PORT = 5050


async def registration_request(nickname):
    reader, writer = await asyncio.open_connection(
        HOST, PORT)
    data = await reader.readuntil(b'\n')
    writer.write("\n".encode())
    await writer.drain()
    data = await reader.readuntil(b'\n')    
    writer.write(f"{nickname}\n".encode())
    account_info = await reader.readuntil(b'\n')
    account_info = json.loads(account_info.decode())
    async with aiofiles.open(TOKEN_KEY, "w") as file:
        await file.write(account_info.get("account_hash"))


def register(ent, lab):
    nickname = ent.get()
    nickname = nickname.replace("\n", "_")
    nickname = nickname.replace(" ", "_")
    asyncio.run(registration_request(nickname))
    ent.delete(0, tk.END)
    lab['text'] = "Вы успешно зарегистрированы, ваш токен сохранён"


def main():
	root = tk.Tk()	
	root.title('Регистрация Майнкрафтера')	
	ent = tk.Entry(root, width=100)
	but = tk.Button(root, text='Зарегистрироваться')
	lab = tk.Label(root, width=100)	
	lab['text'] = "Введите ваш никнейм и нажмите кнопку"		
	but["command"] = lambda: register(ent, lab)
	ent.pack()
	but.pack()
	lab.pack()
	root.mainloop()


if __name__ == '__main__':
	main()
