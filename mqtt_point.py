import paho.mqtt.client as paho
import pickle
from data import *

class MqttPoint:
    def makeOnConnectListener(self_inst):
        def on_connect(client, userdata, flags, rc):
            client.subscribe(self_inst.listen_channel)
        return on_connect
    
    def makeOnMessageListener(self_inst):
        def on_message(client, userdata, msg):
            message = pickle.loads(msg.payload)
            print(f'{self_inst.name} received message: {str(message)}')
            if message.is_request:
                if self_inst.on_request_cb:
                    self_inst.on_request_cb(message)
            else:
                on_reply_cb = None
                for _, msgPair in self_inst.last_message_map.items():
                    last_msg, cb = msgPair
                    if message.uuid == last_msg.uuid:
                        on_reply_cb = cb
                        break
                if on_reply_cb:
                    on_reply_cb(message)
                else:
                    if self_inst.on_request_cb:
                        self_inst.on_request_cb(message)
        return on_message

    def __init__(self, name: str, listen_channel: str, request_channel: str, on_request_cb):
        self.name = name

        self.listen_channel = listen_channel
        self.request_channel = request_channel

        self.on_request_cb = on_request_cb

        self.last_message_map = {}
        
        self.req_client = paho.Client()
        self.req_client.on_publish = None
        self.req_client.on_pre_connect = None
        self.req_client.connect('broker.hivemq.com', 1883)

        self.master_listener = paho.Client()
        self.master_listener.on_connect = MqttPoint.makeOnConnectListener(self)
        self.master_listener.on_message = MqttPoint.makeOnMessageListener(self)
        self.master_listener.on_pre_connect = None
        self.master_listener.connect("broker.hivemq.com", 1883, 60)

    def sendMessage(self, msg: Data_MessageBase, on_reply_cb = None):
        self.last_message_map[msg.msg_type] = (msg, on_reply_cb)
        print(f'{self.name} sending request: {str(msg)}')
        mqtt_msg = pickle.dumps(msg)
        self.req_client.publish(self.request_channel, mqtt_msg, qos=1)

    def start(self):
        self.master_listener.loop_start()
        self.req_client.loop_start()

    def stop(self):
        self.master_listener.loop_stop(force=True)
        self.req_client.loop_stop(force=True)