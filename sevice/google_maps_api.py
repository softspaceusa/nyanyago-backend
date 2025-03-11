from typing import Union

import googlemaps

API_KEY = "AIzaSyAal05yap1WdDdZrF0KrrqzcdvY3E8-D68"  # TODO: переместить отсюда в `.env`

gmaps = googlemaps.Client(key=API_KEY)


async def get_lat_lon(
    address: str,
) -> tuple:
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


async def get_distance_and_duration(
    from_address: Union[str, dict], to_address: Union[str, dict]
) -> tuple:
    """
    Получает расстояние и время в пути между двумя точками
    Если задавать адреса в виде координат, то вот пример: {"lat": 55.93, "lng": -3.118}.
    Args:
        from_address (Union[str, dict]): Начальная точка. В виде строчного адреса или координат.
        to_address (Union[str, dict]): Конечная точка. В виде строчного адреса или координат.

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
        elif element["status"] == "ZERO_RESULTS":
            return 0, 0
        else:
            raise ValueError(f"Ошибка: {element['status']}")
    else:
        raise ValueError("Нет данных для расчёта расстояния")
