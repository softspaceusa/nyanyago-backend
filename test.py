# from firebase_dynamic_links import DynamicLinks
# import traceback
#
#
# def generate_fb_link(auth=False, ref=""):
#     try:
#         if auth is True:
#             link = f"https://nyanyago.ru/auth?ref={ref}"
#         else:
#             link = "https://nyanyago.ru"
#         api_key='AIzaSyBzjbCQeCwtYudcuXmlYkeTJy8BYb75KwA'
#         domain='nyago.page.link'
#         dl=DynamicLinks(api_key, domain)
#         params={
#             "androidInfo": {
#                 "androidPackageName": 'com.nyanyago.nanny_client'
#             },
#             "iosInfo": {
#                 "iosBundleId": "com.nyanyago.nanny_client"}
#         }
#         return dl.generate_dynamic_link(link, False, params)
#     except Exception:
#         print(traceback.format_exc())
#
# print(generate_fb_link(True, "test"))



# T = 10
# T1 = 7
# S1 = 3
# S2 = 5
# S = S1 + S2
# M = float(78)
# k = 1
# J = 1
# F1 = 0.03
# Kc = 0.02
# cost_without_cashback = ((T / T1) * S * M * k) / J
# P___ = Kc * cost_without_cashback / 100
# cost_with_cashback = cost_without_cashback + (F1 * cost_without_cashback / 100) + P___
#
# print(cost_with_cashback)
# print(cost_without_cashback)

import googlemaps

# Ваш API ключ Google Maps
API_KEY = 'AIzaSyAal05yap1WdDdZrF0KrrqzcdvY3E8-D68'

# Инициализация клиента Google Maps
gmaps = googlemaps.Client(key=API_KEY)

# Задаем начальные и конечные координаты
origin = (55.685580, 37.676250)
destination = (57.152864, 65.540597) # hour hours   min mins  day  days


def get_time_from_google(durations):
    durations = durations.split(" ")
    times = int(float(durations[0]))
    if durations[1].lower() in ("hour", "hours"):
        times *= 60
    if durations[1].lower() in ("day", "days"):
        times *= 60 * 24
    if durations[1].lower() in ("week", "weeks"):
        times *= 60 * 24 * 7
    if durations[1].lower() in ("month", "months"):
        times *= 60 * 24 * 30
    if len(durations) == 2:
        return times
    if durations[3].lower() in ("hour", "hours"):
        times += 60 * int(float(durations[2]))
    if durations[3].lower() in ("day", "days"):
        times += 60 * 24 * int(float(durations[2]))
    if durations[3].lower() in ("week", "weeks"):
        times += 60 * 24 * 7 * int(float(durations[2]))
    if durations[3].lower() in ("month", "months"):
        times += 60 * 24 * 30 * int(float(durations[2]))
    if len(durations) == 4:
        return times
    if durations[5].lower() in ("hour", "hours"):
        times += 60 * int(float(durations[4]))
    if durations[5].lower() in ("day", "days"):
        times += 60 * 24 * int(float(durations[4]))
    if durations[5].lower() in ("week", "weeks"):
        times += 60 * 24 * 7 * int(float(durations[4]))
    if durations[5].lower() in ("month", "months"):
        times += 60 * 24 * 30 * int(float(durations[4]))
    return times


# Получаем направление между двумя точками
directions_result = gmaps.directions(origin, destination, mode="driving")

# Выводим маршрут
for step in directions_result[0]['legs'][0]['steps']:
    print(step['html_instructions'])

# Если вам нужно получить более подробную информацию, такую как расстояние или время:
distance = directions_result[0]['legs'][0]['distance']['text']
duration = directions_result[0]['legs'][0]['duration']['text']

print(f"Расстояние: {distance}")
print(f"Время в пути: {duration}")
print(f"Время в пути: {get_time_from_google(duration)}")
