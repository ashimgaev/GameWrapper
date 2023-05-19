from data import *
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import argparse
import json
import sys
from pydantic import BaseModel
from master import Master
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



class MasterServer:
    def __init__(self):
        _, *params = sys.argv
        args = serverArgParser.parse_args()
        self.configFile = ConfigFile.read(args.config)
        self.masterClient = Master()
        self.is_active = False

    def isActive(self):
        return self.is_active

    def start(self):
        print("Server started")
        def on_slave_message(msg):
            if self.is_active == True:
                if msg.msg_type == MessageType.SLAVE_REQUEST_CONFIG:
                    cfg = CfgSectionWrapper(self.configFile, msg.msg_payload)
                    out = Data_ConfigSection(name=cfg.getName(), 
                                            pwd=cfg.getPassword(),
                                            remote_accepted=cfg.getAllowed())
                    self.masterClient.sendConfigRequestReply(reqMessage=msg, cfg_section=out)
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

@masterapi.get("/master/status", response_model=MasterStatusResponse)
def master_get_status():
    return MasterStatusResponse(is_active=MasterApp.server.isActive())

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
        if msg.msg_type == MessageType.SLAVE_REPLY_CONFIG_LIST and msg.cfg_sections and len(msg.cfg_sections) > 0:
            MasterApp.server.configFile.clear()
            for s in msg.cfg_sections:
                cfg = makeNewSection(MasterApp.server.configFile, s.name)
                cfg.setPassword(s.pwd)
            MasterApp.server.configFile.write()

    MasterApp.server.masterClient.sendConfigListRequest(on_reply_cb=onReply)
    return BaseResponse(status='OK')

@masterapi.post("/master/config", response_model=BaseResponse)
def set_config(reqBody: ConfigRequest):
    needUpdate = False
    cfgFile = MasterApp.server.configFile
    for newCfg in reqBody.sections:
        currCfg = CfgSectionWrapper(cfgFile, newCfg.name)
        if currCfg.getPassword() != newCfg.pwd:
            currCfg.setPassword(val=newCfg.pwd)
            needUpdate = True
        currCfg.setAllowed(val=newCfg.allowed)
        # Notify slave
        msgCfg = Data_ConfigSection(name=currCfg.getName(), 
                                pwd=currCfg.getPassword(),
                                remote_accepted=currCfg.getAllowed())
        MasterApp.server.masterClient.sendConfigUpdateRequest(msgCfg)
    
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
