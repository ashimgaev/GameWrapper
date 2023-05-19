import paho.mqtt.client as paho
from mqtt_point import *
from data import *
import time, threading

class Master(MqttPoint):
    def makeOnMessageReplyCallback(self_inst):
        def cb_func(mesage):
            pass
        return cb_func
    
    def makeOnSlaveRequestCallback(self_inst):
        def cb_func(reqMessage: Data_MessageBase):
            if self_inst._on_slave_request_cb:
                self_inst._on_slave_request_cb(reqMessage)
        return cb_func

    def __init__(self):
        super().__init__(name="Master", 
                         listen_channel="com.ashimgaev.home/channel/slave_dbg", 
                         request_channel="com.ashimgaev.home/channel/master_dbg",
                         on_request_cb=Master.makeOnSlaveRequestCallback(self))
        self._on_slave_request_cb = None


    def sendConfigUpdateRequest(self, cfg_section: Data_ConfigSection, on_reply_cb):
        msg = Data_MasterConfigUpdateRequest(cfg_section=cfg_section)
        self.sendMessage(msg, on_reply_cb=on_reply_cb)

    def sendConfigListRequest(self, on_reply_cb):
        def onReply(msg):
            if on_reply_cb:
                on_reply_cb(msg)
        self.sendMessage(Data_MasterConfigListRequest(), onReply)

    def sendConfigRequestReply(self, reqMessage: Data_MessageBase, cfg_section: Data_ConfigSection):
        msg = Data_MasterConfigReply(cfg_section=cfg_section)
        msg.uuid = reqMessage.uuid
        self.sendMessage(msg)

    def start(self, on_config_request_cb):
        self._on_slave_request_cb = on_config_request_cb
        super().start()

    def stop(self):
        self._on_slave_request_cb = None
        super().stop()