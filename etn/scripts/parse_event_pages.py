#!/usr/bin/env python3
import re
import json
import csv
from pathlib import Path
from bs4 import BeautifulSoup

INPUT_DIR = Path(__file__).resolve().parents[1] / 'outputs' / 'event_pages'
OUT_JSON = Path(__file__).resolve().parents[1] / 'outputs' / 'iiba_events_parsed.json'
OUT_CSV = Path(__file__).resolve().parents[1] / 'outputs' / 'iiba_events_parsed.csv'

MONTHS = ('January','February','March','April','May','June','July','August','September','October','November','December')
DATE_RE = re.compile(r'(' + r'|'.join(MONTHS) + r')\s+\d{1,2},\s+\d{4}.*?(?:AM|PM|am|pm)?', re.DOTALL)
TIME_RE = re.compile(r'\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)')


def extract_text(soup):
    return ' '.join(soup.get_text(separator=' ', strip=True).split())


def find_registration_link(soup):
    for a in soup.find_all('a', href=True):
        href = a['href']
        if 'zoom.us' in href or 'register' in href.lower() or 'starchapter' in href.lower() or 'Register' in a.text:
            return href
    return None


def guess_format_and_location(text):
    if 'virtual' in text.lower() or 'zoom' in text.lower():
        return 'Virtual', ''
    m = re.search(r'Location:\s*(.*?)(?:Presented|Hosted|Date:|Time:|Register|Agenda|$)', text, re.IGNORECASE)
    if m:
        loc = m.group(1).strip()
        if loc:
            return ('In-person', loc)
    # look for 📍 marker
    if '📍' in text:
        part = text.split('📍',1)[1].strip()
        maybe = part.split('📌',1)[0].split('Presented',1)[0][:120].strip()
        return ('In-person', maybe)
    return ('Unknown', '')


def extract_title(soup):
    h1 = soup.find('h1')
    if h1 and h1.get_text(strip=True):
        return h1.get_text(strip=True)
    t = soup.title
    if t:
        return t.get_text(strip=True)
    # fallback: first strong or h2
    for tag in ('h2','strong'):
        el = soup.find(tag)
        if el and el.get_text(strip=True):
            return el.get_text(strip=True)
    return ''


def extract_date_text(text):
    m = DATE_RE.search(text)
    if m:
        # try to extract a surrounding substring for time
        start = max(0, m.start()-40)
        end = min(len(text), m.end()+60)
        return text[start:end].strip()
    # fallback search for year
    m2 = re.search(r'\b\d{4}\b', text)
    if m2:
        start = max(0, m2.start()-30)
        end = min(len(text), m2.end()+80)
        return text[start:end].strip()
    return ''


def extract_speakers(soup):
    text = extract_text(soup)
    # look for Presented by / Featuring / Presented
    m = re.search(r'(Presented by|Featuring|Speaker[s]?[:]?)\s*(.*?)\s{2,}', text, re.IGNORECASE)
    if m:
        return m.group(2).strip().split(',')
    # look for 'Presented by' in tags
    for el in soup.find_all():
        txt = el.get_text(' ', strip=True)
        if 'Presented by' in txt or 'Featuring' in txt:
            return [txt]
    return []


def parse_file(path: Path):
    html = path.read_text(encoding='utf-8', errors='ignore')
    soup = BeautifulSoup(html, 'lxml')
    text = extract_text(soup)
    title = extract_title(soup)
    date_text = extract_date_text(text)
    registration = find_registration_link(soup)
    fmt, location = guess_format_and_location(text)
    speakers = extract_speakers(soup)
    # try to find organizer/host
    organizer = ''
    m = re.search(r'(Hosted by|Host:)\s*(.*?)(?:Presented by|Hosted|Organizers|Organizers:|Date:|Time:)', text, re.IGNORECASE)
    if m:
        organizer = m.group(2).strip()
    # canonical link if present
    canonical_el = soup.find('link', rel='canonical')
    canonical = canonical_el['href'] if canonical_el and canonical_el.has_attr('href') else ''

    return {
        'file': str(path.name),
        'title': title,
        'date_text': date_text,
        'location': location,
        'format': fmt,
        'registration_link': registration or '',
        'speakers': [s.strip() for s in speakers if s and s.strip()],
        'organizer': organizer,
        'canonical_link': canonical,
    }


def main():
    files = sorted(INPUT_DIR.glob('*.html'))
    results = []
    for f in files:
        try:
            rec = parse_file(f)
            results.append(rec)
        except Exception as e:
            print('FAILED', f, e)
    # write json
    OUT_JSON.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    # write csv
    keys = ['file','title','date_text','location','format','registration_link','speakers','organizer','canonical_link']
    with OUT_CSV.open('w', newline='', encoding='utf-8') as csvf:
        w = csv.DictWriter(csvf, fieldnames=keys)
        w.writeheader()
        for r in results:
            row = r.copy()
            row['speakers'] = '; '.join(r.get('speakers',[]))
            w.writerow(row)
    print('Parsed', len(results), 'files. Outputs:', OUT_JSON, OUT_CSV)


if __name__ == '__main__':
    main()
