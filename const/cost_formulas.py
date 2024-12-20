Vm = 27  # Средняя скорость движения автомобиля за 2024г - км/ч

S1 = 3  # Радиус подачи автомобиля - километры

Kc = 3  # Коэффициент кэшбека - %

Ks = 1  # Коэффициент страховки - %

Kg = 1  # Городской коэффициент - %

T = 3600 / Vm  # Среднее время за километр пути - секунды


def get_total_cost_of_the_trip(*, M: int, S2: float, To: int) -> float:
    """
    Получает полную стоимость поездки

    Args:
        M (int): Тариф - руб/км
        S2 (float): Дистанция поездки из точки A в точку B - метры
        To (int): Ориентировочное время поездки - секунды

    Returns:
        float: Полная стоимость поездки
    """

    S2 /= 1000  # Дистанция в километрах

    try:
        Kh2 = To / (T * S2)  # Коэффициент учёта пробок
    except ZeroDivisionError:
        Kh2 = 1

    if Kh2 <= 1:
        Kh2 = 1
    elif Kh2 >= 2.5:
        Kh2 = 2.5

    S = S1 + S2

    cost_drive = S * M  # Стоимость поездки (чистая)
    cost_insurance = Ks * S2 / 100  # Стоимость страховки
    cost_drive_full = Kh2 * cost_drive * Kg + cost_insurance  # Стоимость поездки (без кэшбека)
    cost_cashback = Kc * cost_drive_full / 100  # Стоимость кэшбека
    return cost_drive_full + cost_cashback
