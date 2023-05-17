import paho.mqtt.client as paho
from mqtt_point import *
from data import *
import time, threading

class Master(MqttPoint):
    def makeOnMessageReplyCallback(self_inst):
        def cb_func(mesage):
            pass
        return cb_func
    
    def makeOnRequestCallback(self_inst):
        def cb_func(reqMessage: Data_MessageBase):
            if self_inst._on_config_request_cb:
                cfg = self_inst._on_config_request_cb(reqMessage.msg_payload)
                if cfg:
                    self_inst.sendConfigRequestReply(reqMessage, cfg)
        return cb_func

    def __init__(self):
        super().__init__(name="Master", 
                         listen_channel="com.ashimgaev.home/channel/slave", 
                         request_channel="com.ashimgaev.home/channel/master",
                         on_request_cb=Master.makeOnRequestCallback(self))
        self._on_config_request_cb = None


    def sendConfigUpdateRequest(self, cfg_section: Data_ConfigSection):
        msg = Data_MasterConfigUpdateRequest(cfg_section=cfg_section)
        self.sendMessage(msg)

    def sendConfigRequestReply(self, reqMessage: Data_MessageBase, cfg_section: Data_ConfigSection):
        msg = Data_MasterConfigReply(cfg_section=cfg_section)
        msg.uuid = reqMessage.uuid
        self.sendMessage(msg)

    def start(self, on_config_request_cb):
        self._on_config_request_cb = on_config_request_cb
        super().start()

    def stop(self):
        self._on_config_request_cb = None
        super().stop()