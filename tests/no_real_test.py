import aiounittest
import pytest
import requests_mock

from muell import ALL_STREETS_URL, put_streets_in_db
from muell.main import connect, send_trash


class NoRealTest(aiounittest.AsyncTestCase):
    @pytest.mark.skip()
    def test_get_all_streets(self):
        with requests_mock.Mocker() as mock:
            with open('tests/Karlsruhe_ Entsorgungstermine.html') as infile:
                mock.get(ALL_STREETS_URL, text=infile.read())
            connect(put_streets_in_db)

    async def test_schedule(self):
        # with requests_mock.Mocker() as mock:
        #     with open('tests/Karlsruhe_ Entsorgungstermine.html') as infile:
        #         mock.get(ALL_STREETS_URL, text=infile.read())
        await connect(send_trash)
