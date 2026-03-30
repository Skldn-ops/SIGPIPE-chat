import asyncio
import json
import getpass

class Message:
    def __init__(self, sender="0", receiver="0", text="0"):
        self.sender = sender
        self.receiver = receiver
        self.text = text
    
    def to_dict(self):
        return {
            'sender': self.sender,
            'receiver': self.receiver,
            'text': self.text
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(data.get('sender', '0'), 
                  data.get('receiver', '0'), 
                  data.get('text', '0'))
    

class Chat:
    def __init__(self):
        self.chat_with = "@0"
        self.username = "__NO_NAME__"

    async def chat_client(self):
        SERVER_IP = '192.168.1.117'
        SERVER_PORT = 8888

        messages_queue = []

            
        async def auth(reader, writer):
            while True:    
                data = await reader.read(1024)
                ans = data.decode()
                print(ans)
                
                while(ans != '/reg' and ans != '/in'):
                    ans = await asyncio.to_thread(input, "> ")
                    print(ans)
                writer.write(ans.encode())
                await writer.drain()

                data = await reader.read(1024)
                ans = data.decode()
                print(ans)

                while self.username[0] != '@':
                    self.username = await asyncio.to_thread(input, "> ")
                writer.write(self.username.encode())
                await writer.drain()

                data = await reader.read(1024)
                ans = data.decode()
                print(ans)

                attempts = 5
                while(ans[:7] != "success"):
                    attempts-=1
                    if attempts < 0:
                        return True
                
                    ans = await asyncio.to_thread(getpass.getpass, "> ")
                    writer.write(ans.encode())
                    await writer.drain()
                    
                    data = await reader.read(1024)
                    ans = data.decode()
                    print(ans)

                return False




        async def print_from_queue():
            messages_queue.reverse()
            for i in range(len(messages_queue) - 1, -1, -1):
                temp = messages_queue[i]
                if temp.sender == self.chat_with:
                    print(f"\n[{temp.sender} -> {temp.receiver}]: {temp.text}")
                    del messages_queue[i]
            messages_queue.reverse()

            

        async def receive_messages(self):
            try:
                while True:
                    received_data = await reader.read(1024)
                    if not received_data:
                        print("Сервер отключился")
                        break
                    

                    try:
                        data = json.loads(received_data.decode())
                        message = Message.from_dict(data)
                        if message.sender == self.chat_with or message.sender == self.username:
                            print(f"\n[{message.sender} -> {message.receiver}]: {message.text}")
                            print(f"\n[{self.username} -> {self.chat_with}]> ", end="", flush=True)
                        else:
                            messages_queue.append(message)    


                    except json.JSONDecodeError:
                        # Если это не JSON, выводим как обычный текст
                        print(f"\n{received_data.decode().strip()}")
                        print("> ", end="", flush=True)
                    
                    # print("> ", end="", flush=True)

            except asyncio.CancelledError:
                pass
            except Exception as e:
                print(f"Ошибка приема: {e}")
        
        async def send_messages(self):
            try:
                while True:
                    if self.chat_with == "@0":
                        user_input = await asyncio.to_thread(input, "> ")
                    else:
                        user_input = await asyncio.to_thread(input, f"\n[{self.username} -> {self.chat_with}]> ")
                    
                    if user_input.lower() == '/exit':
                        break
                    

                    if user_input.lower()[0] == '@':
                        self.chat_with = user_input.lower()
                        await print_from_queue()
                    elif(self.chat_with != ''):
                        msg = Message(sender=self.username, receiver = self.chat_with, text = user_input)
                        writer.write(json.dumps(msg.to_dict()).encode())
                        await writer.drain()

            except asyncio.CancelledError:
                pass
            finally:
                writer.close()
                await writer.wait_closed()
        

        reader, writer = await asyncio.open_connection(SERVER_IP, SERVER_PORT)
        print("Подключено к чат-серверу")
        while(await auth(reader, writer)):
            print("Failed to authenticate\n")
            return
            #reader, writer = await asyncio.open_connection(SERVER_IP, SERVER_PORT)

        receive_task = asyncio.create_task(receive_messages(self))
        send_task = asyncio.create_task(send_messages(self))
        
        done, pending = await asyncio.wait([receive_task, send_task], 
                                        return_when=asyncio.FIRST_COMPLETED)
        
        for task in pending:
            task.cancel()

try:
    starter = Chat()
    asyncio.run(Chat.chat_client(starter))
except KeyboardInterrupt:
    print("\nВыход из чата")