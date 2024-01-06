# C2 Cloud
#
# Author: Arun Govindasamy

from flask import Blueprint
from controllers.apiController import allrecords, payload_generator, exec_command, session_records, payload_records, hc_records, list_files, file_upload

apiRoute = Blueprint('apiRoute', __name__)

apiRoute.route('/payload/generate/<host_name>/<port>', methods=['GET', 'POST'])(payload_generator)
apiRoute.route('/exec/<session_id>/<command>', methods=['GET', 'POST'])(exec_command)
apiRoute.route('/list/files', methods=['GET'])(list_files)
apiRoute.route('/file/upload', methods=['POST'])(file_upload)
#testing
apiRoute.route('/all', methods=['GET'])(allrecords)
apiRoute.route('/redis/sessions/<session_id>', methods=['GET'])(session_records)
apiRoute.route('/redis/c2/<session_id>', methods=['GET'])(payload_records)
apiRoute.route('/redis/hc/<session_id>', methods=['GET'])(hc_records)