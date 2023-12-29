# C2 Cloud
#
# Author: Arun Govindasamy

from flask import Blueprint
from controllers.c2Controller import handle_client, allrecords

c2Route = Blueprint('c2Route', __name__)

c2Route.route('/<path:args>', methods=['GET', 'POST'])(handle_client)
#testing
c2Route.route('/all', methods=['GET'])(allrecords)
