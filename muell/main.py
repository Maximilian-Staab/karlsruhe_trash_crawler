import asyncio
import json
import logging
import os
import threading
import time
from typing import Callable, Awaitable, AsyncGenerator, Mapping, NewType

import aiohttp as aiohttp
import aiopg
import arrow
import click
import schedule
from bs4 import BeautifulSoup
from quart import Quart, request, Response

from muell.config import config

logger = logging.getLogger("Trash-Crawler")

API_PATH = r"https://web6.karlsruhe.de/service/abfall/akal/akal.php"

TRASH_WHITELIST = [r'Bioabfall', r'Restmüll', r'Wertstoff', r'Papier']

UserId = NewType('UserId', int)


async def send_trash(cursor: aiopg.cursor.Cursor, user_id: UserId, params: Mapping[str, str]):
    logger.info("Got params: %s", json.dumps(params, indent=2))
    async for trash_type, dates in get_website(params):
        for date in dates:
            print('sending data')
            await cursor.execute(
                f"Insert INTO dates(trash_type, date, user_id) \
                    SELECT id AS trash_type, '{date}', {user_id} \
                    FROM trash_types WHERE name='{trash_type}' \
                    ON CONFLICT DO NOTHING")


async def resolve_street_id(cursor: aiopg.cursor.Cursor, street_id) -> str:
    await cursor.execute(f"SELECT users.telegram_chat_id, house_number, streets.name \
                                   FROM users, streets WHERE streets.id = {street_id}")
    return await cursor.fetchone()


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
            await cur.execute("SELECT users.telegram_chat_id, house_number, streets.name \
                               FROM users, streets WHERE street = streets.id")
            for user in await cur.fetchall():
                if user is None:
                    return
                user_id, street_number, street_name = user
                await operation(cur, user_id, dict(strasse=street_name, hausnr=street_number or ''))


async def connect_single_user(user_id: UserId, params: Mapping[str, str],
                              operation: Callable[
                                  [aiopg.cursor.Cursor, UserId, Mapping[str, str]], Awaitable[
                                      None]]):
    """ Connect to the PostgreSQL database server """
    # connect to the PostgreSQL server
    print('Connecting to the PostgreSQL database...')
    async with aiopg.connect(**config()) as conn:
        async with conn.cursor() as cur:
            # execute a statement
            await operation(cur, user_id, params)


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


app = Quart(__name__)


@app.route('/search', methods=["POST"])
async def manual_search():
    data = await request.get_json()
    try:
        new_data = data['event']['data']['new']
        street_id = new_data['street']
        user_id = new_data['telegram_chat_id']
        house_number = new_data['house_number']
    except KeyError:
        return "no new data could be extracted", 400

    async with aiopg.connect(**config()) as conn:
        async with conn.cursor() as cur:
            street_name = await resolve_street_id(cur, street_id)
            await connect_single_user(user_id, dict(strasse=street_name, hausnr=house_number or ''),
                                      send_trash)
            return Response("Ok")


@click.command()
@click.option('--schedule', 'is_scheduled', is_flag=True,
              help='Enable scheduled runner (run every 1 to 2 weeks).')
@click.option('--api', is_flag=True,
              help='Enable the api endpoint to trigger updates for a '
                   'specific street and house number.')
def main(is_scheduled, api):
    if api:
        app.run(host=os.getenv("API_HOST"))

    if is_scheduled:
        print('Starting scheduled run.')
        # schedule can't use async, wrap in thread wrapper
        schedule.every(1).to(2).weeks.do(lambda: start_task(send_trash))
        while True:
            n = schedule.idle_seconds()
            if n > 0:
                print(
                    f"Waiting for {n / 60 / 60:.0f} Hours ({n / 60 / 60 / 24:.0f} Days).")
                time.sleep(n)
            schedule.run_pending()
    else:
        connect(send_trash)


if __name__ == '__main__':
    main()
