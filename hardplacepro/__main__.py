#!/usr/bin/env python
"""Fetch Planet Granite reservations.

"""

from dataclasses import dataclass
from datetime import datetime
import calendar
import typing as t
import json
import logging
from urllib.parse import urlencode
import re
from functools import cached_property

import click
import dateparser
import urllib3
from bs4 import BeautifulSoup, element

BASEURL = "https://app.rockgympro.com/b/widget/?a=equery"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:86.0) Gecko/20100101 Firefox/86.0",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
}


@dataclass(frozen=True)
class Reservation:
    date: str
    slot: str
    availability: t.Literal["available", "full", "too-early"]
    spaces: t.Optional[int]

    @classmethod
    def from_tr(cls, tag: element.Tag) -> "Reservation":
        tds = tag.find_all("td")

        dow, dom, slot = tds[0].getText().strip().split(",")
        date = f"{dow} {dom}"
        slot = slot.replace("  ", " ")

        spaces = 0

        if tds[1].select_one(".offering-page-event-is-full") is not None:
            availability = "full"
        elif tds[3].select_one(".offering-page-call-for-booking") is not None:
            availability = "too-early"
        else:
            availability = "available"

        m = re.search(r"(\d+)\s+spaces?", tds[1].getText())
        if m is not None:
            spaces = int(m[1])

        return cls(date=date, slot=slot, availability=availability, spaces=spaces)

    @cached_property
    def is_available(self) -> bool:
        return self.availability == "available"


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

    r = http.request("POST", BASEURL, headers=HEADERS, body=urlencode(fields))

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
@click.argument("date", nargs=-1)
@click.option(
    "--debug", type=bool, default=False, help="Enable debug logging", required=False
)
@click.option(
    "--color",
    type=click.Choice(["never", "auto", "always"]),
    default="auto",
    help="Enable debug logging",
    required=False,
)
def main(date, debug, color):
    setup(debug)

    color_output: t.Optional[bool] = None
    if color == "never":
        color_output = False
    if color == "always":
        color_output = True

    daily_reservations = []

    timestamps = [
        dateparser.parse(ts, settings={"PREFER_DATES_FROM": "future"}) for ts in date
    ]
    if not all(timestamps):
        print("One or more invalid timestamps. You figure it out.")
        return None

    for ts in timestamps:
        daily_reservations.append((ts, query(ts)))

    for date, reservations in daily_reservations:
        dow = calendar.day_name[date.weekday()]
        print(date.strftime(f"%Y-%m-%d {dow}"))
        for r in reservations:
            fg = "green" if r.is_available else "red"
            msg = f"\t{r.slot}\t{r.spaces}\t{r.availability}"
            click.echo(click.style(msg, fg=fg), color=color_output)


if __name__ == "__main__":
    main()
