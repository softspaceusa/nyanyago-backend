from routers import authentication, files, static_data, chats, drivers, users, chats_websocket, admins, orders, payments
from routers import franchises, orders_socket, mains
from const.dependency import has_access_admin, has_access_franchise, has_access
from const.dependency import BearerTokenAuthBackend,has_access_files
from starlette.middleware.authentication import AuthenticationMiddleware
from tortoise.contrib.fastapi import register_tortoise
from fastapi.responses import JSONResponse
from fastapi import FastAPI, Depends
import uvicorn
from dotenv import load_dotenv
from os import getenv

load_dotenv()

app = FastAPI(title="AutoNanny") #, docs_url=None, redoc_url=None)


PROTECTED = [Depends(has_access)]
PROTECTED_ADMINS = [Depends(has_access_admin)]
PROTECTED_FRANCHISES = [Depends(has_access_franchise)]
PROTECTED_FILES = [Depends(has_access_files)]


app.include_router(
    mains.router,
    tags=["Google"]
)


app.include_router(
    authentication.router,
    prefix="/api/v1.0/auth",
    tags=["Authentication"]
)


app.include_router(
    payments.router,
    prefix="/api/v1.0/payments",
    tags=["Payments"]
)


app.include_router(
    users.router,
    prefix="/api/v1.0/users",
    dependencies=PROTECTED,
    tags=["Users"]
)


app.include_router(
    drivers.router,
    prefix="/api/v1.0/drivers",
    dependencies=PROTECTED,
    tags=["Drivers"]
)


app.include_router(
    static_data.router,
    prefix="/api/v1.0/static-data",
    tags=["Static data"]
)


app.include_router(
    chats.router,
    prefix="/api/v1.0/chats",
    dependencies=PROTECTED,
    tags=["Chats"]
)


app.include_router(
    orders.router,
    prefix="/api/v1.0/orders",
    dependencies=PROTECTED,
    tags=["Orders"]
)

app.include_router(
    franchises.router,
    prefix="/api/v1.0/franchises",
    dependencies=PROTECTED_FRANCHISES,
    tags=["Franchises"]
)


app.include_router(
    admins.router,
    prefix="/api/v1.0/admins",
    dependencies=PROTECTED_ADMINS,
    tags=["Admins"]
)



app.add_middleware(AuthenticationMiddleware,
                   backend=BearerTokenAuthBackend(),
                   on_error=lambda conn, exc: JSONResponse({"detail": str(exc)}, status_code=401))


app.include_router(
    files.router,
    prefix="/api/v1.0/files",
    dependencies=PROTECTED_FILES,
    tags=["Files"]

)


app.include_router(
    chats_websocket.router,
    prefix="/api/v1.0/chats",
    tags=["Websocket"]
)


app.include_router(
    orders_socket.router,
    prefix="/api/v1.0/orders",
    tags=["Websocket"]
)


register_tortoise(
    app,
    db_url=f"postgres://{getenv('DB_USER')}:{getenv('DB_PASSWORD')}@{getenv('DB_HOST')}:5432/{getenv('DB_NAME')}",
    modules={"models": ["models.authentication_db", "models.files_db", "models.users_db", "models.drivers_db",
                        "models.static_data_db", "models.chats_db", "models.admins_db", "models.orders_db"]},
    generate_schemas=True,
    add_exception_handlers=True
)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", log_level="debug", port=443,
                ssl_certfile="fullchain.pem", ssl_keyfile="privkey.pem")
