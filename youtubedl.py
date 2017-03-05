# -*- coding: utf-8 -*-
from resources.lib.libraries import control
import xbmc,xbmcgui
import threading
import heapq

try:
    from YDStreamExtractor import getVideoInfo
    from YDStreamExtractor import mightHaveVideo

except Exception:
    print 'importing Error. You need youtubedl module which is in official xbmc.org'
    xbmc.executebuiltin("XBMC.Notification(LiveStreamsPro,Please [COLOR yellow]install Youtube-dl[/COLOR] module ,10000,"")")


class PriorityQueue:
    def __init__(self):
        self._queue = []
        self._count = 0
        self._cv = threading.Condition()

    def put(self, item, priority):
        with self._cv:
            heapq.heappush(self._queue, (-priority, self._count, item))
            self._count += 1
            self._cv.notify()

    def get(self):
        with self._cv:
            while len(self._queue) == 0:
                self._cv.wait()
            self._count -= 1
            return heapq.heappop(self._queue)[-1]


class Queue:
    def __init__(self):
        self.queue = PriorityQueue()
        self.items = []

    def isEmpty(self):
        return self.items == []

    def enqueue(self, item):
        t = threading.Thread(target=resolve, args=(self.queue, item, len(self.items),))
        t.start()
        self.items.insert(0,t)

    def dequeue(self):
        self.items.pop()
        return self.queue.get()

    def size(self):
        return len(self.items)


def queueItems(items):
    queue = Queue()
    items.reverse()

    try:
        queue.enqueue(items.pop())
        queue.enqueue(items.pop())
    except IndexError:
        pass

    # while len(items) > 0:
    count = 0
    while not queue.isEmpty():
        try:
            item = queue.dequeue()
            control.log('[YOUTUBE.DL] SUCCESS: %s' % item['url'])
            yield count, item
        except IndexError as e:
            control.log('[YOUTUBE.DL] ERROR: %s' % e)
            break
        count += 1
        if len(items):
            queue.enqueue(items.pop())

def resolve(q, item, priority):
    resolved=None
    try:
        resolved=resolveUrl(item['url'])
    except UserWarning as e:
        control.log('[YOUTUBE.DL] WARN: %s' % e)
    except StandardError as e:
        control.log('[YOUTUBE.DL] ERROR: %s' % e)
    finally:
        item['url'] = resolved
        q.put(item, priority)

def resolveUrl(url):
    url=url.encode('utf-8','ignore')
    try:
        info = getVideoInfo(url,quality=3,resolve_redirects=True)
    except ValueError as e:
        raise UserWarning("Youtube_dl error:" % e, e)
    control.log('[YOUTUBE.DL] QUERY: %s INFO %s' % (url, info))
    if info is None:
        raise UserWarning("Missing video info")
    stream_url = None
    for s in info.streams():
        try:
            stream_url = s['xbmc_url']
        except KeyError:
            continue

        if stream_url:
            return stream_url.encode('utf-8','ignore')

    raise UserWarning("Missing stream url")
