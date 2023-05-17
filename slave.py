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
    
    def makeOnConfigReplyCallback(self_inst, on_reply_cb):
        def cb_func(mesage: Data_MasterConfigReply):
            if on_reply_cb:
                on_reply_cb(mesage.cfg_section)
        return cb_func

    def __init__(self):
        super().__init__(name="Slave", 
                         listen_channel="com.ashimgaev.home/channel/master", 
                         request_channel="com.ashimgaev.home/channel/slave", 
                         on_request_cb=SlaveClient.makeOnRequestCallback(self))
        self.on_request_cb = None
        self.config_request_loop = (False,  threading.Timer)
        self.config_request_loop_period = 10
    
    def setConfigLoopPeriod(self, val: int):
        self.config_request_loop_period = val

    def startConfigRequestLoop(self, execTarget: str, on_reply_cb, pre_request_cb, config_loop_period: int):
        self.config_request_loop_period = config_loop_period
        def send_request_func():
            if self.config_request_loop[0]:
                msg = Data_SlaveConfigRequest(section_name=execTarget)
                if pre_request_cb:
                    pre_request_cb(execTarget)
                self.sendMessage(msg, SlaveClient.makeOnConfigReplyCallback(self, on_reply_cb))
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
        self.stopConfigRequestLoop()

def main():

    slaveClient = SlaveClient()
    slaveClient.start()

    slaveClient.startConfigRequestLoop("cossaks", None)

    while True:
        pass

if __name__ == "__main__": 
    main()

