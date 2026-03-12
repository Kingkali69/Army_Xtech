#!/usr/bin/env python3

import socket
import json
import threading
import time
import queue
from typing import Dict, List, Callable
from dataclasses import dataclass, field

COMMS_PORT = 7006
known_nodes = ["192.168.1.116", "192.168.1.235", "192.168.1.14"]

@dataclass
class Message:
    msg_type: str
    sender: str
    payload: dict
    timestamp: float = field(default_factory=time.time)
    msg_id: str = ""

    def __post_init__(self):
        if not self.msg_id:
            import hashlib
            self.msg_id = hashlib.md5(f"{self.sender}{self.timestamp}".encode()).hexdigest()[:8]

    def to_json(self) -> str:
        return json.dumps({
            "type": self.msg_type,
            "sender": self.sender,
            "payload": self.payload,
            "ts": self.timestamp,
            "id": self.msg_id
        })

    @staticmethod
    def from_json(data: str) -> "Message":
        d = json.loads(data)
        return Message(
            msg_type=d["type"],
            sender=d["sender"],
            payload=d["payload"],
            timestamp=d["ts"],
            msg_id=d["id"]
        )

class MeshComms:
    def __init__(self):
        self.node_ip = self._get_ip()
        self.handlers: Dict[str, Callable] = {}
        self.inbox: queue.Queue = queue.Queue()
        self.outbox: queue.Queue = queue.Queue()
        self.seen_messages: set = set()
        self.running = False

    def _get_ip(self) -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def register_handler(self, msg_type: str, handler: Callable):
        self.handlers[msg_type] = handler

    def send(self, msg_type: str, payload: dict, target: str = None):
        msg = Message(msg_type=msg_type, sender=self.node_ip, payload=payload)
        
        if target:
            self._send_to(msg, target)
        else:
            for node in known_nodes:
                if node != self.node_ip:
                    self._send_to(msg, node)

    def _send_to(self, msg: Message, target: str):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3)
            s.connect((target, COMMS_PORT))
            s.sendall(msg.to_json().encode())
            s.close()
        except:
            pass

    def broadcast(self, msg_type: str, payload: dict):
        self.send(msg_type, payload, target=None)

    def _listen(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("0.0.0.0", COMMS_PORT))
        srv.listen(50)
        
        while self.running:
            try:
                srv.settimeout(1)
                c, addr = srv.accept()
                data = c.recv(65535).decode().strip()
                c.close()
                
                if data:
                    msg = Message.from_json(data)
                    
                    if msg.msg_id in self.seen_messages:
                        continue
                    self.seen_messages.add(msg.msg_id)
                    
                    if len(self.seen_messages) > 10000:
                        self.seen_messages = set(list(self.seen_messages)[-5000:])
                    
                    self.inbox.put(msg)
            except socket.timeout:
                continue
            except:
                pass

    def _process(self):
        while self.running:
            try:
                msg = self.inbox.get(timeout=1)
                
                if msg.msg_type in self.handlers:
                    self.handlers[msg.msg_type](msg)
            except queue.Empty:
                continue
            except:
                pass

    def start(self):
        self.running = True
        threading.Thread(target=self._listen, daemon=True).start()
        threading.Thread(target=self._process, daemon=True).start()

    def stop(self):
        self.running = False

MSG_TARGET_SPAWN = "target_spawn"
MSG_TARGET_KILL = "target_kill"
MSG_FLAG_CAPTURED = "flag_captured"
MSG_NODE_ALERT = "node_alert"
MSG_REBALANCE = "rebalance"
MSG_HEARTBEAT = "heartbeat"

comms = MeshComms()

def get_comms() -> MeshComms:
    return comms

if __name__ == "__main__":
    c = get_comms()
    
    def on_heartbeat(msg):
        print(f"[HB] {msg.sender}: {msg.payload}")
    
    def on_alert(msg):
        print(f"[ALERT] {msg.sender}: {msg.payload}")
    
    c.register_handler(MSG_HEARTBEAT, on_heartbeat)
    c.register_handler(MSG_NODE_ALERT, on_alert)
    
    c.start()
    print(f"[COMMS] Node: {c.node_ip}")
    print(f"[COMMS] Listening on port {COMMS_PORT}")
    
    while True:
        c.broadcast(MSG_HEARTBEAT, {"status": "alive", "time": time.time()})
        time.sleep(5)

