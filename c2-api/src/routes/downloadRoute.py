# C2 Cloud
#
# Author: Arun Govindasamy

from flask import Blueprint
from controllers.downloadController import download

downloadRoute = Blueprint('downloadRoute', __name__)

# download exploits, tools & files from c2 cloud  
downloadRoute.route('/<encoded_filename>', methods=['GET'])(download)