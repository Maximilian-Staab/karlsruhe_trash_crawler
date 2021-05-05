from muell.config import config
import json
import os

import arrow
import requests
from bs4 import BeautifulSoup
import psycopg2


WEB_PATH = r"https://web6.karlsruhe.de/service/abfall/akal/akal.php?strasse=RASTATTER%20STRA%C3%9FE&hausnr=77"

TRASH_WHITELIST = [r'Bioabfall', r'Restmüll', r'Wertstoff', r'Papier']


def connect():
    """ Connect to the PostgreSQL database server """
    conn = None
    try:
        # read connection parameters
        params = config()

        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(**params)

        # create a cursor
        cur = conn.cursor()

        # execute a statement
        print('PostgreSQL database version:')
        for trash_type, dates in get_website():
            for date in dates:
                print('sending data')
                cur.execute(
                    f"INSERT INTO dates(trash_type, date) \
                    SELECT id AS trash_type, '{date}' FROM trash_types WHERE name='{trash_type}'")

        # commit pooled inserts
        conn.commit()
        # close the communication with the PostgreSQL
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            print('Database connection closed.')


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


def main():
    payloads = []
    for trash_type, dates in get_website():
        payloads.extend(_create_payload(trash_type, dates))
    print(json.dumps(payloads))


if __name__ == '__main__':
    # main()
    connect()
