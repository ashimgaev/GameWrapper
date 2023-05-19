import paho.mqtt.client as paho
from mqtt_point import *
from data import *
import threading

class SlaveClient(MqttPoint):
    def makeOnRequestCallback(self_inst):
        def cb_func(mesage):
            if self_inst.on_request_cb:
                self_inst.on_request_cb(mesage)
        return cb_func
    
    def __init__(self):
        super().__init__(name="Slave", 
                         listen_channel="com.ashimgaev.home/channel/master_dbg", 
                         request_channel="com.ashimgaev.home/channel/slave_dbg", 
                         on_request_cb=SlaveClient.makeOnRequestCallback(self))
        self.on_request_cb = None
        self.config_request_loop = (False,  threading.Timer)
        self.config_request_loop_period = 10
    
    def setConfigLoopPeriod(self, val: int):
        self.config_request_loop_period = val

    def startConfigRequestLoop(self, execTarget: str, on_reply_cb, pre_request_cb, config_loop_period: int):
        self.config_request_loop_period = config_loop_period
        def send_request_func():
            if self.config_request_loop[0] and self.config_request_loop_period > 0:
                msg = Data_SlaveConfigRequest(section_name=execTarget)
                if pre_request_cb:
                    pre_request_cb(execTarget)
                def on_reply(mesage: Data_MasterConfigReply):
                    if on_reply_cb:
                        on_reply_cb(mesage.cfg_section)
                self.sendMessage(msg, on_reply)
                self.config_request_loop = (True, threading.Timer(self.config_request_loop_period, send_request_func))
                self.config_request_loop[1].start()
        self.config_request_loop = (True, None)
        send_request_func()
    
    def stopConfigRequestLoop(self):
        if self.config_request_loop[1]:
            self.config_request_loop[1].cancel()
        self.config_request_loop = (False, None)

    def start(self, on_request_cb = None):
        self.on_request_cb = on_request_cb
        super().start()

    def stop(self):
        super().stop()
        self.setConfigLoopPeriod(0)
        self.stopConfigRequestLoop()

    def sendConfigListReply(self, reqMessage: Data_MessageBase, cfg_sections: list[Data_ConfigSection]):
        msg = Data_SlaveConfigListReply(cfg_sections=cfg_sections)
        msg.uuid = reqMessage.uuid
        self.sendMessage(msg)

    def sendConfigUpdateReply(self, reqMessage: Data_MessageBase):
        msg = Data_SlaveConfigUpdateReply(status=True)
        msg.uuid = reqMessage.uuid
        self.sendMessage(msg)

    def sendGameStartedRequest(self, gameName: str):
        self.sendMessage(Data_SlaveGameStartedRequest(gameName=gameName))

    def sendGameSoppedRequest(self, gameName: str):
        self.sendMessage(Data_SlaveGameStoppedRequest(gameName=gameName))

def main():

    slaveClient = SlaveClient()
    slaveClient.start()

    slaveClient.startConfigRequestLoop("cossaks", None)

    while True:
        pass

if __name__ == "__main__": 
    main()


