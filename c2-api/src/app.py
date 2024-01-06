# C2 Cloud
#
# Author: Arun Govindasamy

import os
import threading
import json
import time
from datetime import datetime
from flask import Flask, request
from flask_migrate import Migrate
from models.c2model import c2DbHandler
from routes.webRoute import webRoute
from routes.apiRoute import apiRoute
from routes.downloadRoute import downloadRoute
from routes.c2Route import c2Route
from waitress import serve
from c2tcp import C2TcpServer
from libs.common import Common
from libs.redisOperations import RedisOperations

app = Flask(__name__)

app.debug = False

common = Common()

# DB config 
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://{}:{}@{}:{}/{}".format(common.db_username, common.db_password, common.db_hostname, common.db_port, common.db_dbname)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# C2 DB handler 
c2DbHandler.init_app(app)
migrate = Migrate(app, c2DbHandler)

with app.app_context():
    # Creates tables if not exists 
    c2DbHandler.create_all()

# Routes to the api controller 
app.register_blueprint(webRoute, url_prefix='/web')
app.register_blueprint(apiRoute, url_prefix='/api')
app.register_blueprint(downloadRoute, url_prefix='/dld')
app.register_blueprint(c2Route)

def monitor_http_heartbeat():
    redis_client = RedisOperations()
    while True:
        new_epoch = datetime.utcnow()
        queryString = "*"
        records = redis_client.get_hc_records(queryString)
        for record in records:
            record = json.loads(record)
            redis_session_key = "session_details_" + record["session_id"]
            redis_data = redis_client.get_data(redis_session_key)
            hc_epoch = datetime.strptime(record["heartbeat"], "%Y-%m-%d %H:%M:%S")
            time_diff = int(abs(new_epoch - hc_epoch).total_seconds())
            if time_diff > 5 and redis_data["status"] == "Connected":
                redis_data["status"] = "Disconnected"
                redis_client.write_session_data(redis_session_key, redis_data)
                redis_client.publish_message("c2_session", json.dumps(redis_data))
        time.sleep(5)

if __name__ == "__main__":
    # Start Flask server in a thread
    flask_thread = threading.Thread(target=serve, args=(app,), kwargs={"host": common.web_hostname, "port": common.web_port})
    flask_thread.start()

    # Start Flask server in a thread
    hc_thread = threading.Thread(target=monitor_http_heartbeat)
    hc_thread.start()

    # Start TCP server in a thread
    C2TcpServer(app).tcp_server()
