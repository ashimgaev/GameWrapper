from data import *
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import argparse
import json
import sys
from pydantic import BaseModel
from master import Master
from datetime import datetime
from config_file import ConfigFile, ConfigSchema, CfgSectionWrapper, makeNewSection

serverArgParser = argparse.ArgumentParser(description='SBC Rest API Server',
                                 prog=sys.argv[0],
                                 usage='%(prog)s [OPTIONS]',
                                 epilog='\n')

# Argument used to specify a server configuration json file
serverArgParser.add_argument('-p', '--port',
                    type=str,
                    default=8005,
                    help='used to specify a server port')

serverArgParser.add_argument('-c', '--config',
                    type=str,
                    default='master_config.ini',
                    help='path to config file')



class MasterLogger:
    def __init__(self, maxSize: int):
        self._maxSize = maxSize
        self._logs = list[str]()

    def push(self, msg: str):
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        self._logs.append(f'[{current_time}]: {msg}')
        if len(self._logs) > self._maxSize:
            self._logs.pop(0)

    def getLogs(self) -> list[str]:
        return self._logs

class MasterServer:
    def __init__(self):
        _, *params = sys.argv
        args = serverArgParser.parse_args()
        self.configFile = ConfigFile.read(args.config)
        self.masterClient = Master()
        self.is_active = False
        self._logger = MasterLogger(7)

    def isActive(self):
        return self.is_active
    
    def pushSlaveLog(self, mqtt, msg: str):
        self._logger.push(f'{mqtt.slave_name}: {msg}')

    def start(self):
        print("Server started")
        def on_slave_message(msg):
            if msg.msg_type == MessageType.SLAVE_REQUEST_CONFIG:
                self.pushSlaveLog(msg, f'config request for [{msg.msg_payload}]')
                if self.is_active == True:
                    cfg = CfgSectionWrapper(self.configFile, msg.msg_payload)
                    out = Data_ConfigSection(name=cfg.getName(), 
                                            pwd=cfg.getPassword(),
                                            remote_accepted=cfg.getAllowed())
                    self.pushSlaveLog(msg, f'reply to config [{msg.msg_payload}] with {str(cfg.getAllowed())}')
                    self.masterClient.sendConfigRequestReply(reqMessage=msg, cfg_section=out)
            elif msg.msg_type == MessageType.SLAVE_REQUEST_LOG_MESSAGE:
                self.pushSlaveLog(msg, f'log-> {msg.msg_payload}')
            
            # Special case for master requests
            elif msg.msg_type == MessageType.MASTER_REPLY_MASTER_ROLE:
                self.pushSlaveLog(msg, f' master role ACK reply')
            elif msg.msg_type == MessageType.MASTER_REQUEST_MASTER_ROLE:
                if self.masterClient.getName() != msg.msg_payload:
                    self.masterClient.sendMasterRoleRequestReply(reqMessage=msg)
                    self.masterClient.stop()
        self.masterClient.start(on_slave_message)

    def stop(self):
        print("Server stopped")
        self.masterClient.stop()
        self.is_active = False

    def resume(self):
        print("Server resumed")
        self.is_active = True

    def suspend(self):
        print("Server suspended")
        self.is_active = False

class MasterApp:
    server: MasterServer

def master_app_onstart():
    print('master_app_onstart called')
    MasterApp.server = MasterServer()
    MasterApp.server.start()

def master_app_onstop():
    print('master_app_onstop called')
    MasterApp.server.stop()


class ConfigSection(BaseModel):
    name: str
    pwd: str
    allowed: bool

class ConfigRequest(BaseModel):
    sections: list[ConfigSection]

class ConfigResponse(BaseModel):
    sections: list[ConfigSection]

class MasterStatusResponse(BaseModel):
    is_active: bool
    name: str

class MasterLogsResponse(BaseModel):
    logs: list[str]

class MasterStatusRequest(BaseModel):
    is_active: bool

class BaseResponse(BaseModel):
    status: str

masterapi = FastAPI(title='ParentControl REST API',
                description="Game launcher control",
                license_info={'name': 'Copyright by Alexander Shimgaev. All rights reserved'},
                on_startup=[master_app_onstart], 
                on_shutdown=[master_app_onstop])

masterapi.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@masterapi.get("/master/app/{resource}")
def get_demo(resource: str):
    out = ''
    with open(f'./html/{resource}', 'r') as resFile:
        out = resFile.read()
    return HTMLResponse(content=out, status_code=200)

