import asyncio
import threading
import time
from typing import Callable, Awaitable, AsyncGenerator, Mapping, NewType

import aiohttp as aiohttp
import aiopg
import arrow
import click
import schedule
from bs4 import BeautifulSoup

from muell.config import config

API_PATH = r"https://web6.karlsruhe.de/service/abfall/akal/akal.php"
GRAPHQL = "http://192.168.0.207:9123/v1/graphql"

TRASH_WHITELIST = [r'Bioabfall', r'Restmüll', r'Wertstoff', r'Papier']

UserId = NewType('UserId', int)


async def send_trash(cursor: aiopg.cursor.Cursor, user_id: UserId, params: Mapping[str, str]):
    async for trash_type, dates in get_website(params):
        for date in dates:
            print('sending data')
            await cursor.execute(
                f"Insert INTO dates(trash_type, date, user_id) \
                    SELECT id AS trash_type, '{date}', {user_id} \
                    FROM trash_types WHERE name='{trash_type}' \
                    ON CONFLICT DO NOTHING")


async def connect(
        operation: Callable[[aiopg.cursor.Cursor, UserId, Mapping[str, str]], Awaitable[None]]):
    """ Connect to the PostgreSQL database server """
    # read connection parameters
    params = config()

    # connect to the PostgreSQL server
    print('Connecting to the PostgreSQL database...')
    async with aiopg.connect(**params) as conn:
        async with conn.cursor() as cur:
            # execute a statement
            await cur.execute("SELECT users.id, house_number, streets.name \
                               FROM users, streets WHERE street = streets.id")
            for user in await cur.fetchall():
                if user is None:
                    return
                user_id, street_number, street_name = user
                await operation(cur, user_id, dict(strasse=street_name, hausnr=street_number or ''))


def convert_date(some_date):
    return arrow.get(some_date, 'ddd. [den] DD.MM.YYYY', locale='de')


async def _async_wrapper(iterable) -> AsyncGenerator:
    for it in iterable:
        yield it


async def get_website(params: Mapping[str, str]):
    async with aiohttp.ClientSession() as session:
        async with session.get(API_PATH, params=params) as response:
            soup = BeautifulSoup(await response.content.read(), 'html.parser')

            table = soup.find(id="foo").find('table')
            async for row in _async_wrapper(table.find_all('tr')):
                trash_type, dates = row.find_all('td')[1:3]

                try:
                    trash_type = trash_type.string.split(',')[0]
                except AttributeError:
                    continue

                if trash_type not in TRASH_WHITELIST:
                    continue

                dates = list(map(convert_date, list(dates)[1::2]))
                yield trash_type, dates


def start_task(
        operation: Callable[[aiopg.cursor.Cursor, UserId, Mapping[str, str]], Awaitable[None]]):
    def launcher():
        loop = asyncio.new_event_loop()
        loop.run_until_complete(connect(operation))

    thread = threading.Thread(target=launcher)
    thread.start()
    thread.join()


@click.command()
@click.option('--schedule', 'is_scheduled', is_flag=True,
              help='Enable scheduled runner (run every 1 to 2 weeks).')
def main(is_scheduled):
    if is_scheduled:
        print('Starting scheduled run.')
        schedule.every(1).to(2).weeks.do(lambda: start_task(send_trash))
        while True:
            n = schedule.idle_seconds()
            if n > 0:
                print(f"Waiting for {n / 60 / 60:.0f} Hours ({n / 60 / 60 / 24:.0f} Days).")
                time.sleep(n)
            schedule.run_pending()
    else:
        connect(send_trash)


if __name__ == '__main__':
    main()
