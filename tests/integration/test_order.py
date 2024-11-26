import json
from typing import List, Dict
import pytest
from pydantic import BaseModel, RootModel, TypeAdapter

from config import settings
from const.orders_const import NewSchedule, ReadSchedule, Road, DriveAddresses, Address, NowLocation
from tests.conftest import franchise

#franchise login and password
pytest.login = settings.test_franchise_admin_login
pytest.password = settings.test_franchise_admin_password


"""
def test_create_tariff(franchise):
    new_tariff = {
        "title": "string",
        "description": "string",
        "percent": 4,
        "photo_path": "https://nyanyago.ru/api/v1.0/files/econom.png"
    }

    new_tariff_req = franchise.conn.post("/api/v1.0/franchises/tariff",
                                       json=new_tariff)
    assert new_tariff_req.status_code == 200
    new_post = new_tariff_req.json()
    assert new_tariff_req == new_tariff
"""

@pytest.mark.asyncio
@pytest.mark.dependency()
async def test_create_schedule(franchise):

    new_schedule = NewSchedule(
        title="test_schedule",
        description="Create by pytest",
        id_tariff=4,
        children_count=2,
        duration=30,
        other_parametrs=[],
        week_days=[1],
        roads=[
            Road(
                title="Giga road",
                type_drive=[1],
                week_day=1,
                start_time="16:00",
                end_time="17:00",
                addresses=[DriveAddresses(
                    from_address=Address(
                        address="улица Пушкина дом Колотушкина",
                        location=NowLocation(
                            latitude=36.0,
                            longitude=51.0,
                        )
                    ),
                    to_address=Address(
                        address="улица  Колотушкина дом Пушкина",
                        location=NowLocation(
                            latitude=37.0,
                            longitude=54.0
                        )
                    )
                )]
            )
        ]
    )
    new_schedule_json = new_schedule.model_dump(mode='json')
    schedules_resp = await franchise.conn.post( "/orders/schedule", json=new_schedule_json)
    assert schedules_resp.status_code == 200


@pytest.mark.asyncio
@pytest.mark.dependency()
async def test_get_schedule(franchise):
    def get_schedule(schedules: List[ReadSchedule], title: str) -> ReadSchedule:
        for schedule in schedules:
            if schedule.title == title:
                return schedule
    schedules_resp = await franchise.conn.get("/orders/schedules")
    assert schedules_resp.status_code == 200
    schedules = schedules_resp.json()["schedules"]
    schedules_list = [ReadSchedule(**schedule) for schedule in schedules]
    assert schedules_list
    test_schedule = get_schedule(schedules_list, title="test_schedule")
    pytest.test_schedule_id = test_schedule.id

@pytest.mark.asyncio
@pytest.mark.dependency(depends=["test_create_schedule", "test_get_schedule"])
async def test_delete_schedule(franchise):
    schedules_resp = await franchise.conn.delete(f"/orders/schedule/{pytest.test_schedule_id}")
    assert schedules_resp.status_code == 200
