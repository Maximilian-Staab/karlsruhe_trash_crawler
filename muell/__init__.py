import requests
from bs4 import BeautifulSoup

ALL_STREETS_URL = 'https://web6.karlsruhe.de/service/abfall/akal/akal.php?von=A&bis=Z&hausnr='


def get_all_streets():
    result = requests.get(ALL_STREETS_URL)
    soup = BeautifulSoup(result.content, 'html.parser')

    table = soup.find("select", {"name": "strasse"})
    for option in table.findAll('option'):
        yield option['value'], option.text


def put_streets_in_db(cursor, connection):
    for id, name in get_all_streets():
        print('sending data')
        cursor.execute(
            f"INSERT INTO streets(karlsruhe_id, name) VALUES ({id}, '{name}')")
    connection.commit()
