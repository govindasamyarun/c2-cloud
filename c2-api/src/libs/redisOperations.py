# C2 Cloud
#
# Author: Arun Govindasamy

import redis
import yaml
import json
from libs.logger import init_logger
from libs.common import Common

common = Common()
logger_instance = init_logger('C2_Cloud')

class RedisOperations():
    def __init__(self):
        # Redis variable declaration 
        redis_hostname = common.redis_hostname
        redis_port = common.redis_port
        # Create a Redis client
        self.redis_client = redis.StrictRedis(host=redis_hostname, port=redis_port, decode_responses=True)

    def publish_message(self, channel, message):
        # broadcast message to clients 
        logger_instance.debug(f"publish_message, channel: {channel}, message: {message}")
        self.redis_client.publish(channel, message)

    def get_session_records(self, queryString):
        # Get all keys matching a pattern (e.g., '*' for all keys)
        all_keys = self.redis_client.keys('session_details_'+queryString)
        # Retrieve values for all keys
        all_records = self.redis_client.mget(all_keys)
        return all_records

    def get_hc_records(self, queryString):
        # Get all keys matching a pattern (e.g., '*' for all keys)
        all_keys = self.redis_client.keys('hc_'+queryString)
        # Retrieve values for all keys
        all_records = self.redis_client.mget(all_keys)
        return all_records

    def get_payload_records(self, session_id):
        # Get all keys matching a pattern (e.g., '*' for all keys)
        all_keys = self.redis_client.keys('payload_details_*')
        all_records = []
        for key in all_keys:
            try:
                # Retrieve serialized dictionaries from Redis List
                serialized_dicts = self.redis_client.lrange(key, 0, -1)
                for serialized_dict in serialized_dicts:
                    all_records.append(serialized_dict)
            except Exception as e:
                logger_instance.info(f"get_payload_records, key: {key}, error: {e}")
        return all_records

    def get_data(self, redis_key):
        # Retrieve the serialized data from Redis
        key = self.redis_client.get(redis_key)
        if key is not None:
            redis_data = json.loads(self.redis_client.get(redis_key).encode('utf-8)'))
        else:
            redis_data = {}
        return redis_data

    def write_session_data(self, redis_key, redis_data):
        # store session records. it cannot handle the data structure of payload_details 
        serialized_data = json.dumps(redis_data).encode('utf-8')
        self.redis_client.set(redis_key, serialized_data)

    def write_payload_data(self, redis_key, redis_data):
        # store payload records 
        serialized_data = json.dumps(redis_data)
        self.redis_client.rpush(redis_key, serialized_data)
