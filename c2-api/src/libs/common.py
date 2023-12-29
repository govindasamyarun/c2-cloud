# C2 Cloud
#
# Author: Arun Govindasamy

import random
import string
import yaml
from datetime import datetime

class Common():
    def __init__(self):
        with open('config.yaml') as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        self.tcp_server_ip = config['tcp_server']['ip']
        self.tcp_server_port = config['tcp_server']['port']
        self.tcp_max_retry_count = config['tcp_server']['max_retry_count']
        self.tcp_socket_buffer_size = config['tcp_server']['socket_buffer_size']
        self.redis_hostname = config["redis"]["hostname"]
        self.redis_port = config["redis"]["port"]
        self.redis_channel_session = config['redis']['channel_session']
        self.redis_channel_payload = config['redis']['channel_payload']
        self.db_hostname = config["database"]["hostname"]
        self.db_port = config["database"]["port"]
        self.db_username = config["database"]["username"]
        self.db_password = config["database"]["password"]
        self.db_dbname = config["database"]["database"]
        self.web_hostname = config["web"]["hostname"]
        self.web_port = config["web"]["port"]
        self.log_level = config['logger']['level']

    def generate_random_id(self):
        # Generate three random groups of 6 characters each
        characters = string.digits + string.ascii_letters
        random_id = ''.join(random.choices(characters, k=6))
        return random_id

    def current_datetime(self):
        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime('%Y-%m-%d %H:%M:%S.%f')
        return formatted_datetime