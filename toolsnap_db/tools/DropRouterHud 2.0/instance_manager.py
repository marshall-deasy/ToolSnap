"""
instance_manager.py - Multi-instance coordination for DropRouterHud.

Creates lock files to detect sibling routers and assign stack positions.
Cleans up on exit. Prevents duplicate routers on same folder.
"""

import atexit
import json
import os
import psutil
import time
from pathlib import Path
from typing import List, Tuple


class InstanceManager:
    """
    Manages multi-instance coordination via lock files.
    Each router gets a unique position index for HUD stacking.
    """
    
    LOCK_DIR = Path.home() / ".droprouterhud_locks"
    LOCK_TIMEOUT = 60  # Consider lock stale after 60s without heartbeat
    
    def __init__(self, project_name: str, watch_folder: str):
        self.project_name = project_name
        self.watch_folder = str(Path(watch_folder).resolve())
        self.pid = os.getpid()
        self.lock_file = None
        self.position_index = 0
        
        self.LOCK_DIR.mkdir(exist_ok=True)
        
    def acquire_position(self) -> int:
        """
        Find available position index by checking existing locks.
        Returns: position_index (0-based)
        """
        # Clean stale locks first
        self._clean_stale_locks()
        
        # Check for duplicate (same project + folder)
        existing = self._get_active_locks()
        for lock in existing:
            if (lock.get("project_name") == self.project_name and 
                lock.get("watch_folder") == self.watch_folder):
                # Duplicate detected
                print(f"⚠️  Warning: Another router already monitoring {self.project_name}")
                print(f"   Running both instances. Close the other if unintended.")
        
        # Find next available index
        used_indices = {lock.get("position_index", 0) for lock in existing}
        for i in range(100):  # Support up to 100 instances
            if i not in used_indices:
                self.position_index = i
                break
        
        # Create our lock file
        self.lock_file = self.LOCK_DIR / f"droprouterhud_{self.pid}.json"
        self._write_lock()
        
        # Register cleanup
        atexit.register(self.release)
        
        return self.position_index
    
    def _write_lock(self):
        """Write/update lock file with current state."""
        if not self.lock_file:
            return
            
        lock_data = {
            "pid": self.pid,
            "project_name": self.project_name,
            "watch_folder": self.watch_folder,
            "position_index": self.position_index,
            "last_heartbeat": time.time(),
            "started_at": time.time(),
        }
        
        with open(self.lock_file, "w") as f:
            json.dump(lock_data, f, indent=2)
    
    def heartbeat(self):
        """Update heartbeat timestamp to keep lock alive."""
        if self.lock_file and self.lock_file.exists():
            try:
                with open(self.lock_file, "r") as f:
                    data = json.load(f)
                data["last_heartbeat"] = time.time()
                with open(self.lock_file, "w") as f:
                    json.dump(data, f, indent=2)
            except Exception:
                pass
    
    def release(self):
        """Remove lock file on clean exit."""
        if self.lock_file and self.lock_file.exists():
            try:
                self.lock_file.unlink()
            except Exception:
                pass
    
    def _get_active_locks(self) -> List[dict]:
        """Get all active lock files (excluding our own)."""
        locks = []
        
        for lock_path in self.LOCK_DIR.glob("droprouterhud_*.json"):
            # Skip our own lock
            if lock_path == self.lock_file:
                continue
                
            try:
                with open(lock_path, "r") as f:
                    data = json.load(f)
                
                # Check if process is still alive
                pid = data.get("pid")
                if pid and self._is_process_alive(pid):
                    locks.append(data)
                else:
                    # Dead process, remove stale lock
                    lock_path.unlink()
            except Exception:
                # Corrupted lock file, remove it
                try:
                    lock_path.unlink()
                except Exception:
                    pass
        
        return locks
    
    def _clean_stale_locks(self):
        """Remove lock files for dead processes or with old heartbeats."""
        now = time.time()
        
        for lock_path in self.LOCK_DIR.glob("droprouterhud_*.json"):
            try:
                with open(lock_path, "r") as f:
                    data = json.load(f)
                
                pid = data.get("pid")
                last_heartbeat = data.get("last_heartbeat", 0)
                
                # Remove if process dead or heartbeat stale
                if not self._is_process_alive(pid) or (now - last_heartbeat > self.LOCK_TIMEOUT):
                    lock_path.unlink()
                    
            except Exception:
                # Corrupted, remove it
                try:
                    lock_path.unlink()
                except Exception:
                    pass
    
    @staticmethod
    def _is_process_alive(pid: int) -> bool:
        """Check if a process ID is currently running."""
        if not pid:
            return False
        try:
            return psutil.pid_exists(pid)
        except Exception:
            return False
    
    @classmethod
    def get_all_routers(cls) -> List[Tuple[str, str, int]]:
        """
        Get info about all running routers.
        Returns: List of (project_name, watch_folder, position_index)
        """
        cls.LOCK_DIR.mkdir(exist_ok=True)
        routers = []
        
        for lock_path in cls.LOCK_DIR.glob("droprouterhud_*.json"):
            try:
                with open(lock_path, "r") as f:
                    data = json.load(f)
                
                pid = data.get("pid")
                if pid and cls._is_process_alive(pid):
                    routers.append((
                        data.get("project_name", "Unknown"),
                        data.get("watch_folder", ""),
                        data.get("position_index", 0),
                    ))
            except Exception:
                pass
        
        return sorted(routers, key=lambda x: x[2])  # Sort by position
