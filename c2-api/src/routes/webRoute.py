# C2 Cloud
#
# Author: Arun Govindasamy

from flask import Blueprint
from controllers.webController import home, cli, payload, exploits

webRoute = Blueprint('webRoute', __name__)

webRoute.route('/home', methods=['GET'])(home)
webRoute.route('/payload', methods=['GET'])(payload)
webRoute.route('/exploits', methods=['GET'])(exploits)
webRoute.route('/cli-<session_id>', methods=['GET'])(cli)
