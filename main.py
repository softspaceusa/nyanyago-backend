from config import settings
from routers import authentication, files, static_data, chats, drivers, users, chats_websocket, admins, orders, payments
from routers import franchises, orders_socket, mains
from const.dependency import has_access_admin, has_access_franchise, has_access
from const.dependency import BearerTokenAuthBackend, has_access_files
from starlette.middleware.authentication import AuthenticationMiddleware
from tortoise.contrib.fastapi import register_tortoise
from fastapi.responses import JSONResponse
from fastapi import FastAPI, Depends
import uvicorn
from dotenv import load_dotenv
from os import getenv

load_dotenv()

app = FastAPI(title=settings.app_name)


PROTECTED = [Depends(has_access)]
PROTECTED_ADMINS = [Depends(has_access_admin)]
PROTECTED_FRANCHISES = [Depends(has_access_franchise)]
PROTECTED_FILES = [Depends(has_access_files)]
SECRET_KEY = getenv('SECRET_KEY')

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

original_openapi = app.openapi


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = original_openapi().copy()

    openapi_schema["paths"]["/api/v1.0/orders/current-drive-mode/{token}"] = {
        "get": {
            "summary": "WebSocket для режима текущей поездки",
            "description": """
                Этот WebSocket используется водителями для:
                - обновления местоположения в реальном времени,
                - управления статусом поездки (начало, ожидание, завершение),
                - отправки уведомлений клиенту.

                Сообщения могут включать:
                - **lat** и **lon**: координаты местоположения водителя;
                - **type**: тип заказа (например, "order");
                - **flag**: флаг действия (например, "startDrive", "waiting", "isFinish", "drive", "finishDrive");
                - **id_order**: идентификатор заказа;
                - **index_address**: индекс адреса для обновления статуса;

                Типы данных, которые можно отправлять через WebSocket:
                - начать поездку: {"id_order": 0, "lat": 0.0, "lon": 0.0, "type": "order", "flag": "startDrive"}
                - начать ожидание: {"id_order": 0, "lat": 0.0, "lon": 0.0, "index_address": 0, "flag": "waiting", "type": "order"}
                - водитель прибыл на точку: {"id_order": 0, "lat": 0.0, "lon": 0.0, "index_address": 0, "flag": "isFinish", "type": "order"}
                - движение к следующей точке: {"id_order": 0, "lat": 0.0, "lon": 0.0, "to_index_address": 0, "flag": "drive", "type": "order"}
                - завершить поездку: {"id_order": 0, "lat": 0.0, "lon": 0.0, "flag": "finishDrive", "type": "order"}
            """,
            "responses": {
                "101": {
                    "description": '{"status": True, "message": "title_message"}'
                },
                "400": {
                    "description": "Ошибка в параметрах соединения"
                }
            }
        }
    }
    openapi_schema["paths"]["/api/v1.0/orders/search-driver/{token}"] = {
        "get": {
            "summary": "WebSocket для поиска водителя",
            "description": """
                    Этот WebSocket используется клиентами для поиска водителя и отмены заказа.

                    Клиент может отправлять сообщение с флагом "cancel" для отмены активного заказа.
                    Если заказ отменен, водителю отправляется уведомление.
                """,
            "responses": {
                "101": {
                    "description": '{"status": True, "id_status": 3}'
                },
                "400": {
                    "description": "Ошибка в параметрах соединения"
                }
            }
        }
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


register_tortoise(
    app,
    db_url=f"postgres://{getenv('DB_USER')}:{getenv('DB_PASSWORD')}@{getenv('DB_HOST')}:5432/{getenv('DB_NAME')}",
    modules={"models": ["models.authentication_db", "models.files_db", "models.users_db", "models.drivers_db",
                        "models.static_data_db", "models.chats_db", "models.admins_db", "models.orders_db"]},
    generate_schemas=True,
    add_exception_handlers=True
)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", log_level=settings.log_level, port=settings.port,
                ssl_certfile=settings.ssl_certfile, ssl_keyfile=settings.ssl_keyfile)
