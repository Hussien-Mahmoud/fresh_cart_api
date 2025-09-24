from .routers_products import router as products_router
from .routers_categories import router as categories_router
from .routers_brands import router as brands_router

__all__ = [
    'products_router',
    'categories_router',
    'brands_router',
]
