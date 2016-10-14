import threading, os, json, requests, sys, traceback
from ircutils import bot

defaultConfig = dict(
    nick="RedditReader",
    subreddit="all",
    server="irc.example.org",
    channels="#botzoo"
)


class Listing(object):
    def __init__(self, children):
        self.items = []
        for item in children:
            if isinstance(item, dict):
                data = item['data']
                item = Item(name=data['name'],
                            url=data['url'],
                            title=data['title'],
                            author=data['author'],
                            created=data['created'],
                            permalink='http://redd.it/{}/'.format(data['id']),
                            over_18=data['over_18'],
                            )
                self.items.append(item)

    def __len__(self):
        return len(self.items)

    def __getitem__(self, i):
        return self.items[i]

    @classmethod
    def get(cls, reddit):
        url = 'https://reddit.com/r/%s/new.json' % reddit
        headers = dict()
        headers['User-Agent'] = "redditreader IRC Bot /u/flare561"
        data = requests.get(url, headers=headers).json()['data']
        return Listing(data['children'])


class Item(object):
    def __init__(self, name, url, title, author, created, permalink, over_18=True):
        self.name = name
        self.url = url
        self.title = title
        self.author = author
        self.created = created
        self.permalink = permalink
        self.over_18 = over_18

    def __str__(self):
        x = u'[%s] %s: %s%s' % (
            self.author, self.title, self.permalink, self.over_18 and u' [NSFW]' or '')
        return x.encode('UTF-8', 'replace')


def scan(subreddit):
    return Listing.get(subreddit).items


class RedditReader(bot.SimpleBot):
    def on_invite(self, event):
        self.join_channel(event.params[0])


def setInterval(interval):
    def decorator(function):
        def wrapper(*args, **kwargs):
            stopped = threading.Event()

            def loop():  # executed in another thread
                while not stopped.wait(interval):  # until stopped
                    function(*args, **kwargs)

            t = threading.Thread(target=loop)
            t.daemon = True  # stop if the program exits
            t.start()
            return stopped

        return wrapper

    return decorator


@setInterval(60.0)
def process_reddit(bot):
    try:
        items = scan(defaultConfig['subreddit'])
        for item in items:
            for key in bot.channels.keys():
                if not item.permalink in bot.scanned_items:
                    bot.send_message(key, str(item))
                    bot.scanned_items.append(item.permalink)
    except:
        print "ERROR", str(sys.exc_info())
        print traceback.print_tb(sys.exc_info()[2])


if __name__ == "__main__":
    s = RedditReader(defaultConfig['nick'].encode('ascii', 'replace'))
    s.connect(defaultConfig['server'].encode('ascii', 'replace'), channel=defaultConfig['channels'].encode('ascii', 'replace'),
              use_ssl=False)
    s.scanned_items = [str(item) for item in scan((defaultConfig['subreddit']))]
    t = process_reddit(s)
    print "Starting"
    s.start()
