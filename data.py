import uuid
import enum
import json
from pydantic import BaseModel
from dataclasses import dataclass

class MessageType(enum.Enum):
    UNKNOWN = 0
    SLAVE_REQUEST_CONFIG = 1
    SLAVE_REQUEST_MASTER_ROLE = 2
    SLAVE_REQUEST_LOG_MESSAGE = 3

    SLAVE_REPLY_CONFIG_LIST = 20
    SLAVE_REPLY_CONFIG_UPDATE = 21
    SLAVE_REPLY_STATISTIC = 22
    SLAVE_REPLY_MASTER_ROLE = 23
    
    MASTER_REQUEST_CONFIG_UPDATE = 100
    MASTER_REQUEST_CONFIG_LIST = 101
    MASTER_REQUEST_STATISTIC = 102,
    MASTER_REQUEST_MASTER_ROLE = 103,
    MASTER_REQUEST_SHOW_MESSAGE = 104,
    MASTER_REQUEST_SLAVE_SHUTDOWN = 105

    MASTER_REPLY_CONFIG = 200
    MASTER_REPLY_MASTER_ROLE = 201


class Data_MessageBase:
    def __init__(self, is_request: bool, type: MessageType = MessageType.UNKNOWN, payload: str = '', on_reply_cb = None):
        self.on_reply_cb = on_reply_cb
        self.msg_type = type
        self.msg_payload = payload
        self.uuid = str(uuid.uuid4())
        self.is_request = is_request
        self.slave_name = 'empty'

    def __str__(self) -> str:
        return f"type={self.msg_type}, payload={self.msg_payload}, uuid={self.uuid}"

class Data_MessageRequest(Data_MessageBase):
    def __init__(self, type: MessageType = MessageType.UNKNOWN, payload: str = ''):
        super().__init__(is_request=True, type=type, payload=payload)

class Data_MessageReply(Data_MessageBase):
    def __init__(self, type: MessageType = MessageType.UNKNOWN, payload: str = ''):
        super().__init__(is_request=False, type=type, payload=payload)


class Data_ConfigSection():
    def __init__(self, name: str = "", pwd: str = "", remote_accepted: bool = False):
        self.name = name
        self.pwd = pwd
        self.remote_accepted=remote_accepted

##### SLAVE SECTION ####
##### REQUEST
class Data_SlaveConfigRequest(Data_MessageRequest):
    def __init__(self, section_name: str = ''):
        super().__init__(type=MessageType.SLAVE_REQUEST_CONFIG, payload=section_name)

class Data_SlaveLogMessageRequest(Data_MessageRequest):
    def __init__(self, msg: str):
        super().__init__(type=MessageType.SLAVE_REQUEST_LOG_MESSAGE, payload=msg)

class Data_SlaveMasterRoleRequest(Data_MessageRequest):
    def __init__(self, name: str):
        super().__init__(type=MessageType.SLAVE_REQUEST_MASTER_ROLE, payload=name)

##### REPLY
class Data_SlaveConfigListReply(Data_MessageReply):
    def __init__(self, cfg_sections: list[Data_ConfigSection]):
        super().__init__(type=MessageType.SLAVE_REPLY_CONFIG_LIST, payload="")
        self.cfg_sections = cfg_sections

class Data_SlaveConfigUpdateReply(Data_MessageReply):
    def __init__(self, status: bool):
        super().__init__(type=MessageType.SLAVE_REPLY_CONFIG_UPDATE, payload="OK")

class Data_SlaveStatisticReply(Data_MessageReply):
    def __init__(self, games: list[str]):
        super().__init__(type=MessageType.SLAVE_REPLY_STATISTIC, payload="")
        self.games = games

class Data_SlaveMasterRoleReply(Data_MessageReply):
    def __init__(self, name: str):
        super().__init__(type=MessageType.SLAVE_REPLY_MASTER_ROLE, payload=name)


##### MASTER SECTION ####
##### REQUEST
class Data_MasterConfigUpdateRequest(Data_MessageRequest):
    def __init__(self, cfg_section: Data_ConfigSection = Data_ConfigSection()):
        super().__init__(type=MessageType.MASTER_REQUEST_CONFIG_UPDATE, payload=cfg_section.name)
        self.cfg_section = cfg_section

class Data_MasterConfigListRequest(Data_MessageRequest):
    def __init__(self):
        super().__init__(type=MessageType.MASTER_REQUEST_CONFIG_LIST)

class Data_MasterShowMessageRequest(Data_MessageRequest):
    def __init__(self, msg: str):
        super().__init__(type=MessageType.MASTER_REQUEST_SHOW_MESSAGE, payload=msg)

class Data_MasterShutdownSlaveRequest(Data_MessageRequest):
    def __init__(self, name: str):
        super().__init__(type=MessageType.MASTER_REQUEST_SLAVE_SHUTDOWN, payload=name)

class Data_MasterStatisticRequest(Data_MessageRequest):
    def __init__(self):
        super().__init__(type=MessageType.MASTER_REQUEST_STATISTIC)

class Data_MasterMasterRoleRequest(Data_MessageRequest):
    def __init__(self, name: str):
        super().__init__(type=MessageType.MASTER_REQUEST_MASTER_ROLE, payload=name)

##### REPLY
class Data_MasterConfigReply(Data_MessageReply):
    def __init__(self, cfg_section: Data_ConfigSection = Data_ConfigSection()):
        super().__init__(type=MessageType.MASTER_REPLY_CONFIG, payload="")
        self.cfg_section = cfg_section

class Data_MasterMasterRoleReply(Data_MessageReply):
    def __init__(self, name: str):
        super().__init__(type=MessageType.MASTER_REPLY_MASTER_ROLE, payload=name)