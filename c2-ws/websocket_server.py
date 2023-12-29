# C2 Cloud
#
# Author: Arun Govindasamy

import asyncio
import websockets
import redis
import yaml

class WebSocketServer:
    def __init__(self):
        self.clients = set()
        with open('config.yaml') as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        self.clients_path = {}
        self.redis_host = config["redis"]["hostname"]
        self.redis_port = config["redis"]["port"]
        self.redis_session_channel = config["redis"]["channel_session"]
        self.redis_payload_channel = config["redis"]["channel_payload"]
        self.websocket_host = config["websocket"]["hostname"]
        self.websocket_port = config["websocket"]["port"]
        self.redis_session_client = redis.StrictRedis(host=self.redis_host, port=self.redis_port, db=0)
        self.redis_payload_client = redis.StrictRedis(host=self.redis_host, port=self.redis_port, db=0)
        self.session_pubsub = self.redis_session_client.pubsub()
        self.payload_pubsub = self.redis_payload_client.pubsub()
        self.session_pubsub.subscribe(self.redis_session_channel)
        self.payload_pubsub.subscribe(self.redis_payload_channel)

    async def subscriber(self, websocket, pubsub, path):
        print(f"subscriber")
        while True:
            try:
                messages = pubsub.get_message()
                if messages and messages['type'] == 'message':
                    data = messages['data'].decode('utf-8')
                    print(f"redis_subscriber data: {data}")
                    await self.broadcast(websocket, data, path)
            except Exception as e:
                print(f"subscriber: websocket close {e}")
                return

    async def connect(self, websocket, path):
        self.clients.add(websocket)
        if path not in self.clients_path:
            self.clients_path[path] = set()
        self.clients_path[path].add(websocket)
        print(f"Client connected: websocket: {websocket} path:{path}")
        # Start the session_subscriber 
        if path == "/sessions" or path == "/payload":
            loop = asyncio.get_event_loop()
            # Set the pubsub value based on the path 
            if path == "/sessions":
                pubsub = self.session_pubsub
            else:
                pubsub = self.payload_pubsub
            loop.run_in_executor(None, self.run_subscriber, websocket, pubsub, path)

        while True:
            try:
                await websocket.recv()
            except websockets.exceptions.ConnectionClosedOK:
                print(f"Client disconnected: websocket close {websocket}")
                await websocket.close()
                self.clients.remove(websocket)
                self.clients_path[path].remove(websocket)
                return

    def run_subscriber(self, websocket, pubsub, path):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.subscriber(websocket, pubsub, path))

    # broadcast based on the path /sessions /payload
    async def broadcast(self, sender, message, path):
        if path in self.clients_path:
            for client in self.clients_path[path]:
                print(f"broadcast - path: {path} client: {client} sender: {sender}")
                # await asyncio.gather(*[client.send(message) for client in self.clients])
                try:
                    await client.send(message)
                except Exception as e:
                    print(f"Error sending message to client: {e}")

# Initialize and run the WebSocketServer
server = WebSocketServer()
start_server = websockets.serve(server.connect, server.websocket_host, server.websocket_port)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()

