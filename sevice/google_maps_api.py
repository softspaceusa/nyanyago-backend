from typing import Union

import googlemaps

API_KEY = "AIzaSyAal05yap1WdDdZrF0KrrqzcdvY3E8-D68"  # TODO: переместить отсюда в `.env`

gmaps = googlemaps.Client(key=API_KEY)


def get_lat_lon(
    address: str,
) -> tuple:  # TODO: `get_lat_lon` мб надо сделать асинхронной
    """
    Определяет координаты по адресу

    Args:
        address (str): Адрес.

    Returns:
        tuple: Координаты - lat, lon
    """
    geocode_result = gmaps.geocode(address)
    if geocode_result:
        location = geocode_result[0]["geometry"]["location"]
        return location["lat"], location["lng"]
    else:
        return None, None


def get_distance_and_duration(
    from_address: Union[str, tuple], to_address: Union[str, tuple]
) -> tuple:
    """
    Получает расстояние и время в пути между двумя точками
    Args:
        from_address (Union[str, tuple]): Начальная точка. В виде строчного адреса или координат.
        to_address (Union[str, tuple]): Конечная точка. В виде строчного адреса или координат.

    Returns:
        tuple: Расстояние в метрах, время в секундах
    """
    result = gmaps.distance_matrix(
        origins=from_address, destinations=to_address, mode="driving"  # на машине
    )

    if result["rows"]:
        element = result["rows"][0]["elements"][0]
        if element["status"] == "OK":
            distance = element["distance"]["value"]
            duration = element["duration"]["value"]
            return distance, duration
        else:
            raise ValueError(f"Ошибка: {element['status']}")
    else:
        raise ValueError("Нет данных для расчёта расстояния")
