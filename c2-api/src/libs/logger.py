# C2 Cloud
#
# Author: Arun Govindasamy

import logging
from libs.common import Common

common = Common()

def init_logger(name):
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

    logger = logging.getLogger(name)
    if not logger.handlers:
        # if logger has no handlers, add a handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.setLevel(common.log_level)
        logger.addHandler(console_handler)  
    
    return logger
