# C2 Cloud
#
# Author: Arun Govindasamy

from sqlalchemy import text
from models.c2model import c2DbHandler, SessionDetailsTable, PayloadDetailsTable
from libs.logger import init_logger

session = c2DbHandler.session
logger_instance = init_logger('C2_Cloud')

class DBOperations():
    def __init__(self):
        self.session_table = SessionDetailsTable.__tablename__
        self.payload_table = PayloadDetailsTable.__tablename__

    def auth(self):
        # Execute a db query to verify the connection 
        # Checks DB authentication 
        from app import app
        with app.app_context():
            try:
                c2DbHandler.session.query(text("1")).from_statement(text("SELECT 1")).all()
                db_status_code = 200
            except Exception as e:
                logger_instance.info('authCheck - error: {}'.format(e))
                db_status_code = 0
        return db_status_code

    def write_session_data(self, values):
        # This function insert a record in a table 
        logger_instance.info(f'DBOperations - Execute write_session_data function')
        # Define your insert query
        insert_query = text(f"""
            INSERT INTO {self.session_table} (session_id, session_type, os_type, created_at, host_name, port, status, shell, user_name, commands)
            VALUES (:session_id, :session_type, :os_type, :created_at, :host_name, :port, :status, :shell, :user_name, :commands)
            ON CONFLICT (session_id) DO UPDATE SET status = EXCLUDED.status, shell = EXCLUDED.shell, commands = EXCLUDED.commands;
        """)
        user_data = {'session_id': values['session_id'], 'session_type': values['session_type'], 'os_type': values['os_type'], 'created_at': values['created_at'], 'host_name': values['host_name'], 'port': values['port'], 'status': values['status'], 'shell': values['shell'], 'user_name': values['user_name'], 'commands': str(values['commands'])}
        try:
            insertData = c2DbHandler.session.execute(insert_query, user_data)
            c2DbHandler.session.commit()
            data = {'status': 'success'}
        except Exception as e:
            logger_instance.info(f'DBOperations - Failed to insert record, error: {e}')
            data = {'status': 'error'}
        return data

    # 
    def allRecords(self, tablename):
        logger_instance.info('DBOperations - Execute allRecords function')
        select_query = text(f"SELECT * FROM {tablename}")
        result = c2DbHandler.session.execute(select_query)
        return result

    def check_session(self, session_id):
        logger_instance.info('DBOperations - Execute check_session function')
        query = text(f"SELECT COUNT(*) FROM {self.session_table} WHERE session_id = '{session_id}'")
        result = c2DbHandler.session.execute(query)
        count = result.scalar()
        return count

    def write_payload_data(self, values):
        # This function insert a record in a table 
        logger_instance.info('DBOperations - Execute write_payload_data function')
        # Define your insert query
        insert_query = text(f"""
            INSERT INTO {self.payload_table} (session_id, shell, command, command_date, response, response_date)
            VALUES (:session_id, :shell, :command, :command_date, :response, :response_date)
        """)
        user_data = {'session_id': values['session_id'], 'shell': values['shell'], 'command': values['command'], 'command_date': values['command_date'], 'response': values['response'], 'response_date': values['response_date']}
        try:
            insertData = c2DbHandler.session.execute(insert_query, user_data)
            c2DbHandler.session.commit()
            data = {'status': 'success'}
        except Exception as e:
            logger_instance.info('ERROR - insertRecord - Failed to insert record # {}'.format(e))
            data = {'status': 'error'}
        return data

    def selectFristRecord(self, session_id):
        logger_instance.info('DBOperations - Execute selectFristRecord function')
        query = text(f"SELECT * FROM {self.payload_table} WHERE session_id = '{session_id}' AND status = FALSE ORDER BY id LIMIT 1")
        result = c2DbHandler.session.execute(query)
        first_record = result.fetchone()
        return first_record