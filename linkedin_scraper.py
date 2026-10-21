"""Bounded public job reader; standard library only. No login or challenge bypass."""
import argparse
import csv
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import time
from urllib.error import HTTPError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
FIELDS = ['ID', 'Date', 'Company', 'Title', 'Location', 'Description', 'Level',
          'Type', 'Function', 'Industry', 'Link', 'CollectedAt']


class Node:
    def __init__(self, tag='', attrs=()):
        self.tag, self.attrs, self.children = tag, {k: v or '' for k, v in attrs}, []

    def walk(self):
        yield self
        for child in self.children:
            if isinstance(child, Node):
                yield from child.walk()

    def find(self, tag=None, cls=None):
        return next((n for n in self.walk() if (tag is None or n.tag == tag)
                     and (cls is None or cls in n.attrs.get('class', '').split())), None)

    def text(self):
        return ' '.join(' '.join(c.text() if isinstance(c, Node) else c
                                for c in self.children).split())


class Page(HTMLParser):
    VOID = set('area base br col embed hr img input link meta param source track wbr'.split())

    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.root = Node()
        self.stack = [self.root]
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs)
        self.stack[-1].children.append(n)
        if tag not in self.VOID:
            self.stack.append(n)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def text(node):
    return node.text() if node else ''


def job_id(url):
    m = re.search(r'/jobs/view/(?:[^/?#]*-)?(\d+)(?:[/?#]|$)', url)
    return m.group(1) if m else None


class AccessBlocked(RuntimeError):
    pass


class Client:
    def __init__(self, delay):
        self.delay, self.last, self.requests = delay, 0, 0

    def get(self, url):
        time.sleep(max(0, self.delay - (time.monotonic() - self.last)))
        self.requests += 1
        try:
            req = Request(url, headers={'User-Agent': 'PersonalJobReader/1.0',
                                       'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8'})
            with urlopen(req, timeout=30) as response:
                final = response.url
                html = response.read().decode('utf-8', errors='replace')
        except HTTPError as exc:
            if exc.code in (401, 403, 429, 999):
                raise AccessBlocked(f'HTTP {exc.code}: access restricted; no retry.') from exc
            raise
        finally:
            self.last = time.monotonic()
        if any(p in urlparse(final).path.lower() for p in ('/authwall', '/checkpoint', '/login', '/uas/')):
            raise AccessBlocked(f'Authentication/challenge redirect: {final}')
        page = Page(html).root
        title = text(page.find('title')).lower()
        if any(m in title for m in ('security verification', 'security check', 'sign in', 'entrar')):
            raise AccessBlocked(f'Authentication/challenge page: {title}')
        if page.find(cls='g-recaptcha') or page.find(cls='h-captcha'):
            raise AccessBlocked('CAPTCHA detected.')
        return page


def cards(page):
    found = {}
    for node in page.walk():
        if 'base-card' not in node.attrs.get('class', '').split():
            continue
        link = node.find('a', 'base-card__full-link')
        ident = job_id(link.attrs.get('href', '')) if link else None
        if not ident:
            continue
        date = node.find('time')
        found[ident] = dict(ID=ident, Title=text(node.find(cls='base-search-card__title')),
                            Company=text(node.find(cls='base-search-card__subtitle')),
                            Location=text(node.find(cls='job-search-card__location')),
                            Date=date.attrs.get('datetime', '') if date else '',
                            Link=f'https://www.linkedin.com/jobs/view/{ident}/')
    return list(found.values())


