import uuid
import enum
import json
from pydantic import BaseModel
from dataclasses import dataclass

class MessageType(enum.Enum):
    UNKNOWN = 0
    SLAVE_REQUEST_CONFIG = 1
    
    MASTER_REQUEST_CONFIG_UPDATE = 100
    MASTER_REPLY_CONFIG = 200


class Data_MessageBase:
    def __init__(self, is_request: bool, type: MessageType = MessageType.UNKNOWN, payload: str = '', on_reply_cb = None):
        self.on_reply_cb = on_reply_cb
        self.msg_type = type
        self.msg_payload = payload
        self.uuid = uuid.uuid4()
        self.is_request = is_request

    def __str__(self) -> str:
        return f"type={self.msg_type}, payload={self.msg_payload}, uuid={self.uuid}"

class Data_MessageRequest(Data_MessageBase):
    def __init__(self, type: MessageType = MessageType.UNKNOWN, payload: str = ''):
        super().__init__(is_request=True, type=type, payload=payload)

class Data_MessageReply(Data_MessageBase):
    def __init__(self, type: MessageType = MessageType.UNKNOWN, payload: str = ''):
        super().__init__(is_request=False, type=type, payload=payload)

class Data_SlaveConfigRequest(Data_MessageRequest):
    def __init__(self, section_name: str = ''):
        super().__init__(type=MessageType.SLAVE_REQUEST_CONFIG, payload=section_name)

class Data_ConfigSection():
    def __init__(self, name: str = "", pwd: str = "", remote_accepted: bool = False):
        self.name = name
        self.pwd = pwd
        self.remote_accepted=remote_accepted


class Data_MasterConfigReply(Data_MessageReply):
    def __init__(self, cfg_section: Data_ConfigSection = Data_ConfigSection()):
        super().__init__(type=MessageType.MASTER_REPLY_CONFIG, payload="")
        self.cfg_section = cfg_section

class Data_MasterConfigUpdateRequest(Data_MessageRequest):
    def __init__(self, cfg_section: Data_ConfigSection = Data_ConfigSection()):
        super().__init__(type=MessageType.MASTER_REQUEST_CONFIG_UPDATE, payload=cfg_section.name)
        self.cfg_section = cfg_section
