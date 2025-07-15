"""Administrative privileges verification module."""

import ctypes
import logging


logger = logging.getLogger(__name__)


def is_admin() -> bool:
    """Check if the current process has administrator privileges.
    
    Returns:
        bool: True if running as administrator, False otherwise
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        return False


def ensure_admin_privileges() -> None:
    """Ensure the application is running with administrator privileges.
    
    Raises:
        PermissionError: If not running as administrator
    """
    if not is_admin():
        logger.error("Administrator privileges required")
        print("ERROR: This application requires administrator privileges!")
        print("Please run as administrator.")
        raise PermissionError("Administrator privileges required")
    
    logger.info("Administrator privileges verified")