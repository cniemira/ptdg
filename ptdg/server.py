import argparse
import asyncio
import logging
import sys

from datetime import datetime
from itertools import chain
from random import random


logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
log = logging.getLogger()


# rather than include a/the lipsum module, here's ~160 words.
lwords = ['a', 'ac', 'accumsan', 'ad', 'adipiscing', 'aenean', 'aliquam',
          'aliquet', 'amet', 'ante', 'aptent', 'arcu', 'at', 'auctor',
          'augue', 'bibendum', 'blandit', 'class', 'commodo', 'condimentum',
          'congue', 'consectetur', 'consequat', 'conubia', 'convallis',
          'curabitur', 'cursus', 'dapibus', 'diam', 'dictum', 'dignissim',
          'dolor', 'donec', 'dui', 'duis', 'efficitur', 'egestas', 'eget',
          'eleifend', 'elementum', 'elit', 'enim', 'erat', 'eros', 'est',
          'et', 'etiam', 'eu', 'euismod', 'ex', 'facilisis', 'fames',
          'faucibus', 'felis', 'fermentum', 'feugiat', 'finibus', 'fringilla',
          'fusce', 'gravida', 'habitant', 'hendrerit', 'himenaeos', 'id',
          'imperdiet', 'in', 'inceptos', 'integer', 'interdum', 'ipsum',
          'justo', 'lacus', 'laoreet', 'lectus', 'leo', 'libero', 'ligula',
          'litora', 'lobortis', 'lorem', 'maecenas', 'magna', 'malesuada',
          'massa', 'mattis', 'mauris', 'maximus', 'metus', 'mi', 'molestie',
          'mollis', 'morbi', 'nam', 'nec', 'neque', 'netus', 'nibh', 'nisi',
          'nisl', 'non', 'nostra', 'nulla', 'nullam', 'nunc', 'odio', 'orci',
          'ornare', 'pellentesque', 'per', 'phasellus', 'porta', 'porttitor',
          'posuere', 'praesent', 'pretium', 'primis', 'proin', 'pulvinar',
          'purus', 'quam', 'quis', 'quisque', 'rhoncus', 'risus', 'rutrum',
          'sagittis', 'sapien', 'scelerisque', 'sed', 'sem', 'semper',
          'senectus', 'sit', 'sociosqu', 'sodales', 'sollicitudin',
          'suscipit', 'suspendisse', 'taciti', 'tellus', 'tempor', 'tempus',
          'tincidunt', 'torquent', 'tortor', 'tristique', 'turpis',
          'ullamcorper', 'ultrices', 'ultricies', 'urna', 'ut', 'varius',
          'vehicula', 'vel', 'velit', 'venenatis', 'vestibulum', 'vitae',
          'vivamus', 'viverra', 'volutpat', 'vulputate']


header_template = """
HTTP/1.1 200 OK
Content-Type: text/plain; version=0.0.4
Content-Length: {length}
Date: {date} GMT
""".strip()


metric_template = """
# HELP {name} Value of {name}
# TYPE {name} {type}
{name}{tag} {value}
""".strip()


def lipsum(n):
    # use reservoir sampling to produce n random words
    result = []
    i = 0
    for item in lwords:
        i += 1
        if len(result) < n:
            result.append(item)
        else:
            p = int(random() * i)
            if p < n:
                result[p] = item
    return result


# https://gist.github.com/kgaughan/2491663
def parse_range(rng):
    parts = rng.split('-')
    if 1 > len(parts) > 2:
        raise ValueError("Bad range: '%s'" % (rng,))
    parts = [int(i) for i in parts]
    start = parts[0]
    end = start if len(parts) == 1 else parts[1]
    if start > end:
        end, start = start, end
    return range(start, end + 1)


def parse_range_list(rngs):
    return sorted(set(chain(*[parse_range(rng) for rng in rngs.split(',')])))


class MetricHandler(object):
    def __init__(self, count=1, name=None, tags=None):
        order = len(str(count))
        self.keyform = "{}_{{:0{}d}}".format(name, order)
        self.count = count + 1
        self.iter = 0
        self.tags = []

        if tags is not None:
            lipsum = self._lipsum(len(tags))
            for t in tags:
                if t.count('='):
                    if not t.endswith('"'):
                        k,v = t.split('=', 1)
                        t = '='.join([k, '"{}"'.format(v)])
                    self.tags.append(t)
                else:
                    self.tags.append('{}="{}"'.format(t, next(lipsum)))
        else:
            self.tags.append(None)

    def _key(self, i):
        return self.keyform.format(i)

    def _lipsum(self, n):
        for word in lipsum(n):
            yield word.strip('?!.,\'').lower()

    @asyncio.coroutine
    def __call__(self, reader, writer):
        self.iter += 1
        laddr = writer.get_extra_info('sockname')
        raddr = writer.get_extra_info('peername')
        data = yield from reader.readline()
        log.info("{} {!r} {}".format(laddr, data, raddr))

        lines = [metric_template.format(name='iteration', value=self.iter,
                                        tag='', type='counter')]
        tags = []
        for tag in self.tags:
            if tag:
                tags.append(tag)
        tag = ''
        if len(tags):
            tag = '{{{}}}'.format(','.join(tags))
        rand = {self._key(i): random() for i in range(1, self.count)}
        lines += [metric_template.format(name=k, value=v, tag=tag,
                                         type='gauge')
                 for k, v in rand.items()]

        body = "\n".join(lines) + "\n"
        date = datetime.now().strftime('%a, %d %b %Y %H:%M:%S')
        headers = header_template.format(length=len(body), date=date)
        response = headers + "\n\n" + body

        writer.write(response.encode())
        yield from writer.drain()
        writer.close()


def main():
    parser = argparse.ArgumentParser(description='PTDG')

    parser.add_argument('-c', action='store', dest='COUNT', type=int,
                        default=1,
                        help='Metric count per listener')
    parser.add_argument('-l', action='store', dest='IADDR', type=str,
                        default='127.0.0.1',
                        help='Listener address')
    parser.add_argument('-n', action='store', dest='NAME', type=str,
                        default='test',
                        help='Name prefix')
    parser.add_argument('-p', action='store', dest='PORTS', type=str,
                        default='9090',
                        help='Port range')
    parser.add_argument('-t', action='append', dest='TAGS',
                        help='One or more complete tags (k=v) or tag names ' +
                             '(with random string values) to add to metrics')

    args = parser.parse_args(sys.argv[1:])
    ports = parse_range_list(args.PORTS)
    loop = asyncio.get_event_loop()

    for port in ports:
        handler = MetricHandler(count=args.COUNT, name=args.NAME,
                                tags=args.TAGS)
        coro = asyncio.start_server(handler, args.IADDR, port, loop=loop)
        loop.run_until_complete(coro)

    loop.run_forever()


if __name__ == '__main__':
    main()
