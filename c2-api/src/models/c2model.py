# C2 Cloud
#
# Author: Arun Govindasamy

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import UniqueConstraint
from datetime import datetime

c2DbHandler = SQLAlchemy()

class SessionDetailsTable(c2DbHandler.Model):
    __tablename__ = 'session_details'

    id = c2DbHandler.Column(c2DbHandler.Integer, primary_key=True)
    session_id = c2DbHandler.Column(c2DbHandler.String, default='')
    session_type = c2DbHandler.Column(c2DbHandler.String, default='')
    os_type = c2DbHandler.Column(c2DbHandler.String, default='')
    created_at = c2DbHandler.Column(c2DbHandler.DateTime, default=datetime.utcnow)
    host_name = c2DbHandler.Column(c2DbHandler.String, default='')
    port = c2DbHandler.Column(c2DbHandler.String, default='')
    status = c2DbHandler.Column(c2DbHandler.String, default='')
    shell = c2DbHandler.Column(c2DbHandler.String, default='')
    user_name = c2DbHandler.Column(c2DbHandler.String, default='')
    commands = c2DbHandler.Column(c2DbHandler.String, default='')

    __table_args__ = (
        UniqueConstraint('session_id', name='unique_session_id_constraint'),
    )

    @property
    def serialize(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'session_type': self.session_type,
            'os_type': self.os_type,
            'created_at': self.created_at,
            'host_name': self.host_name,
            'port': self.port,
            'status': self.status,
            'shell': self.shell,
            'user_name': self.user_name,
            'commands': self.commands
        }

class PayloadDetailsTable(c2DbHandler.Model):
    __tablename__ = 'payload_details'

    id = c2DbHandler.Column(c2DbHandler.Integer, primary_key=True)
    session_id = c2DbHandler.Column(c2DbHandler.String, default='')
    shell = c2DbHandler.Column(c2DbHandler.String, default='')
    command = c2DbHandler.Column(c2DbHandler.String, default='')
    command_date = c2DbHandler.Column(c2DbHandler.DateTime, default=datetime.utcnow)
    response = c2DbHandler.Column(c2DbHandler.Text, default='')
    response_date = c2DbHandler.Column(c2DbHandler.DateTime, nullable=True, default=None)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'shell': self.shell,
            'command': self.command,
            'command_date': self.command_date,
            'response': self.response,
            'response_date': self.response_date
        }
