# C2 Cloud
#
# Author: Arun Govindasamy

from flask import render_template, request, redirect, url_for, send_file
from libs.logger import init_logger
import base64
import os

logger_instance = init_logger('C2_Cloud')

def download(encoded_filename):
    logger_instance.info(f"download - encoded_filename: {encoded_filename}")
    filename = base64.b64decode(encoded_filename).decode('utf-8')
    filepath = "/usr/src/app/src/exploits/" + filename
    if os.path.exists(filename) and os.path.isfile(filename):
        return send_file(filepath, as_attachment=True)
    else:
        return "File not found or invalid file path"