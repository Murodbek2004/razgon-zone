from .user_handlers import router as user_router
from .trading_handlers import router as trading_router
from .admin_handlers import router as admin_router

__all__ = ["user_router", "trading_router", "admin_router"]
