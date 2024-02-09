# C2 Cloud
#
# Author: Arun Govindasamy

from distutils import command
from email import message
from unittest import result
import yaml
import time
import json
import string
import requests
import random
import redis
import base64
import threading
import re
from datetime import datetime

class Telegram:
    def __init__(self):
        self.clients = set()
        with open('config.yaml') as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        self.clients_path = {}
        self.redis_host = config["redis"]["hostname"]
        self.redis_port = config["redis"]["port"]
        self.redis_session_channel = config["redis"]["channel_session"]
        self.redis_payload_channel = config["redis"]["channel_payload"]
        self.redis_telegram_channel = config["redis"]["channel_telegram"]
        self.bot_chat_id = config["telegram"]["chat_id"]
        self.bot_name = config["telegram"]["bot_name"]
        self.bot_username = config["telegram"]["bot_username"]
        self.bot_token = config["telegram"]["bot_token"]
        self.redis_client = redis.StrictRedis(host=self.redis_host, port=self.redis_port, decode_responses=True)
        self.redis_session_client = redis.StrictRedis(host=self.redis_host, port=self.redis_port, db=0)
        self.redis_payload_client = redis.StrictRedis(host=self.redis_host, port=self.redis_port, db=0)
        self.redis_telegram_client = redis.StrictRedis(host=self.redis_host, port=self.redis_port, db=0)
        self.session_pubsub = self.redis_session_client.pubsub()
        self.payload_pubsub = self.redis_payload_client.pubsub()
        self.telegram_pubsub = self.redis_telegram_client.pubsub()
        self.telegram_pubsub.subscribe(self.redis_telegram_channel)

    def current_datetime(self):
        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime('%Y-%m-%d %H:%M:%S.%f')
        return formatted_datetime

    def generate_random_id():
        # Generate three random groups of 6 characters each
        characters = string.digits + string.ascii_letters
        random_id = ''.join(random.choices(characters, k=6))
        return random_id

    def receiver(self):
        print(f"C2 Telegram receiver")
        offset = 0 # read data from redis. if no data, then set it to 0
        while True:
            url = f'https://api.telegram.org/bot{self.bot_token}/getUpdates'
            params = {'offset': offset, 'limit': 1, 'timeout': 2}

            response = requests.get(url, params=params)
            if response.status_code == 200:
                updates_response = response.json()
                updates = updates_response["result"]
                if updates:
                    for update in updates:
                        offset = update['update_id']
                        print(f"C2 Telegram receiver - id: {update['update_id']}, text: {update['channel_post']['text']}, type_text: {type(update['channel_post']['text'])}, offset: {offset}")
                        try:
                            dt = self.current_datetime()
                            text = base64.b64decode(update['channel_post']['text']).decode('utf-8')
                            command = ""
                            (s_key, command) = re.findall(r'\"k\"\:\"(.*?)\"\,\"c\"\:\"(.*?)\"', text, re.DOTALL)[0]
                            commands_fifo_list = []
                            session_key = "session_details_" + s_key
                            session_data = {"session_id": s_key, "session_type": "telegram_bot", "os_type": "NA", "created_at": dt, "host_name": "Telegram Bot", "port": 0, "status": "Connected", "shell": "$", "user_name": "", "commands": commands_fifo_list}
                            check = self.redis_client.exists(session_key)
                            print(f"C2 Telegram receiver - session_key: {session_key}, check: {check}, command: {command}")
                            if check and command:
                                message = ""
                                response = re.findall(r'\,\"v\"\:\"(.*?)\"', text, re.DOTALL)[0]
                                print(f"C2 Telegram  receiver - s_key: {s_key}, command: {command}, response: {response}, message: {message}")
                                message = response.replace("\n", "")
                                payload_key = "payload_details_" + s_key
                                payload_data = {"session_id": s_key, "shell": "$", "command": command, "command_date": dt, "response": message, "response_date": dt}
                                serialized_data = json.dumps(payload_data)
                                self.redis_client.rpush(payload_key, serialized_data)
                                self.redis_client.publish(self.redis_payload_channel, serialized_data)
                                print(f"C2 Telegram receiver - complete")
                            else:
                                print(f"C2 Telegram receiver - session_key: {session_key} init")
                                serialized_data = json.dumps(session_data).encode('utf-8')
                                self.redis_client.set(session_key, serialized_data)
                                self.redis_client.publish(self.redis_session_channel, serialized_data)
                        except Exception as e:
                            print(f"C2 Telegram receiver - error: {e}")
                            message = {}
                    offset = update['update_id'] + 1
            time.sleep(5)

    def subscriber(self):
        print(f"C2 Telegram subscriber")
        while True:
            try:
                messages = self.telegram_pubsub.get_message()
                print(f"C2 Telegram subscriber listening - pubsub: {self.telegram_pubsub}, messages: {messages}")
                if messages and messages['type'] == 'message':
                    data = json.loads(messages['data'].decode('utf-8'))
                    command = data["command"]
                    print(f"C2 Telegram subscriber - redis_subscriber data: {data}, command: {command}")
                    url = f'https://api.telegram.org/bot{self.bot_token}/sendMessage'
                    params = {
                        'chat_id': self.bot_chat_id,
                        'text': command
                    }
                    response = requests.get(url, params=params)
                    print(f"C2 Telegram subscriber - command: {command}, status: {response.status_code}, response: {response.text}")
            except Exception as e:
                print(f"C2 Telegram subscriber - subscriber: websocket close {e}")
            time.sleep(5)

    def start_server(self):
        subscriber_thred = threading.Thread(target=self.subscriber, args=())
        receiver_thread = threading.Thread(target=self.receiver, args=())

        subscriber_thred.start()
        receiver_thread.start()

        subscriber_thred.join()
        receiver_thread.join()

Telegram().start_server()