def detail(page, card):
    ids = set()
    for n in page.walk():
        if n.tag == 'link' and 'canonical' in n.attrs.get('rel', '').split():
            ids.add(job_id(n.attrs.get('href', '')))
        if n.tag == 'meta' and n.attrs.get('property') == 'og:url':
            ids.add(job_id(n.attrs.get('content', '')))
        urn = n.attrs.get('data-entity-urn', '')
        if urn.startswith('urn:li:jobPosting:'):
            ids.add(urn.rsplit(':', 1)[-1])
    if card['ID'] not in ids:
        raise ValueError('Detail page does not confirm expected job ID.')
    description = text(page.find(cls='show-more-less-html__markup'))
    title = text(page.find('h1'))
    if not title or len(description) < 80:
        raise ValueError('Missing title/description; possible changed layout or access wall.')
    row = dict.fromkeys(FIELDS, '')
    row.update(card)
    row.update(Title=title, Description=description, CollectedAt=datetime.now(timezone.utc).isoformat())
    labels = {'seniority level': 'Level', 'nível de experiência': 'Level',
              'employment type': 'Type', 'tipo de emprego': 'Type',
              'job function': 'Function', 'função': 'Function',
              'industries': 'Industry', 'setores': 'Industry'}
    for n in page.walk():
        if 'description__job-criteria-item' in n.attrs.get('class', '').split():
            label = text(n.find(cls='description__job-criteria-subheader')).lower()
            if label in labels:
                row[labels[label]] = text(n.find(cls='description__job-criteria-text'))
    return row


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--keywords', default='analista de dados')
    p.add_argument('--location', default='Brazil')
    p.add_argument('--limit', type=int, default=10)
    p.add_argument('--max-pages', type=int, default=1)
    p.add_argument('--delay', type=float, default=5)
    p.add_argument('--remote', action='store_true')
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    if not 1 <= args.limit <= 100 or not 1 <= args.max_pages <= 5 or args.delay < 3:
        p.error('limit 1..100; max-pages 1..5; delay >=3 seconds required')
    output = args.output or ROOT / 'output' / datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    output.mkdir(parents=True, exist_ok=False)
    client = Client(args.delay)
    report = dict(status='running', collected=0, requests=0, errors=[], keywords=args.keywords,
                  location=args.location, remote=args.remote, requested=args.limit, max_pages=args.max_pages)
    seen = set()
    try:
        with (output / 'jobs.csv').open('w', encoding='utf-8-sig', newline='') as cf, (output / 'jobs.jsonl').open('w', encoding='utf-8') as jf:
            writer = csv.DictWriter(cf, fieldnames=FIELDS)
            writer.writeheader()
            for page_num in range(args.max_pages):
                params = dict(keywords=args.keywords, location=args.location, start=page_num * 25)
                if args.remote:
                    params['f_WT'] = '2'
                batch = cards(client.get('https://www.linkedin.com/jobs/search/?' + urlencode(params)))
                if not batch:
                    raise ValueError('No public cards found; layout/access may have changed.')
                for card in batch:
                    if card['ID'] in seen:
                        continue
                    seen.add(card['ID'])
                    try:
                        row = detail(client.get(card['Link']), card)
                    except AccessBlocked:
                        raise
                    except Exception as exc:
                        report['errors'].append(dict(id=card['ID'], error=str(exc)))
                        print(f"Skipped {card['ID']}: {exc}", flush=True)
                        if len(report['errors']) >= 3:
                            raise RuntimeError('Three detail failures; stopping for inspection.') from exc
                        continue
                    writer.writerow(row)
                    jf.write(json.dumps(row, ensure_ascii=False) + '\n')
                    cf.flush()
                    jf.flush()
                    report['collected'] += 1
                    print(f"[{report['collected']}/{args.limit}] {row['Company']} | {row['Title']}", flush=True)
                    if report['collected'] >= args.limit:
                        break
                if report['collected'] >= args.limit:
                    break
            report['status'] = 'complete' if report['collected'] == args.limit else 'partial'
    except (Exception, KeyboardInterrupt) as exc:
        report['status'] = 'blocked' if isinstance(exc, AccessBlocked) else 'failed'
        report['errors'].append(dict(error=str(exc) or 'Interrupted'))
        print(f'Stopped: {exc}', flush=True)
    finally:
        report['requests'] = client.requests
        (output / 'run.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"{report['status']}: {report['collected']} jobs; results: {output}", flush=True)
    return 0 if report['status'] == 'complete' else 1


if __name__ == '__main__':
    raise SystemExit(main())
