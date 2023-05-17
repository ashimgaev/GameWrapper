from data import *
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import argparse
import json
import sys
from pydantic import BaseModel
from master import Master
from config_file import ConfigFile, ConfigSchema

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
        self.is_active = True
        def on_config_request(cfgname: str):
            is_allowed = self.configFile.getParam(cfgname, ConfigSchema.PARAM_NAME_ALLOWED)
            remote_allowed = is_allowed.lower() in ['true', '1', 'y', 'yes']
            return Data_ConfigSection(name=cfgname, 
                                     pwd=self.configFile.getParam(cfgname, ConfigSchema.PARAM_NAME_PASSWORD),
                                     remote_accepted=remote_allowed)
        self.masterClient.start(on_config_request)

    def stop(self):
        print("Server stopped")
        self.masterClient.stop()
        self.is_active = False


class MasterApp:
    server: MasterServer

def master_app_onstart():
    print('master_app_onstart called')
    MasterApp.server = MasterServer()

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
        MasterApp.server.start()
    else:
        MasterApp.server.stop()
    return MasterStatusResponse(is_active=MasterApp.server.isActive())

@masterapi.get("/master/config", response_model=ConfigResponse)
def get_config():
    sections = list[ConfigSection]()
    cfg = MasterApp.server.configFile
    for name in cfg.getSections():
        sections.append(ConfigSection(name=name, 
                                      pwd=cfg.getParam(name, ConfigSchema.PARAM_NAME_PASSWORD), 
                                      allowed=cfg.getParam(name, ConfigSchema.PARAM_NAME_ALLOWED)))
    response = ConfigResponse(sections=sections)
    return response

@masterapi.post("/master/config", response_model=BaseResponse)
def set_config(reqBody: ConfigRequest):
    needUpdate = False
    cfgFile = MasterApp.server.configFile
    for cfg in reqBody.sections:
        currentPwd = cfgFile.getParam(section=cfg.name, name=ConfigSchema.PARAM_NAME_PASSWORD)
        if currentPwd != cfg.pwd:
            cfgFile.setParam(section=cfg.name, name=ConfigSchema.PARAM_NAME_PASSWORD, val=cfg.pwd)
            needUpdate = True
        cfgFile.setParam(section=cfg.name, name=ConfigSchema.PARAM_NAME_ALLOWED, val=str(cfg.allowed))
        # Notify slave
        is_allowed = cfgFile.getParam(cfg.name, ConfigSchema.PARAM_NAME_ALLOWED)
        remote_allowed = is_allowed.lower() in ['true', '1', 'y', 'yes']
        cfg = Data_ConfigSection(name=cfg.name, 
                                pwd=cfgFile.getParam(cfg.name, ConfigSchema.PARAM_NAME_PASSWORD),
                                remote_accepted=remote_allowed)
        MasterApp.server.masterClient.sendConfigUpdateRequest(cfg)
    
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