@masterapi.get("/master/send-message", response_model=BaseResponse)
def master_send_message(msg: str):
    MasterApp.server.masterClient.sendShowMessageRequest(msg=msg)
    return BaseResponse(status='OK')

@masterapi.get("/master/slave-shutdown", response_model=BaseResponse)
def master_send_slave_shutdown(name: str):
    MasterApp.server.masterClient.sendSlaveShutdownRequest(name=name)
    return BaseResponse(status='OK')

@masterapi.get("/master/logs", response_model=MasterLogsResponse)
def master_get_logs():
    return MasterLogsResponse(logs=MasterApp.server._logger.getLogs())

@masterapi.get("/master/statistic", response_model=BaseResponse)
def master_get_statistic():
    def onReply(msg):
        if msg.msg_type == MessageType.SLAVE_REPLY_STATISTIC:
            MasterApp.server.pushSlaveLog(msg, f'statistic reply-> {msg.games}')
    MasterApp.server._logger.push(f'Master statistic request')
    MasterApp.server.masterClient.sendStatisticRequest(onReply)
    return BaseResponse(status='OK')

@masterapi.get("/master/master-role", response_model=BaseResponse)
def master_get_master_role():
    MasterApp.server._logger.push(f'Master request: MASTER ROLE')
    MasterApp.server.masterClient.sendMasterRoleRequest()
    return BaseResponse(status='OK')

@masterapi.get("/master/status", response_model=MasterStatusResponse)
def master_get_status():
    return MasterStatusResponse(is_active=MasterApp.server.isActive(), name=MasterApp.server.masterClient.getName())

@masterapi.post("/master/status", response_model=MasterStatusResponse)
def master_set_status(reqBody: MasterStatusRequest):
    if reqBody.is_active:
        MasterApp.server.resume()
    else:
        MasterApp.server.suspend()
    return MasterStatusResponse(is_active=MasterApp.server.isActive())

@masterapi.get("/master/config", response_model=ConfigResponse)
def get_config():
    sections = list[ConfigSection]()
    cfgFile = MasterApp.server.configFile
    for name in cfgFile.getSections():
        cfg = CfgSectionWrapper(cfgFile, name)
        sections.append(ConfigSection(name=cfg.getName(), 
                                      pwd=cfg.getPassword(), 
                                      allowed=cfg.getAllowed()))
    response = ConfigResponse(sections=sections)
    return response

@masterapi.get("/master/config/sync", response_model=BaseResponse)
def sync_config():
    def onReply(msg):
        if msg.msg_type == MessageType.SLAVE_REPLY_CONFIG_LIST:
            MasterApp.server.pushSlaveLog(msg, f'sync config reply with {len(msg.cfg_sections)} items')
            if msg.cfg_sections and len(msg.cfg_sections) > 0:
                MasterApp.server.configFile.clear()
                for s in msg.cfg_sections:
                    cfg = makeNewSection(MasterApp.server.configFile, s.name)
                    cfg.setPassword(s.pwd)
                MasterApp.server.configFile.write()
    MasterApp.server._logger.push(f'Master sync config request')
    MasterApp.server.masterClient.sendConfigListRequest(on_reply_cb=onReply)
    return BaseResponse(status='OK')

@masterapi.post("/master/config", response_model=BaseResponse)
def set_config(reqBody: ConfigRequest):
    needUpdate = False
    cfgFile = MasterApp.server.configFile
    for newCfg in reqBody.sections:
        cfg = CfgSectionWrapper(cfgFile, newCfg.name)
        if cfg.getPassword() != newCfg.pwd:
            cfg.setPassword(val=newCfg.pwd)
            needUpdate = True
        cfg.setAllowed(val=newCfg.allowed)
        # Notify slave
        msgCfg = Data_ConfigSection(name=cfg.getName(), 
                                pwd=cfg.getPassword(),
                                remote_accepted=cfg.getAllowed())
        def on_reply(msg):
            MasterApp.server.pushSlaveLog(msg, f'config ACK reply for [{cfg.getName()}]')

        MasterApp.server._logger.push(f'Master send config update request [{cfg.getName()}]')
        MasterApp.server.masterClient.sendConfigUpdateRequest(msgCfg, on_reply)
    
    if needUpdate:
        cfgFile.write()
    
    return BaseResponse(status='OK')

MASTER_APP = masterapi

def main():
    _, *params = sys.argv
    print("Starting REST API with parameters:", params)
    args = serverArgParser.parse_args()
    print("serving at port", args.port)
    import uvicorn  
    uvicorn.run('master_main:MASTER_APP', host="127.0.0.1", port=args.port)
    

if __name__ == "__main__": 
    main()
