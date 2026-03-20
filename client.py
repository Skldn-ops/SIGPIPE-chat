import asyncio
import json

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

    async def chat_client(self):
        SERVER_IP = '192.168.1.110'
        SERVER_PORT = 8888

        messages_queue = []

        
        reader, writer = await asyncio.open_connection(SERVER_IP, SERVER_PORT)
        print("Подключено к чат-серверу")
            

        async def print_from_queue():
            messages_queue.reverse()
            for i in range(len(messages_queue) - 1, -1, -1):
                temp = messages_queue[i]
                if str(temp.sender) == str(self.chat_with):
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
                        if str(message.sender) == str(self.chat_with):
                            #await print_from_queue()
                            print(f"\n[{message.sender} -> {message.receiver}]: {message.text}")
                            print("> ", end="", flush=True)
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
                    user_input = await asyncio.to_thread(input, "> ")
                    
                    if user_input.lower() == '/exit':
                        break
                    

                    #parts = user_input.split(' ', 1)
                    if user_input.lower()[0] == '@':
                        self.chat_with = user_input.lower()[1:]
                        await print_from_queue()
                    elif(self.chat_with != ''):
                        msg = Message(sender="me", receiver = int(self.chat_with), text = user_input)
                        writer.write(json.dumps(msg.to_dict()).encode())
                        await writer.drain()

            except asyncio.CancelledError:
                pass
            finally:
                writer.close()
                await writer.wait_closed()
        
        #define_reciever_task = asyncio.create_task(find_reciever())
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