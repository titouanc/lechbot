from plugins import (UrlShow, Twitter, Topic, Space, Reminder, TechWednesday,
                     TwitterStream, VUBMenu, Ascii, Giphy, Poll)
from ircbot.plugin import HelpPlugin
from config import TWITTER_CONFIG, GIPHY_KEY


CHANS = {
    '#titoufaitdestests': [
        Ascii(),
        Topic(),
        Space(),
        TechWednesday(),
        Reminder(),
        Twitter(TWITTER_CONFIG),
        UrlShow(TWITTER_CONFIG),
        TwitterStream(TWITTER_CONFIG, 'TitouOnRails'),
        VUBMenu(),
        Giphy(GIPHY_KEY),
        HelpPlugin(),
        Poll(),
    ],
    'QUERY': [
        TechWednesday(),
        VUBMenu(),
        HelpPlugin(),
    ],
}

# Rate limit for incoming UrLab notifications in seconds
RATELIMIT = {
    # Hal events
    'bell': 120,
    'passage': 3600,
    'kitchen_move': 3600,
    'doors_stairs': 900,

    # Incubator activity stream
    'Event.a créé': 900,
    'Event.a édité': 900,

    'Project.a créé': 900,
    'Project.a édité': 900,
    'Project.participe à': 900,

    'Task.a ajouté la tâche': 3600,
    'Task.a fini la tâche': 3600,
    'Task.a ré-ajouté la tâche': 3600,

    'wiki.revision': 300,
}

try:
    from local_chanconfig import CHANS, RATELIMIT
except ImportError:
    pass
