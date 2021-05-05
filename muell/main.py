import json
import os

import arrow
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from influxdb import InfluxDBClient

load_dotenv()

WEB_PATH = r"https://web6.karlsruhe.de/service/abfall/akal/akal.php?strasse=RASTATTER%20STRA%C3%9FE&hausnr=77"
PASSWORD = os.environ['PASSWORD']

TRASH_WHITELIST = [r'Bioabfall', r'Restmüll', r'Wertstoff', r'Papier']
INFLUXDB_URL = "192.168.0.152"
INFLUXDB_PORT = "8086"
INFLUXDB_USER = "trash_service"
INFLUXDB_DATABASE = "trash_schedule"

client = InfluxDBClient(host=INFLUXDB_URL,
                        port=INFLUXDB_PORT,
                        username=INFLUXDB_USER,
                        password=PASSWORD,
                        database=INFLUXDB_DATABASE)


def convert_date(some_date):
    return arrow.get(some_date, 'ddd. [den] DD.MM.YYYY', locale='de')


def get_website():
    result = requests.get(WEB_PATH)
    soup = BeautifulSoup(result.content, 'html.parser')

    table = soup.find(id="foo").find('table')
    for row in table.find_all('tr'):
        trash_type, dates = row.find_all('td')[1:3]

        try:
            trash_type = trash_type.string.split(',')[0]
        except AttributeError:
            continue

        trash_type = trash_type.replace('ü', 'ue')
        if trash_type not in TRASH_WHITELIST:
            continue

        dates = list(map(convert_date, list(dates)[1::2]))
        yield trash_type, dates


def _create_payload(trash_type, dates):
    return [
        {
            'measurement': 'trash',
            'time': str(date),
            'tags': {
                'trashType': trash_type
            },
            'fields': {
                "date": str(date)
            }
        }
        for date in dates
    ]


def send_to_influx(client: InfluxDBClient, trash_type: str, dates):
    payloads = []
    for date in dates:
        payloads.append({
            'measurement': 'trash',
            'time': str(date),
            'tags': {
                'trashType': trash_type
            },
            'fields': {
                "date": str(date)
            }
        })
    client.write_points(payloads)


def main():
    payloads = []
    for trash_type, dates in get_website():
        payloads.extend(_create_payload(trash_type, dates))
    print(json.dumps(payloads))


if __name__ == '__main__':
    main()
