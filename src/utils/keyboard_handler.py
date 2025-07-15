"""Keyboard event handling for the throttling application."""

import threading
import logging
from typing import Callable, Dict, Optional

import keyboard

logger = logging.getLogger(__name__)

class KeyboardHandler:
    """Handles keyboard events for controlling the application."""
    
    def __init__(self, config):
        """Initialize keyboard handler."""
        self.callbacks: Dict[str, Callable] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        
    def register_callback(self, key: str, callback: Callable) -> None:
        """Register a callback for a key press."""
        self.callbacks[key] = callback
        
    def _keyboard_listener(self) -> None:
        """Listen for keyboard events in a separate thread."""
        while self._running:
            try:
                event = keyboard.read_event()
                if event.event_type == keyboard.KEY_DOWN:
                    if event.name in self.callbacks:
                        self.callbacks[event.name]()
            except Exception as e:
                logger.error(f"Keyboard error: {e}")
                    
    def start(self) -> None:
        """Start keyboard listener thread."""
        self._running = True
        self._thread = threading.Thread(target=self._keyboard_listener, daemon=True)
        self._thread.start()
        logger.info("Keyboard handler started")
        
    def stop(self) -> None:
        """Stop keyboard listener thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        logger.info("Keyboard handler stopped")