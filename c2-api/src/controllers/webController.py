# C2 Cloud
#
# Author: Arun Govindasamy

from flask import render_template, request, redirect, url_for
from libs.logger import init_logger

logger_instance = init_logger('C2_Cloud')

def home():
    logger_instance.info('web - home')
    return render_template('home.html')

def payload():
    logger_instance.info('web - payload')
    return render_template('payload.html')

def cli(session_id):
    logger_instance.info(f'web - cli, session_id: {session_id}')
    return render_template('cli.html')
