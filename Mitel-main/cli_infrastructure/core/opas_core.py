#!/usr/bin/env python3
"""
OPAS - OmniPlatform AI Substrate
================================
Proprietary sync, mesh traversal, and Android independence layer.
Patent-pending technology for cross-platform autonomous synchronization.

Copyright (c) 2024 KK&G DevOps. All rights reserved.
PROPRIETARY AND CONFIDENTIAL - Patent Pending

Core Features:
- Smart Sync: Adaptive file synchronization with intelligent batching
- Remote Apply: Autonomous update application across mesh nodes
- Android Independence: Standalone operation with seamless reconnection
- Mesh Traversal: AI-driven node navigation and file propagation
- Full Audit Trail: Patent-ready logging of all operations
"""

import os
import sys
import json
import time
import hashlib
import zipfile
import tempfile
import threading
import queue
import socket
import platform
import base64
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path

OPAS_VERSION = "1.0.0"
OPAS_PATENT_ID = "OPAS-2024-001"

class SyncStrategy(Enum):
    INDIVIDUAL = "individual"
    BATCH_ZIP = "batch_zip"
    DELTA = "delta"
    FULL_CLONE = "full_clone"

class NodeState(Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    SYNCING = "syncing"
    ERROR = "error"

class ChangeType(Enum):
    ADDED = "added"
    MODIFIED = "modified"
    REMOVED = "removed"

@dataclass
class FileChange:
    path: str
    change_type: ChangeType
    old_hash: str = ""
    new_hash: str = ""
    size: int = 0
    timestamp: float = field(default_factory=time.time)

@dataclass
class SyncOperation:
    op_id: str
    strategy: SyncStrategy
    files: List[FileChange]
    source_node: str
    target_nodes: List[str]
    started_at: float
    completed_at: float = 0
    status: str = "pending"
    results: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AuditEntry:
    timestamp: float
    operation: str
    details: Dict[str, Any]
    node_id: str
    patent_ref: str = OPAS_PATENT_ID

class OPASLogger:
    def __init__(self, log_dir: str = None):
        self.log_dir = log_dir or os.path.expanduser("~/.opas/logs")
        os.makedirs(self.log_dir, exist_ok=True)
        self.audit_file = os.path.join(self.log_dir, f"opas_audit_{datetime.now().strftime('%Y%m%d')}.jsonl")
        self.lock = threading.Lock()
    
    def audit(self, operation: str, details: Dict[str, Any], node_id: str = "local"):
        entry = AuditEntry(
            timestamp=time.time(),
            operation=operation,
            details=details,
            node_id=node_id
        )
        with self.lock:
            with open(self.audit_file, 'a') as f:
                f.write(json.dumps(asdict(entry)) + '\n')
        self._console(f"[OPAS] [{operation}] {details.get('message', '')}")
    
    def _console(self, msg: str):
        print(f"{datetime.now().strftime('%H:%M:%S')} {msg}")


class SmartSync:
    """
    OPAS Smart Sync Engine
    Proprietary adaptive synchronization with intelligent batching.
    """
    
    BATCH_THRESHOLD = 10
    
    def __init__(self, watch_dir: str, logger: OPASLogger):
        self.watch_dir = watch_dir
        self.logger = logger
        self.file_registry: Dict[str, str] = {}
        self.pending_changes: List[FileChange] = []
        self.running = False
        self.watch_thread = None
        self.lock = threading.Lock()
        # Exclude patterns - also exclude parent directories to prevent cross-folder syncing
        self.exclude_patterns = {
            '.git', '__pycache__', '.pyc', '.log', '.zip', 'android/platform', '.opas',
            # Prevent syncing with UI version or other engine folders
            'N.O.Q.C.G.O.E-main', 'nexian_engine_cli', 'GhostAgent', 'agentghost'
        }
    
    def start(self):
        self.running = True
        self._build_initial_registry()
        self.watch_thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.watch_thread.start()
        self.logger.audit("SMART_SYNC_START", {
            "message": f"Watching {self.watch_dir}",
            "files_tracked": len(self.file_registry)
        })
    
    def stop(self):
        self.running = False
    
    def _should_exclude(self, path: str) -> bool:
        for pattern in self.exclude_patterns:
            if pattern in path:
                return True
        return False
    
    def _compute_hash(self, filepath: str) -> str:
        try:
            with open(filepath, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()[:16]
        except:
            return ""
    
    def _build_initial_registry(self):
        for root, dirs, files in os.walk(self.watch_dir):
            dirs[:] = [d for d in dirs if not self._should_exclude(d)]
            for f in files:
                if self._should_exclude(f):
                    continue
                fpath = os.path.join(root, f)
                rel_path = os.path.relpath(fpath, self.watch_dir)
                self.file_registry[rel_path] = self._compute_hash(fpath)
    
    def _watch_loop(self):
        while self.running:
            changes = self._detect_changes()
            if changes:
                with self.lock:
                    self.pending_changes.extend(changes)
                self.logger.audit("CHANGES_DETECTED", {
                    "message": f"Detected {len(changes)} file changes",
                    "changes": [{"path": c.path, "type": c.change_type.value} for c in changes]
                })
            time.sleep(2)
    
    def _detect_changes(self) -> List[FileChange]:
        changes = []
        current_files: Set[str] = set()
        
        for root, dirs, files in os.walk(self.watch_dir):
            dirs[:] = [d for d in dirs if not self._should_exclude(d)]
            for f in files:
                if self._should_exclude(f):
                    continue
                fpath = os.path.join(root, f)
                rel_path = os.path.relpath(fpath, self.watch_dir)
                current_files.add(rel_path)
                
                new_hash = self._compute_hash(fpath)
                old_hash = self.file_registry.get(rel_path, "")
                
                if not old_hash:
                    changes.append(FileChange(
                        path=rel_path,
                        change_type=ChangeType.ADDED,
                        new_hash=new_hash,
                        size=os.path.getsize(fpath)
                    ))
                    self.file_registry[rel_path] = new_hash
                elif new_hash != old_hash:
                    changes.append(FileChange(
                        path=rel_path,
                        change_type=ChangeType.MODIFIED,
                        old_hash=old_hash,
                        new_hash=new_hash,
                        size=os.path.getsize(fpath)
                    ))
                    self.file_registry[rel_path] = new_hash
        
        for rel_path in list(self.file_registry.keys()):
            if rel_path not in current_files:
                changes.append(FileChange(
                    path=rel_path,
                    change_type=ChangeType.REMOVED,
                    old_hash=self.file_registry[rel_path]
                ))
                del self.file_registry[rel_path]
        
        return changes
    
    def get_pending_changes(self) -> List[FileChange]:
        with self.lock:
            changes = self.pending_changes.copy()
            self.pending_changes.clear()
            return changes
    
    def determine_strategy(self, changes: List[FileChange]) -> SyncStrategy:
        if len(changes) > self.BATCH_THRESHOLD:
            self.logger.audit("STRATEGY_SELECTED", {
                "message": f"Batch ZIP strategy ({len(changes)} files > {self.BATCH_THRESHOLD} threshold)",
                "strategy": "batch_zip",
                "file_count": len(changes)
            })
            return SyncStrategy.BATCH_ZIP
        else:
            self.logger.audit("STRATEGY_SELECTED", {
                "message": f"Individual sync strategy ({len(changes)} files)",
                "strategy": "individual",
                "file_count": len(changes)
            })
            return SyncStrategy.INDIVIDUAL
    
    def create_sync_package(self, changes: List[FileChange], strategy: SyncStrategy) -> Tuple[str, Dict[str, Any]]:
        if strategy == SyncStrategy.BATCH_ZIP:
            return self._create_zip_package(changes)
        else:
            return self._create_individual_package(changes)
    
    def _create_zip_package(self, changes: List[FileChange]) -> Tuple[str, Dict[str, Any]]:
        zippath = os.path.join(tempfile.gettempdir(), f"opas_sync_{int(time.time())}.zip")
        manifest = {
            "type": "batch_zip",
            "created_at": time.time(),
            "files": []
        }
        
        with zipfile.ZipFile(zippath, 'w', zipfile.ZIP_DEFLATED) as zf:
            for change in changes:
                if change.change_type == ChangeType.REMOVED:
                    manifest["files"].append({
                        "path": change.path,
                        "action": "remove",
                        "hash": change.old_hash
                    })
                else:
                    fpath = os.path.join(self.watch_dir, change.path)
                    if os.path.exists(fpath):
                        zf.write(fpath, change.path)
                        manifest["files"].append({
                            "path": change.path,
                            "action": "write",
                            "hash": change.new_hash,
                            "size": change.size
                        })
            
            zf.writestr("opas_manifest.json", json.dumps(manifest))
        
        self.logger.audit("ZIP_PACKAGE_CREATED", {
            "message": f"Created sync package: {os.path.basename(zippath)}",
            "size_mb": os.path.getsize(zippath) / (1024*1024),
            "file_count": len(manifest["files"])
        })
        
        return zippath, manifest
    
    def _create_individual_package(self, changes: List[FileChange]) -> Tuple[str, Dict[str, Any]]:
        package = {
            "type": "individual",
            "created_at": time.time(),
            "files": []
        }
        
        for change in changes:
            entry = {
                "path": change.path,
                "action": "remove" if change.change_type == ChangeType.REMOVED else "write",
                "hash": change.new_hash or change.old_hash
            }
            
            if change.change_type != ChangeType.REMOVED:
                fpath = os.path.join(self.watch_dir, change.path)
                if os.path.exists(fpath):
                    with open(fpath, 'rb') as f:
                        entry["content"] = base64.b64encode(f.read()).decode()
                    entry["size"] = change.size
            
            package["files"].append(entry)
        
        self.logger.audit("INDIVIDUAL_PACKAGE_CREATED", {
            "message": f"Created individual sync package",
            "file_count": len(package["files"])
        })
        
        return json.dumps(package), package


class RemoteApply:
    """
    OPAS Remote Apply Engine
    Proprietary autonomous update application with verification.
    """
    
    def __init__(self, target_dir: str, logger: OPASLogger):
        self.target_dir = target_dir
        self.logger = logger
        self.offline_queue: List[Dict[str, Any]] = []
        self.queue_file = os.path.join(os.path.expanduser("~/.opas"), "offline_queue.json")
        os.makedirs(os.path.dirname(self.queue_file), exist_ok=True)
        self._load_queue()
    
    def _load_queue(self):
        if os.path.exists(self.queue_file):
            try:
                with open(self.queue_file, 'r') as f:
                    self.offline_queue = json.load(f)
            except:
                self.offline_queue = []
    
    def _save_queue(self):
        with open(self.queue_file, 'w') as f:
            json.dump(self.offline_queue, f)
    
    def queue_for_offline(self, package: Dict[str, Any]):
        self.offline_queue.append({
            "queued_at": time.time(),
            "package": package
        })
        self._save_queue()
        self.logger.audit("QUEUED_OFFLINE", {
            "message": f"Queued update for offline apply",
            "file_count": len(package.get("files", []))
        })
    
    def process_offline_queue(self) -> int:
        if not self.offline_queue:
            return 0
        
        processed = 0
        for item in self.offline_queue[:]:
            result = self.apply_package(item["package"])
            if result["success"]:
                self.offline_queue.remove(item)
                processed += 1
        
        self._save_queue()
        return processed
    
    def apply_zip_package(self, zippath: str) -> Dict[str, Any]:
        result = {"success": True, "applied": [], "failed": [], "removed": []}
        
        try:
            with zipfile.ZipFile(zippath, 'r') as zf:
                manifest_data = zf.read("opas_manifest.json")
                manifest = json.loads(manifest_data)
                
                for file_info in manifest["files"]:
                    path = file_info["path"]
                    action = file_info["action"]
                    expected_hash = file_info.get("hash", "")
                    
                    target_path = os.path.join(self.target_dir, path)
                    
                    if action == "remove":
                        if os.path.exists(target_path):
                            os.remove(target_path)
                            result["removed"].append(path)
                    else:
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        zf.extract(path, self.target_dir)
                        
                        actual_hash = self._compute_hash(target_path)
                        if actual_hash == expected_hash:
                            result["applied"].append(path)
                        else:
                            result["failed"].append({"path": path, "reason": "hash_mismatch"})
                            result["success"] = False
            
            self.logger.audit("ZIP_PACKAGE_APPLIED", {
                "message": f"Applied ZIP package",
                "applied": len(result["applied"]),
                "removed": len(result["removed"]),
                "failed": len(result["failed"])
            })
            
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
            self.logger.audit("ZIP_APPLY_ERROR", {"message": str(e)})
        
        return result
    
    def apply_package(self, package: Dict[str, Any]) -> Dict[str, Any]:
        result = {"success": True, "applied": [], "failed": [], "removed": []}
        
        for file_info in package.get("files", []):
            path = file_info["path"]
            action = file_info["action"]
            expected_hash = file_info.get("hash", "")
            
            target_path = os.path.join(self.target_dir, path)
            
            try:
                if action == "remove":
                    if os.path.exists(target_path):
                        os.remove(target_path)
                        result["removed"].append(path)
                else:
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    content = base64.b64decode(file_info.get("content", ""))
                    with open(target_path, 'wb') as f:
                        f.write(content)
                    
                    actual_hash = self._compute_hash(target_path)
                    if actual_hash == expected_hash:
                        result["applied"].append(path)
                    else:
                        result["failed"].append({"path": path, "reason": "hash_mismatch"})
            except Exception as e:
                result["failed"].append({"path": path, "reason": str(e)})
        
        if result["failed"]:
            result["success"] = False
        
        self.logger.audit("PACKAGE_APPLIED", {
            "message": f"Applied sync package",
            "applied": len(result["applied"]),
            "removed": len(result["removed"]),
            "failed": len(result["failed"])
        })
        
        return result
    
    def _compute_hash(self, filepath: str) -> str:
        try:
            with open(filepath, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()[:16]
        except:
            return ""
    
    def verify_all_hashes(self, manifest: Dict[str, Any]) -> Dict[str, Any]:
        result = {"verified": [], "mismatched": [], "missing": []}
        
        for file_info in manifest.get("files", []):
            if file_info["action"] == "remove":
                continue
            
            path = file_info["path"]
            expected_hash = file_info.get("hash", "")
            target_path = os.path.join(self.target_dir, path)
            
            if not os.path.exists(target_path):
                result["missing"].append(path)
            else:
                actual_hash = self._compute_hash(target_path)
                if actual_hash == expected_hash:
                    result["verified"].append(path)
                else:
                    result["mismatched"].append({"path": path, "expected": expected_hash, "actual": actual_hash})
        
        self.logger.audit("HASH_VERIFICATION", {
            "message": f"Verified {len(result['verified'])} files",
            "verified": len(result["verified"]),
            "mismatched": len(result["mismatched"]),
            "missing": len(result["missing"])
        })
        
        return result


class AndroidIndependence:
    """
    OPAS Android Independence Layer
    Proprietary standalone operation with seamless reconnection.
    """
    
    def __init__(self, logger: OPASLogger):
        self.logger = logger
        self.is_android = self._detect_android()
        self.is_standalone = False
        self.cached_state: Dict[str, Any] = {}
        self.state_file = os.path.expanduser("~/.opas/android_state.json")
        self.last_master_contact = 0
        self._load_cached_state()
    
    def _detect_android(self) -> bool:
        indicators = [
            os.path.exists("/data/data/com.termux"),
            "ANDROID" in os.environ.get("PREFIX", "").upper(),
            "termux" in sys.executable.lower() if sys.executable else False,
            platform.system() == "Linux" and os.path.exists("/system/build.prop")
        ]
        return any(indicators)
    
    def _load_cached_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    self.cached_state = json.load(f)
            except:
                self.cached_state = {}
    
    def _save_cached_state(self):
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(self.cached_state, f)
    
    def enter_standalone_mode(self):
        if not self.is_standalone:
            self.is_standalone = True
            self.logger.audit("ANDROID_STANDALONE", {
                "message": "Entered standalone mode - operating independently",
                "cached_state_available": bool(self.cached_state)
            })
    
    def exit_standalone_mode(self, master_state: Dict[str, Any]):
        if self.is_standalone:
            self.is_standalone = False
            self.cached_state = master_state
            self._save_cached_state()
            self.last_master_contact = time.time()
            self.logger.audit("ANDROID_RECONNECTED", {
                "message": "Reconnected to master - syncing state",
                "state_keys": list(master_state.keys())
            })
    
    def get_ui_state(self) -> Dict[str, Any]:
        return self.cached_state.get("ui_state", {})
    
    def update_local_state(self, changes: Dict[str, Any]):
        if "ui_state" not in self.cached_state:
            self.cached_state["ui_state"] = {}
        self.cached_state["ui_state"].update(changes)
        self._save_cached_state()
        
        if self.is_standalone:
            self.logger.audit("ANDROID_LOCAL_UPDATE", {
                "message": "Updated local state (standalone)",
                "changes": list(changes.keys())
            })
    
    def should_render_standalone(self) -> bool:
        return self.is_android and self.is_standalone
    
    def get_platform_info(self) -> Dict[str, Any]:
        return {
            "is_android": self.is_android,
            "is_standalone": self.is_standalone,
            "last_master_contact": self.last_master_contact,
            "cached_state_age": time.time() - self.cached_state.get("timestamp", 0) if self.cached_state else -1
        }


class MeshTraversal:
    """
    OPAS Mesh Traversal Engine
    Proprietary AI-driven node navigation and file propagation.
    """
    
    def __init__(self, logger: OPASLogger):
        self.logger = logger
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.node_states: Dict[str, NodeState] = {}
        self.traversal_history: List[Dict[str, Any]] = []
    
    def register_node(self, node_id: str, ip: str, port: int, platform: str, ssh_user: str = None, ssh_port: int = 22):
        # CRITICAL FIX: Remove duplicate nodes with same IP address
        # This prevents multiple registrations of the same device
        nodes_to_remove = []
        for existing_id, existing_info in self.nodes.items():
            if existing_info.get("ip") == ip and existing_info.get("port") == port:
                # Same IP and port - remove old entry
                if existing_id != node_id:
                    nodes_to_remove.append(existing_id)
        
        for old_id in nodes_to_remove:
            del self.nodes[old_id]
            if old_id in self.node_states:
                del self.node_states[old_id]
            self.logger.audit("NODE_DEDUP", {
                "message": f"Removed duplicate node: {old_id} (same IP: {ip})",
                "kept_node": node_id
            })
        
        self.nodes[node_id] = {
            "ip": ip,
            "port": port,
            "platform": platform,
            "ssh_user": ssh_user,
            "ssh_port": ssh_port,
            "registered_at": time.time()
        }
        self.node_states[node_id] = NodeState.ONLINE
        self.logger.audit("NODE_REGISTERED", {
            "message": f"Registered node: {node_id}",
            "ip": ip,
            "platform": platform
        })
    
    def get_online_nodes(self) -> List[str]:
        return [nid for nid, state in self.node_states.items() if state == NodeState.ONLINE]
    
    def traverse_and_push(self, package_path: str, manifest: Dict[str, Any], use_ssh: bool = False) -> Dict[str, Any]:
        """
        ⚠️ DEPRECATED: Prefer unified_sync_authority for file sync.
        This method is kept for compatibility but should use HTTP (use_ssh=False).
        """
        results = {}
        traversal_id = f"trav_{int(time.time())}"
        
        self.logger.audit("MESH_TRAVERSAL_START", {
            "message": f"Starting mesh traversal: {traversal_id}",
            "target_nodes": list(self.nodes.keys()),
            "use_ssh": use_ssh
        })
        
        for node_id, node_info in self.nodes.items():
            self.node_states[node_id] = NodeState.SYNCING
            
            result = self._push_to_node(node_id, node_info, package_path, manifest, use_ssh)
            results[node_id] = result
            
            self.node_states[node_id] = NodeState.ONLINE if result["success"] else NodeState.ERROR
            
            self.traversal_history.append({
                "traversal_id": traversal_id,
                "node_id": node_id,
                "timestamp": time.time(),
                "success": result["success"],
                "method": "ssh" if use_ssh else "http"
            })
        
        self.logger.audit("MESH_TRAVERSAL_COMPLETE", {
            "message": f"Mesh traversal complete: {traversal_id}",
            "results": {nid: r["success"] for nid, r in results.items()}
        })
        
        return results
    
    def _push_to_node(self, node_id: str, node_info: Dict[str, Any], package_path: str, manifest: Dict[str, Any], use_ssh: bool) -> Dict[str, Any]:
        if use_ssh and node_info.get("ssh_user"):
            return self._push_via_ssh(node_id, node_info, package_path, manifest)
        else:
            return self._push_via_http(node_id, node_info, package_path, manifest)
    
    def _push_via_ssh(self, node_id: str, node_info: Dict[str, Any], package_path: str, manifest: Dict[str, Any]) -> Dict[str, Any]:
        import subprocess
        
        ip = node_info["ip"]
        user = node_info["ssh_user"]
        port = node_info.get("ssh_port", 22)
        
        try:
            if package_path.endswith('.zip'):
                remote_path = "/tmp/opas_sync.zip"
                scp_cmd = ["scp", "-P", str(port), "-o", "ConnectTimeout=5", package_path, f"{user}@{ip}:{remote_path}"]
                result = subprocess.run(scp_cmd, capture_output=True, timeout=60)
                
                if result.returncode != 0:
                    return {"success": False, "error": f"SCP failed: {result.stderr.decode()}"}
                
                if node_info["platform"] == "android":
                    extract_cmd = f"cd /data/data/com.termux/files/home && unzip -o {remote_path} && rm {remote_path}"
                else:
                    extract_cmd = f"cd /tmp && unzip -o {remote_path} && rm {remote_path}"
                
                ssh_cmd = ["ssh", "-p", str(port), "-o", "ConnectTimeout=5", f"{user}@{ip}", extract_cmd]
                result = subprocess.run(ssh_cmd, capture_output=True, timeout=120)
                
                if result.returncode != 0:
                    return {"success": False, "error": f"Extract failed: {result.stderr.decode()}"}
            else:
                package = json.loads(package_path)
                for file_info in package.get("files", []):
                    if file_info["action"] == "write":
                        content = base64.b64decode(file_info["content"])
                        remote_file = f"/tmp/opas_{file_info['path'].replace('/', '_')}"
                        
                        with tempfile.NamedTemporaryFile(delete=False) as tmp:
                            tmp.write(content)
                            tmp_path = tmp.name
                        
                        scp_cmd = ["scp", "-P", str(port), tmp_path, f"{user}@{ip}:{remote_file}"]
                        subprocess.run(scp_cmd, capture_output=True, timeout=30)
                        os.unlink(tmp_path)
            
            self.logger.audit("SSH_PUSH_SUCCESS", {
                "message": f"Pushed to {node_id} via SSH",
                "node_id": node_id,
                "ip": ip
            })
            
            return {"success": True, "method": "ssh"}
            
        except Exception as e:
            self.logger.audit("SSH_PUSH_ERROR", {
                "message": f"SSH push failed: {str(e)}",
                "node_id": node_id
            })
            return {"success": False, "error": str(e)}
    
    def _push_via_http(self, node_id: str, node_info: Dict[str, Any], package_path: str, manifest: Dict[str, Any]) -> Dict[str, Any]:
        import urllib.request
        
        ip = node_info["ip"]
        port = node_info["port"]
        
        try:
            if package_path.endswith('.zip'):
                with open(package_path, 'rb') as f:
                    zip_data = base64.b64encode(f.read()).decode()
                
                data = json.dumps({
                    "type": "zip_sync",
                    "data": zip_data,
                    "manifest": manifest
                }).encode()
            else:
                data = package_path.encode() if isinstance(package_path, str) else package_path
            
            url = f"http://{ip}:{port}/opas/apply"
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read())
                
            self.logger.audit("HTTP_PUSH_SUCCESS", {
                "message": f"Pushed to {node_id} via HTTP",
                "node_id": node_id,
                "ip": ip
            })
            
            return {"success": True, "method": "http", "response": result}
            
        except Exception as e:
            self.logger.audit("HTTP_PUSH_ERROR", {
                "message": f"HTTP push failed: {str(e)}",
                "node_id": node_id
            })
            return {"success": False, "error": str(e)}
    
    def trigger_ui_resync(self, node_id: str = None) -> Dict[str, Any]:
        import urllib.request
        
        results = {}
        targets = [node_id] if node_id else list(self.nodes.keys())
        
        for nid in targets:
            if nid not in self.nodes:
                continue
            
            node_info = self.nodes[nid]
            try:
                url = f"http://{node_info['ip']}:{node_info['port']}/ui/resync"
                req = urllib.request.Request(url, method="POST")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    results[nid] = {"success": True}
            except Exception as e:
                results[nid] = {"success": False, "error": str(e)}
        
        self.logger.audit("UI_RESYNC_TRIGGERED", {
            "message": f"Triggered UI resync on {len(targets)} nodes",
            "results": {nid: r["success"] for nid, r in results.items()}
        })
        
        return results


class OPAS:
    """
    OPAS - OmniPlatform AI Substrate
    Main orchestrator for proprietary sync, mesh traversal, and Android independence.
    """
    
    def __init__(self, work_dir: str = None, node_id: str = None):
        self.work_dir = work_dir or os.getcwd()
        self.node_id = node_id or self._generate_node_id()
        
        self.logger = OPASLogger()
        self.smart_sync = SmartSync(self.work_dir, self.logger)
        self.remote_apply = RemoteApply(self.work_dir, self.logger)
        self.android = AndroidIndependence(self.logger)
        self.mesh = MeshTraversal(self.logger)
        
        self.running = False
        self.sync_thread = None
        
        self.logger.audit("OPAS_INIT", {
            "message": f"OPAS initialized: {self.node_id}",
            "version": OPAS_VERSION,
            "patent_id": OPAS_PATENT_ID,
            "work_dir": self.work_dir,
            "is_android": self.android.is_android
        })
    
    def _generate_node_id(self) -> str:
        hostname = socket.gethostname()
        plat = "android" if AndroidIndependence(OPASLogger()).is_android else platform.system().lower()
        return f"opas_{plat}_{hostname}"
    
    def start(self):
        self.running = True
        self.smart_sync.start()
        self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.sync_thread.start()
        
        self.logger.audit("OPAS_START", {
            "message": "OPAS engine started",
            "node_id": self.node_id
        })
    
    def stop(self):
        self.running = False
        self.smart_sync.stop()
        
        self.logger.audit("OPAS_STOP", {
            "message": "OPAS engine stopped"
        })
    
    def _sync_loop(self):
        while self.running:
            changes = self.smart_sync.get_pending_changes()
            
            if changes:
                self._process_changes(changes)
            
            time.sleep(1)
    
    def _process_changes(self, changes: List[FileChange]):
        strategy = self.smart_sync.determine_strategy(changes)
        package_path, manifest = self.smart_sync.create_sync_package(changes, strategy)
        
        online_nodes = self.mesh.get_online_nodes()
        
        if online_nodes:
            results = self.mesh.traverse_and_push(package_path, manifest)
            self.mesh.trigger_ui_resync()
            
            for node_id, result in results.items():
                if not result["success"]:
                    self.logger.audit("SYNC_QUEUED", {
                        "message": f"Queued sync for offline node: {node_id}",
                        "node_id": node_id
                    })
        
        if strategy == SyncStrategy.BATCH_ZIP and os.path.exists(package_path):
            os.unlink(package_path)
    
    def register_node(self, node_id: str, ip: str, port: int, platform: str, ssh_user: str = None, ssh_port: int = 22):
        self.mesh.register_node(node_id, ip, port, platform, ssh_user, ssh_port)
    
    def force_sync(self) -> Dict[str, Any]:
        self.logger.audit("FORCE_SYNC", {
            "message": "Force sync initiated"
        })
        
        all_files = []
        for rel_path, file_hash in self.smart_sync.file_registry.items():
            fpath = os.path.join(self.work_dir, rel_path)
            if os.path.exists(fpath):
                all_files.append(FileChange(
                    path=rel_path,
                    change_type=ChangeType.MODIFIED,
                    new_hash=file_hash,
                    size=os.path.getsize(fpath)
                ))
        
        if all_files:
            strategy = SyncStrategy.BATCH_ZIP
            package_path, manifest = self.smart_sync.create_sync_package(all_files, strategy)
            results = self.mesh.traverse_and_push(package_path, manifest)
            self.mesh.trigger_ui_resync()
            
            if os.path.exists(package_path):
                os.unlink(package_path)
            
            return {"success": True, "files": len(all_files), "results": results}
        
        return {"success": False, "error": "No files to sync"}
    
    def apply_incoming(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if data.get("type") == "zip_sync":
            zip_data = base64.b64decode(data["data"])
            tmp_zip = os.path.join(tempfile.gettempdir(), f"opas_incoming_{int(time.time())}.zip")
            with open(tmp_zip, 'wb') as f:
                f.write(zip_data)
            
            result = self.remote_apply.apply_zip_package(tmp_zip)
            os.unlink(tmp_zip)
            return result
        else:
            return self.remote_apply.apply_package(data)
    
    def get_status(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "version": OPAS_VERSION,
            "patent_id": OPAS_PATENT_ID,
            "running": self.running,
            "files_tracked": len(self.smart_sync.file_registry),
            "nodes_registered": len(self.mesh.nodes),
            "nodes_online": len(self.mesh.get_online_nodes()),
            "android_info": self.android.get_platform_info(),
            "offline_queue_size": len(self.remote_apply.offline_queue)
        }


def create_opas_http_handlers(opas: OPAS):
    def handle_get(path: str) -> Optional[Dict[str, Any]]:
        if path == "/opas/status":
            return opas.get_status()
        if path == "/opas/files":
            return {"files": list(opas.smart_sync.file_registry.keys())}
        if path == "/opas/nodes":
            return {"nodes": opas.mesh.nodes, "states": {k: v.value for k, v in opas.mesh.node_states.items()}}
        return None
    
    def handle_post(path: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if path == "/opas/apply":
            return opas.apply_incoming(data)
        if path == "/opas/register":
            opas.register_node(
                data["node_id"], data["ip"], data["port"], data["platform"],
                data.get("ssh_user"), data.get("ssh_port", 22)
            )
            return {"status": "ok", "registered": data["node_id"]}
        if path == "/opas/force_sync":
            return opas.force_sync()
        if path == "/ui/resync":
            return {"status": "ok", "message": "UI resync triggered"}
        return None
    
    return handle_get, handle_post


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="OPAS - OmniPlatform AI Substrate")
    parser.add_argument("--dir", default=os.getcwd(), help="Working directory")
    parser.add_argument("--node-id", help="Node identifier")
    parser.add_argument("--register", help="Register node: id,ip,port,platform,ssh_user,ssh_port")
    parser.add_argument("--force-sync", action="store_true", help="Force full sync")
    parser.add_argument("--status", action="store_true", help="Show status")
    args = parser.parse_args()
    
    opas = OPAS(work_dir=args.dir, node_id=args.node_id)
    
    if args.register:
        parts = args.register.split(",")
        opas.register_node(
            parts[0], parts[1], int(parts[2]), parts[3],
            parts[4] if len(parts) > 4 else None,
            int(parts[5]) if len(parts) > 5 else 22
        )
    
    if args.status:
        print(json.dumps(opas.get_status(), indent=2))
        sys.exit(0)
    
    if args.force_sync:
        opas.start()
        result = opas.force_sync()
        print(json.dumps(result, indent=2))
        opas.stop()
        sys.exit(0)
    
    opas.start()
    print(f"[OPAS] Running... Press Ctrl+C to stop")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        opas.stop()

