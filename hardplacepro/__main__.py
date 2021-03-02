#!/usr/bin/env python
"""Fetch Planet Granite reservations.

"""

from dataclasses import dataclass
from datetime import datetime
from pprint import pprint
import typing as t
import json
import logging
from urllib.parse import urlencode
import re

import click
import dateparser
import urllib3
from bs4 import BeautifulSoup, element

BASEURL = "https://app.rockgympro.com/b/widget/?a=equery"

PARAMS = {
    "credentials": "include",
    "headers": {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:86.0) Gecko/20100101 Firefox/86.0",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
    },
    "referrer": "https://app.rockgympro.com/b/widget/?a=offering&offering_guid=3d2b6cb6c62f4025b4c616a2b77b856f&random=602adc4500203&iframeid=&mode=p",
    "method": "POST",
    "mode": "cors",
}


@dataclass(frozen=True)
class Reservation:
    slot: str
    is_available: bool
    spaces: t.Optional[int]

    @classmethod
    def from_tr(cls, tag: element.Tag) -> "Reservation":
        tds = tag.find_all("td")
        slot = tds[0].getText().strip()
        is_available = tds[1].select_one(".offering-page-event-is-full") is None
        is_available = is_available and "NOT AVAILABLE YET" not in tds[3].text

        spaces = 0
        m = re.search('(\d+)\s+spaces', tds[1].getText())
        if m is not None:
            spaces = int(m[1])

        return cls(slot, is_available, spaces)


def query(ts: datetime) -> t.Sequence[Reservation]:
    http = urllib3.PoolManager()

    fields = {
        "PreventChromeAutocomplete": "",
        "random": "603e65c25539a",
        "iframeid": "",
        "mode": "p",
        "fctrl_1": "offering_guid",
        "offering_guid": "3d2b6cb6c62f4025b4c616a2b77b856f",
        "fctrl_2": "course_guid",
        "course_guid": "",
        "fctrl_3": "limited_to_course_guid_for_offering_guid_3d2b6cb6c62f4025b4c616a2b77b856f",
        "limited_to_course_guid_for_offering_guid_3d2b6cb6c62f4025b4c616a2b77b856f": "",
        "fctrl_4": "show_date",
        "show_date": ts.strftime("%Y-%m-%d"),
        "ftagname_0_pcount-pid-1-1301": "pcount",
        "ftagval_0_pcount-pid-1-1301": "1",
        "ftagname_1_pcount-pid-1-1301": "pid",
        "ftagval_1_pcount-pid-1-1301": "1301",
        "fctrl_5": "pcount-pid-1-1301",
        "pcount-pid-1-1301": "0",
        "ftagname_0_pcount-pid-1-3664346": "pcount",
        "ftagval_0_pcount-pid-1-3664346": "1",
        "ftagname_1_pcount-pid-1-3664346": "pid",
        "ftagval_1_pcount-pid-1-3664346": "3664346",
        "fctrl_6": "pcount-pid-1-3664346",
        "pcount-pid-1-3664346": "0",
        "ftagname_0_pcount-pid-1-3664347": "pcount",
        "ftagval_0_pcount-pid-1-3664347": "1",
        "ftagname_1_pcount-pid-1-3664347": "pid",
        "ftagval_1_pcount-pid-1-3664347": "3664347",
        "fctrl_7": "pcount-pid-1-3664347",
        "pcount-pid-1-3664347": 0,
    }

    r = http.request(
        "POST",
        BASEURL,
        headers=PARAMS["headers"],
        body=urlencode(fields)
    )

    data = r.data.decode("utf-8")
    doc = None
    try:
        doc = json.loads(data)
    except json.decoder.JSONDecodeError:
        print("Failed to decode response", data, len(data))
        return

    html = doc["event_list_html"]
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.find_all("tr")
    return [Reservation.from_tr(row) for row in rows]



def setup(debug):
    if debug:
        level = logging.DEBUG
    else:
        level = logging.WARN

    logging.basicConfig(level=level)
    logging.getLogger("asyncio").level = logging.FATAL

@click.command()
@click.argument("date")
@click.option("--debug", type=bool, default=False, help="Enable debug logging", required=False)
def main(date, debug):
    setup(debug)
    ts = dateparser.parse(date, settings={'PREFER_DATES_FROM': 'future'})
    if ts is None:
        print(f"invalid date: {ts}")
    else:
        print(f"Fetching reservations for {ts}")
        reservations = query(ts)
        for r in reservations:
            fg = "green" if r.is_available else "red"
            click.echo(click.style(f"{r.slot}: {r.is_available}, {r.spaces}", fg=fg))


if __name__ == "__main__":
    main()
