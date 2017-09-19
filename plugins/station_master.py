import asyncio
import random
from ircbot.persist import Persistent
from ircbot.text import parse_time
from ircbot.plugin import BotPlugin
from .helpers import public_api, mkurl, protect, full_pamela, spaceapi
from datetime import datetime, timedelta
from datetime import time as dtime
from operator import itemgetter
from time import mktime
import itertools
import functools

RULES = {
    'train_morning': [
        {"hour": [9], "minute": [40], "weekday": [1, 2, 3, 4, 5]},
    ],
    'train_evening': [
        {"hour": [17], "minute": [40], "weekday": [1, 2, 3, 4, 5]},
    ],
    'metro': [
        {"hour": [9], "minute": [15], "weekday": [1, 2, 3, 4, 5]},
    ],
    "pair": [
        {"hour": range(24), "minute": range(0, 60, 2), "weekday": range(7)}
    ],
    "impair": [
        {"hour": range(24), "minute": range(1, 60, 2), "weekday": range(7)}
    ]
}

def next_day(weekday, hour=0, minute=0, second=0):
    now = datetime.now()
    d_days = (weekday - now.weekday())%7
    day = now + timedelta(days=d_days)
    if d_days == 0 and dtime(hour, minute, second) < now.time():
        day += timedelta(days=7)
    return day.replace(hour=hour, minute=minute, second=second, microsecond=0)


class StationMaster(BotPlugin):
    def __init__(self):
        self.loop = asyncio.get_event_loop()

    def get_next_instant(self, event_type):
        rules = RULES[event_type]
        expanded_rules = itertools.chain(*(
            itertools.product(rule["weekday"], rule["hour"], rule['minute'])
            for rule in rules
        ))
        expanded_rules = list(expanded_rules)
        days = [next_day(*rule) for rule in expanded_rules]
        return min(days)

    def event(self, event_type):
        self.set_next_call(event_type)
        getattr(self, "run_%s" % event_type)()

    def run_pair(self):
        print("Ceci est une minute paire")

    def run_impair(self):
        print("Ceci est une minute impaire")


    def set_next_call(self, event_type):
        at = self.get_next_instant(event_type)
        dt = (at - datetime.now()).total_seconds()
        self.loop.call_at(self.loop.time() + dt, lambda: self.event(event_type))

    @BotPlugin.on_connect
    def boot(self):
        for event_type in RULES.keys():
            self.set_next_call(event_type)
