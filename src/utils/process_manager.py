"""
Process management utilities.

This module provides functionality to find processes, monitor their network
connections, and manage process-related operations.
"""

import psutil
import logging
from typing import Set, List, Optional, Dict, Any
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class ProcessInfo:
    """Information about a process."""
    pid: int
    name: str
    cmdline: List[str]
    cpu_percent: float
    memory_percent: float
    connections: List[Any]
    
    def __str__(self) -> str:
        return f"ProcessInfo(pid={self.pid}, name='{self.name}', cpu={self.cpu_percent}%)"


class ProcessManager:
    """Manager for process-related operations."""
    
    def __init__(self):
        """Initialize the process manager."""
        self._process_cache: Dict[int, ProcessInfo] = {}
        self._cache_timestamp = 0
        self._cache_ttl = 5.0  # Cache for 5 seconds
        
        logger.info("ProcessManager initialized")
    
    def find_process_by_name(self, name_substring: str) -> int:
        """Find a process by name substring.
        
        Args:
            name_substring: Substring to search for in process names
            
        Returns:
            Process ID of the found process
            
        Raises:
            RuntimeError: If no matching process is found
        """
        logger.debug(f"Searching for process with name containing '{name_substring}'")
        
        try:
            for process in psutil.process_iter(['pid', 'name']):
                try:
                    process_info = process.info
                    if name_substring.lower() in process_info['name'].lower():
                        logger.info(f"Found process: {process_info['name']} (PID: {process_info['pid']})")
                        return process_info['pid']
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    # Process might have terminated or we don't have access
                    continue
            
            # If we get here, no process was found
            raise RuntimeError(f"No process matching '{name_substring}' found")
        
        except Exception as e:
            logger.error(f"Error searching for process: {e}")
            raise
    
    def find_all_processes_by_name(self, name_substring: str) -> List[int]:
        """Find all processes matching a name substring.
        
        Args:
            name_substring: Substring to search for in process names
            
        Returns:
            List of process IDs matching the criteria
        """
        logger.debug(f"Searching for all processes with name containing '{name_substring}'")
        
        matching_pids = []
        
        try:
            for process in psutil.process_iter(['pid', 'name']):
                try:
                    process_info = process.info
                    if name_substring.lower() in process_info['name'].lower():
                        matching_pids.append(process_info['pid'])
                        logger.debug(f"Found matching process: {process_info['name']} (PID: {process_info['pid']})")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            logger.info(f"Found {len(matching_pids)} processes matching '{name_substring}'")
            return matching_pids
        
        except Exception as e:
            logger.error(f"Error searching for processes: {e}")
            raise
    
    def get_process_ports(self, pid: int) -> Set[int]:
        """Get all ports used by a specific process.
        
        Args:
            pid: Process ID
            
        Returns:
            Set of port numbers used by the process
        """
        logger.debug(f"Getting ports for process PID: {pid}")
        
        try:
            process = psutil.Process(pid)
            connections = process.net_connections()
            
            ports = set()
            for conn in connections:
                # Add local port
                if conn.laddr:
                    ports.add(conn.laddr.port)
                
                # Add remote port
                if conn.raddr:
                    ports.add(conn.raddr.port)
            
            logger.info(f"Process {pid} is using {len(ports)} ports: {sorted(ports)}")
            return ports
        
        except psutil.NoSuchProcess:
            logger.warning(f"Process {pid} no longer exists")
            return set()
        except psutil.AccessDenied:
            logger.warning(f"Access denied to process {pid}")
            return set()
        except Exception as e:
            logger.error(f"Error getting ports for process {pid}: {e}")
            return set()
    def get_process_info(self, pid: int) -> Optional[ProcessInfo]:
        """Get detailed information about a process.
        
        Args:
            pid: Process ID
            
        Returns:
            ProcessInfo object if process exists, None otherwise
        """
        try:
            process = psutil.Process(pid)
            return ProcessInfo(
                pid=process.pid,
                name=process.name(),
                cmdline=process.cmdline(),
                cpu_percent=process.cpu_percent(),
                memory_percent=process.memory_percent(),
                connections=process.connections()
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            logger.warning(f"Could not get info for process {pid}")
            return None 