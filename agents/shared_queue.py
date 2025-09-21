#!/usr/bin/env python3
"""
Shared File-Based Message Queue for Agent Communication

Since each pod has separate memory, we use a shared volume/file for A2A communication.
"""

import json
import os
import time
from typing import Dict, List, Any
import threading

class SharedMessageQueue:
    """File-based message queue for inter-agent communication"""
    
    def __init__(self, queue_file: str = "/tmp/agent_messages.json"):
        self.queue_file = queue_file
        self.lock_file = f"{queue_file}.lock"
        self._ensure_queue_file()
        
    def _ensure_queue_file(self):
        """Ensure queue file exists"""
        if not os.path.exists(self.queue_file):
            with open(self.queue_file, 'w') as f:
                json.dump([], f)
    
    def _acquire_lock(self) -> bool:
        """Simple file-based locking"""
        try:
            # Try to create lock file
            with open(self.lock_file, 'x') as f:
                f.write(str(time.time()))
            return True
        except FileExistsError:
            return False
    
    def _release_lock(self):
        """Release file lock"""
        try:
            os.remove(self.lock_file)
        except FileNotFoundError:
            pass
    
    def send_message(self, agent_name: str, message: Dict[str, Any]) -> None:
        """Send message to another agent"""
        msg = {
            'to': agent_name,
            'payload': message,
            'timestamp': time.time(),
            'id': f"{time.time()}_{hash(str(message))}"
        }
        
        # Wait for lock
        while not self._acquire_lock():
            time.sleep(0.1)
        
        try:
            # Read current queue
            with open(self.queue_file, 'r') as f:
                queue = json.load(f)
            
            # Add message
            queue.append(msg)
            
            # Write back
            with open(self.queue_file, 'w') as f:
                json.dump(queue, f, indent=2)
                
            print(f"[SHARED-A2A] Message sent to {agent_name}: {message.get('type', 'unknown')}")
            
        finally:
            self._release_lock()
    
    def get_messages(self, agent_name: str) -> List[Dict[str, Any]]:
        """Get messages for an agent (consuming them)"""
        messages = []
        
        # Wait for lock
        while not self._acquire_lock():
            time.sleep(0.1)
        
        try:
            # Read current queue
            with open(self.queue_file, 'r') as f:
                queue = json.load(f)
            
            # Find messages for this agent
            remaining_queue = []
            for msg in queue:
                if msg['to'] == agent_name:
                    messages.append(msg)
                else:
                    remaining_queue.append(msg)
            
            # Write back remaining messages
            with open(self.queue_file, 'w') as f:
                json.dump(remaining_queue, f, indent=2)
                
            if messages:
                print(f"[SHARED-A2A] {agent_name} received {len(messages)} messages")
            
        finally:
            self._release_lock()
            
        return messages
