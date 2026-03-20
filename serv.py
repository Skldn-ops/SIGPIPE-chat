import asyncio
import json
from collections import deque

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

class ChatServer:
    def __init__(self):
        self.id_descr = {}
        self.message_queues = {}
        self.client_counter = 0
    
    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info('peername')
        
        self.client_counter += 1
        client_id = self.client_counter
        
        print(f"Клиент {client_id} подключился: {addr}")
        
        self.message_queues[client_id] = asyncio.Queue()
        self.id_descr[client_id] = (reader, writer)
        
        # Отправляем клиенту его ID как объект Message
        welcome_msg = Message(sender="0", receiver=str(client_id), 
                             text=f"Ваш ID: {client_id}. Ожидание второго клиента...")
        await self.server_answers(client_id, welcome_msg)


        
        # await self.broadcast(Message(sender="server", receiver="all", 
        #                             text=f"Клиент {client_id} присоединился к чату"))
        
        # if len(self.id_descr) == 2:
        #     await self.broadcast(Message(sender="server", receiver="all", 
        #                                 text="Оба клиента подключены! Можно начинать общение."))
        
        try:
            read_task = asyncio.create_task(self.read_from_client(client_id, reader))
            send_task = asyncio.create_task(self.send_to_client(client_id, writer))
            
            done, pending = await asyncio.wait([read_task, send_task], 
                                              return_when=asyncio.FIRST_COMPLETED)
            
            for task in pending:
                task.cancel()
                
        except asyncio.CancelledError:
            print(f"Клиент {client_id} прерван")
        finally:
            self.remove_client(client_id)
            writer.close()
            await writer.wait_closed()
            print(f"Клиент {client_id} отключен")
    





    async def read_from_client(self, client_id, reader):
        try:
            while True:
                data = await reader.read(1024)
                if not data:
                    break
                
                # Пытаемся распарсить как JSON (объект Message)
                try:
                    msg_data = json.loads(data.decode())
                    received_msg = Message.from_dict(msg_data)

                    received_msg.sender = str(client_id)

                    print(f"Получен объект Message от {client_id}: {received_msg.text}")
                    
                    await self.send_to_friend(client_id, int(received_msg.receiver), received_msg)
                    
                except json.JSONDecodeError:
                    # Если это не JSON, обрабатываем как старый формат
                    message = data.decode().strip()
                    print(f"Получен текст от клиента {client_id}: {message}")
                    
                    # Пробуем распарсить старый формат "получатель сообщение"
                    parts = message.split(' ', 1)
                    if len(parts) == 2:
                        friend_id, text = parts
                        msg = Message(sender=str(client_id), receiver=friend_id, text=text)
                        await self.send_to_friend(client_id, int(friend_id), msg)
                
        except asyncio.CancelledError:
            print(f"Чтение от клиента {client_id} отменено")
            raise
    
    async def send_to_client(self, client_id, writer):
        try:
            while True:
                message_obj = await self.message_queues[client_id].get()
                
                # Сериализуем объект Message в JSON перед отправкой
                json_data = json.dumps(message_obj.to_dict())
                writer.write(json_data.encode())
                await writer.drain()
                
        except asyncio.CancelledError:
            print(f"Отправка клиенту {client_id} отменена")
            raise
    


    async def server_answers(self, client_id, message_obj):

        if client_id in self.message_queues:
            await self.message_queues[client_id].put(message_obj)
            return True
        return False
    


    
    async def send_to_friend(self, sender_id, friend_id, message_obj):

        if friend_id in self.message_queues:
            await self.message_queues[friend_id].put(message_obj)
            print(f"Сообщение от {sender_id} отправлено клиенту {friend_id}")
            return True
        else:
            print(f"Клиент {friend_id} не найден")
            # Уведомляем отправителя
            error_msg = Message(sender="0", receiver=str(sender_id), 
                               text=f"Клиент {friend_id} не подключен. Сообщение не доставлено.")
            if sender_id in self.message_queues:
                await self.message_queues[sender_id].put(error_msg)
            return False
    
    async def broadcast(self, message_obj, exclude_id=None):
        """Отправка сообщения всем клиентам"""
        print(f"Broadcast: {message_obj.text}")
        for client_id in self.id_descr:
            if exclude_id is None or client_id != exclude_id:
                if client_id in self.message_queues:
                    await self.message_queues[client_id].put(message_obj)
    
    def remove_client(self, client_id):
        if client_id in self.id_descr:
            del self.id_descr[client_id]
        if client_id in self.message_queues:
            del self.message_queues[client_id]
        
        if self.id_descr:
            asyncio.create_task(
                self.broadcast(Message(sender="0", receiver="all", 
                                      text=f"Клиент {client_id} покинул чат"))
            )

async def main():
    server = await asyncio.start_server(ChatServer().handle_client, '192.168.1.110', 8888)
    
    addr = server.sockets[0].getsockname()
    print(f'Чат-сервер запущен на {addr}')
    print('Ожидание подключения двух клиентов...')
    
    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    asyncio.run(main())