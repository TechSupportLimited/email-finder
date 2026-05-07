import requests
import re
import sys
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
}

url = sys.argv[1] if len(sys.argv) > 1 else 'https://www.pocketgeektechrepair.co.uk/norwich'

r = requests.get(url, headers=HEADERS, timeout=10)
print(f'Status: {r.status_code}')
print(f'URL: {url}')
print()

soup = BeautifulSoup(r.text, 'html.parser')

# 1. Emails in raw HTML
emails_raw = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', r.text)
print(f'[1] Emails in raw HTML: {emails_raw[:10] if emails_raw else "NONE"}')

# 2. Emails in visible text
emails_text = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', soup.get_text())
print(f'[2] Emails in visible text: {emails_text[:10] if emails_text else "NONE"}')

# 3. mailto links
mailtos = [a['href'] for a in soup.find_all('a', href=True) if a['href'].startswith('mailto:')]
print(f'[3] mailto: links: {mailtos[:10] if mailtos else "NONE"}')

# 4. Cloudflare data-cfemail
cf = soup.find_all(attrs={'data-cfemail': True})
print(f'[4] data-cfemail tags: {len(cf)} found')
for tag in cf:
    print(f'    -> {tag["data-cfemail"]}')

# 5. Lines containing @ in raw HTML
at_lines = [l.strip() for l in r.text.splitlines() if '@' in l and len(l.strip()) < 200]
print(f'\n[5] Lines with "@" in HTML ({len(at_lines)} total):')
for line in at_lines[:15]:
    print(f'    {line[:120]}')
