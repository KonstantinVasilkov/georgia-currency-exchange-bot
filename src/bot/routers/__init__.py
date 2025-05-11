"""
Bot routers package initialization.
"""

from src.bot.routers.start import router as start_router
from src.bot.routers.currency import router as currency_router

# List of all routers
routers = [
    start_router,
    currency_router,
]
