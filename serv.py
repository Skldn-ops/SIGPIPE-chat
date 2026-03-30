import asyncio
import json
# from typing import List
# from collections import deque
import sql_tab

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
        self.client_counter = 0
        self.Tab = sql_tab.DB_manager()
        self.id_descr = {}  # (client_id, connection_id) -> (reader, writer)
        self.message_queues = {}  # (client_id, connection_id) -> Queue
        self.user_connections = {}  # client_id -> set of connection_ids


    async def auth_func(self, reader, writer):
        while True:
                hello_mes = "type /reg or /in"
                writer.write(hello_mes.encode())
                await writer.drain()
                data = await reader.read(1024)

                command = data.decode()
                if command != '/reg' and command != "/in":
                    writer.close()
                    await writer.wait_closed()

                if command == '/reg':
                    
                    reg_mes = "username(starts with '@'): "
                    writer.write(reg_mes.encode())
                    await writer.drain()
                    data = await reader.read(1024)
                    client_name = data.decode()
                    if client_name[0] != '@' or client_name == "@0":
                        writer.close()
                        await writer.wait_closed()
                    
                    reg_mes = "password: "
                    writer.write(reg_mes.encode())
                    await writer.drain()
                    data = await reader.read(1024)
                    client_passwd = data.decode()
                    if not client_passwd:
                        writer.close()
                        await writer.wait_closed()
                    
                    client_id = self.Tab.register_user(client_name, client_passwd)
                    
                    reg_mes = "success register\n"
                    writer.write(reg_mes.encode())
                    await writer.drain()
                    return client_id
                
                if command == '/in':
                    reg_mes = "username: "
                    writer.write(reg_mes.encode())
                    await writer.drain()
                    data = await reader.read(1024)
                    client_name = data.decode()
                    if not client_name or client_name[0] != '@' or client_name == "@0" or not(self.Tab.get_id_by_username(client_name)):
                        writer.close()
                        await writer.wait_closed()

                    reg_mes = "password: "
                    writer.write(reg_mes.encode())
                    await writer.drain()

                    client_id = None
                    attempts = 5
                    while client_id is None:
                        attempts-=1
                        if attempts < 0:
                            writer.close()
                            await writer.wait_closed()
                            break

                        data = await reader.read(1024)
                        client_passwd = data.decode()

                        client_id = self.Tab.authenticate_user(client_name, client_passwd)
                        if client_id is None:
                            reg_mes = "Wrong password\n"
                            writer.write(reg_mes.encode())
                            await writer.drain()
                            

                    reg_mes = "success auth\n"
                    writer.write(reg_mes.encode())
                    await writer.drain()
                    return client_id

                    
                    


        
    
    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info('peername')

        try:
            client_id = await self.auth_func(reader, writer)
        except ConnectionResetError:
            print("Клиент ввел неверный пароль")
            return
            


        client_name = self.Tab.get_username_by_id(client_id)
        print(f"Клиент {client_id} {client_name} подключился и авторизовался: {addr}")

        connection_id = self.client_counter
        self.client_counter += 1

        self.id_descr[(client_id, connection_id)] = (reader, writer)
        self.message_queues[(client_id, connection_id)] = asyncio.Queue()
        
        if client_id not in self.user_connections:
            self.user_connections[client_id] = set()
        self.user_connections[client_id].add(connection_id)
        
        # Отправляем клиенту его ID как объект Message
        welcome_msg = Message(sender="@0", receiver=client_name, 
                             text=f"Ваш ID: {client_id}. Ваше имя: {client_name}")
        await self.server_answers(client_id, welcome_msg)

        
        try:
            read_task = asyncio.create_task(self.read_from_client(client_id, connection_id, reader))
            send_task = asyncio.create_task(self.send_to_client(client_id, connection_id, writer))
            
            done, pending = await asyncio.wait([read_task, send_task], 
                                              return_when=asyncio.FIRST_COMPLETED)
            
            for task in pending:
                task.cancel()
                
        except asyncio.CancelledError:
            print(f"Клиент {client_id} прерван")
        finally:
            # Удаляем только это подключение
            self.remove_connection(client_id, connection_id)
            writer.close()
            await writer.wait_closed()
            print(f"Клиент {client_id} (подключение {connection_id}) отключен")
    
    def remove_connection(self, client_id, connection_id):
        """Удаляет конкретное подключение пользователя"""
        if (client_id, connection_id) in self.id_descr:
            del self.id_descr[(client_id, connection_id)]
        if (client_id, connection_id) in self.message_queues:
            del self.message_queues[(client_id, connection_id)]
        
        if client_id in self.user_connections:
            self.user_connections[client_id].discard(connection_id)
            if not self.user_connections[client_id]:
                del self.user_connections[client_id]    
    





    async def read_from_client(self, client_id, connection_id, reader):
        try:
            while True:
                data = await reader.read(1024)
                if not data:
                    break
                
                # Пытаемся распарсить как JSON (объект Message)
                try:
                    msg_data = json.loads(data.decode())
                    received_msg = Message.from_dict(msg_data)
                    print(f"Получен объект Message от {received_msg.sender}: {received_msg.text}")
                    
                    await self.send_to_friend(received_msg, connection_id)
                    
                except(ConnectionError, BrokenPipeError, ConnectionResetError) as e:
                    print(f"Соединение с клиентом {client_id} разорвано: {e}")
                    break 
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    print(f"Ошибка при чтении от клиента {client_id}: {e}")
                    break
                
        except asyncio.CancelledError:
            print(f"Чтение от клиента {client_id} отменено")
            raise
    
    async def send_to_client(self, client_id, connection_id, writer):
        try:
            while True:
                try:
                    message_obj = await self.message_queues[(client_id, connection_id)].get()
                    
                    json_data = json.dumps(message_obj.to_dict())
                    writer.write(json_data.encode())
                    await writer.drain()
                
                except(ConnectionError, BrokenPipeError, ConnectionResetError) as e:
                    print(f"Соединение с клиентом {client_id} разорвано при отправке: {e}")
                    break
                except asyncio.CancelledError:
                    raise               
        
        except asyncio.CancelledError:
            print(f"Отправка клиенту {client_id} ( подкл {connection_id}) отменена")
            raise
    


    async def server_answers(self, client_id, message_obj):

        if client_id in self.message_queues:
            await self.message_queues[client_id].put(message_obj)
            return True
        return False
    


    
    async def send_to_friend(self, message_obj, cur_connection_id):
        friend_id = self.Tab.get_id_by_username(message_obj.receiver)
        sender_id = self.Tab.get_id_by_username(message_obj.sender)
        sent = False
        if friend_id in self.user_connections:
            for connection_id in self.user_connections[friend_id]:
                if(friend_id, connection_id) in self.message_queues:
                    await self.message_queues[(friend_id, connection_id)].put(message_obj)
                    sent = True
        
        if sender_id in self.user_connections:
            for connection_id in self.user_connections[sender_id]:
                if connection_id != cur_connection_id:
                    if (sender_id, connection_id) in self.message_queues:
                        await self.message_queues[(sender_id, connection_id)].put(message_obj)
        return sent
    # async def broadcast(self, message_obj, exclude_id=None):
    #     """Отправка сообщения всем клиентам"""
    #     print(f"Broadcast: {message_obj.text}")
    #     for client_id in self.id_descr:
    #         if exclude_id is None or client_id != exclude_id:
    #             if client_id in self.message_queues:
    #                 await self.message_queues[client_id].put(message_obj)
    
    # def remove_client(self, client_id):
    #     if client_id in self.id_descr:
    #         del self.id_descr[client_id]
    #     if client_id in self.message_queues:
    #         del self.message_queues[client_id]
        
    #     if self.id_descr:
    #         asyncio.create_task(
    #             self.broadcast(Message(sender="0", receiver="all", 
    #                                   text=f"Клиент {client_id} покинул чат"))
    #         )

async def main():
    server = await asyncio.start_server(ChatServer().handle_client, '192.168.1.117', 8888)
    
    addr = server.sockets[0].getsockname()
    print(f'Чат-сервер запущен на {addr}')
    
    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    asyncio.run(main())