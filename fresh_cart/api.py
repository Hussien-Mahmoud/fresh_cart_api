from ninja import NinjaAPI

from catalog.api import products_router, categories_router, brands_router
from users.api import addresses_router
from carts.api import cart_router
from orders.api import orders_router
from payments.api import payments_router


# from ninja_jwt.routers.obtain import obtain_pair_router
# from ninja_extra import exceptions
# from ninja_jwt.controller import NinjaJWTDefaultController
#
# api = NinjaAPI(title="Fresh Cart API", version="1.0.0")
# api.add_router('/token', tags=['Auth'], router=obtain_pair_router)

from ninja_jwt.controller import NinjaJWTDefaultController
from ninja_extra import NinjaExtraAPI

api = NinjaExtraAPI(title="Fresh Cart API", version="1.0.0")
api.register_controllers(NinjaJWTDefaultController)


# Domain routers
api.add_router("", products_router)
api.add_router("", categories_router)
api.add_router("", brands_router)
api.add_router("", addresses_router)
api.add_router("", cart_router)
api.add_router("", orders_router)
api.add_router("", payments_router)
