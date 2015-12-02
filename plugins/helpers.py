import asyncio
import aiohttp
import aioamqp
import json
from os import path
from datetime import datetime
from logging import getLogger
from config import (INCUBATOR, INCUBATOR_SECRET, SPACEAPI,
                    RMQ_HOST, RMQ_USER, RMQ_PASSWORD,
                    LECHBOT_EVENTS_QUEUE, LECHBOT_NOTIFS_QUEUE,
                    TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)

logger = getLogger(__name__)
TIMEFMT = "%Y-%m-%d %H:%M:%S"


def mkurl(endpoint, host=INCUBATOR):
    url = str(host)
    if url[-1] != '/':
        url += '/'
    return url + endpoint.lstrip('/')


@asyncio.coroutine
def private_api(endpoint, data):
    """Call UrLab incubator private API"""
    data['secret'] = INCUBATOR_SECRET
    response = yield from aiohttp.post(mkurl(endpoint), data=data)
    status_code = response.status
    yield from response.release()
    assert status_code == 200


@asyncio.coroutine
def public_api(endpoint):
    """Call UrLab incubator public API"""
    if not endpoint.startswith('http'):
        if endpoint[-1] != '/':
            endpoint += '/'
        url = mkurl(path.join('api', endpoint.lstrip('/')))
    else:
        url = endpoint
    headers = {'User-agent': "UrLab [LechBot]"}
    response = yield from aiohttp.get(url, headers=headers)
    res = yield from response.json()
    yield from response.release()
    return res


@asyncio.coroutine
def spaceapi():
    res = yield from public_api(SPACEAPI)
    return res


@asyncio.coroutine
def rmq_error_callback(exc):
    logger.error("Error when connecting to RabbitMQ: " + str(exc))


@asyncio.coroutine
def lechbot_event_consume(coroutine):
    try:
        transport, protocol = yield from aioamqp.connect(
            host=RMQ_HOST, login=RMQ_USER, password=RMQ_PASSWORD,
            on_error=rmq_error_callback)
        channel = yield from protocol.channel()
        queue = yield from channel.queue_declare(LECHBOT_EVENTS_QUEUE)

        @asyncio.coroutine
        def consume(body, envelope, properties):
            yield from channel.basic_client_ack(envelope.delivery_tag)
            try:
                msg = json.loads(body.decode())
                now = datetime.now()
                msgtime = datetime.strptime(
                    msg.get('time', now.strftime(TIMEFMT)), TIMEFMT)
                if (now - msgtime).total_seconds() < 120:
                    yield from coroutine(msg['name'])
            except:
                logger.exception("Error when consuming message from " +
                                 LECHBOT_EVENTS_QUEUE)

        yield from channel.basic_consume(LECHBOT_EVENTS_QUEUE, callback=consume)
    except aioamqp.AmqpClosedConnection:
        logger.exception("Closed connection")


@asyncio.coroutine
def lechbot_notif(notif_name):
    try:
        transport, protocol = yield from aioamqp.connect(
            host=RMQ_HOST, login=RMQ_USER, password=RMQ_PASSWORD,
            on_error=rmq_error_callback)
        channel = yield from protocol.channel()
        yield from channel.queue_declare(LECHBOT_NOTIFS_QUEUE)
        msg = {'time': datetime.now().strftime(TIMEFMT), 'name': notif_name}
        yield from channel.publish(json.dumps(msg), '', LECHBOT_NOTIFS_QUEUE)
        yield from protocol.close()
        transport.close()
    except aioamqp.AmqpClosedConnection:
        logger.exception("Closed connection")


class AsyncTwitter:
    def __init__(self):
        self.connected = False

    @asyncio.coroutine
    def connect(self):
        auth_query = {
            'auth': aiohttp.BasicAuth(
                TWITTER_CONSUMER_KEY,
                TWITTER_CONSUMER_SECRET
            ),
            'data': {'grant_type': 'client_credentials'},
            'headers': {'Content-Type': "application/x-www-form-urlencoded"},
        }

        auth_url = "https://api.twitter.com/oauth2/token"
        response = yield from aiohttp.post(auth_url, **auth_query)
        data = yield from response.json()
        yield from response.release()
        self.auth = {'Authorization': 'Bearer ' + data['access_token']}
        logger.info("Connected to Twitter")
        self.connected = True

    @asyncio.coroutine
    def query(self, kind, endpoint, **data):
        if not self.connected:
            yield from self.connect()
        if not endpoint.endswith('.json'):
            endpoint += '.json'
        url = "https://api.twitter.com/1.1" + endpoint
        if kind != 'POST':
            q = "&".join("{}={}".format(k, v) for k, v in data.items())
            if q:
                url += '?' + q
            response = yield from aiohttp.get(url, headers=self.auth)
        else:
            response = yield from aiohttp.get(url, headers=self.auth, data=data)
        res = yield from response.json()
        yield from response.release()
        return res

    @asyncio.coroutine
    def status(self, id):
        return self.query('GET', '/statuses/show', id=id)

twitter = AsyncTwitter()
