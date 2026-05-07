import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import argparse
from concurrent.futures import ThreadPoolExecutor

BANNER = """
###########################################
#   Email Finder | Designed by YogSec    #
###########################################
"""

VERSION = '1.0'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
}

def decode_cloudflare_email(encoded):
    """Decode Cloudflare-protected email (data-cfemail attribute)."""
    try:
        r = int(encoded[:2], 16)
        return ''.join(chr(int(encoded[i:i+2], 16) ^ r) for i in range(2, len(encoded), 2))
    except Exception:
        return ''

VERBOSE = False

# Function to extract emails from a webpage
def extract_emails(url):
    emails = set()
    try:
        response = requests.get(url, timeout=10, headers=HEADERS)
        if VERBOSE:
            print(f'  [{response.status_code}] {url}')
        if response.status_code == 200:
            html = response.text

            # Decode HTML entities (e.g. &#64; -> @, &amp; -> &)
            from html import unescape
            html_decoded = unescape(html)

            soup = BeautifulSoup(html_decoded, 'html.parser')

            # 1. Extract from visible text
            found_emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', soup.get_text())
            emails.update(found_emails)

            # 2. Extract from mailto: links
            for tag in soup.find_all('a', href=True):
                href = tag['href']
                if href.startswith('mailto:'):
                    email = href[7:].split('?')[0].strip()
                    if '@' in email:
                        emails.add(email)

            # 3. Decode Cloudflare-protected emails (data-cfemail)
            for tag in soup.find_all(attrs={'data-cfemail': True}):
                decoded = decode_cloudflare_email(tag['data-cfemail'])
                if decoded and '@' in decoded:
                    emails.add(decoded)

            # 4. Also search raw HTML for obfuscated patterns like [at], (at), @
            raw_matches = re.findall(r'[a-zA-Z0-9._%+-]+\s*[\[@(]\s*(?:at\s*[\])]?\s*)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html_decoded)
            for m in raw_matches:
                normalized = re.sub(r'\s*[\[(]\s*at\s*[\])]\s*', '@', m, flags=re.IGNORECASE)
                if '@' in normalized:
                    emails.add(normalized.strip())

    except Exception as e:
        if VERBOSE:
            print(f'  [ERROR] {url} — {e}')
        pass
    return emails

# Function to check common pages for contact information
def crawl_emails_from_website(base_url):
    # Always scan the given URL itself first, then common paths from domain root
    from urllib.parse import urlparse
    parsed = urlparse(base_url)
    root_url = f'{parsed.scheme}://{parsed.netloc}'

    urls_to_check = [
        base_url,  # The exact URL provided
        root_url,  # Domain root
        urljoin(root_url, '/contact-us'),
        urljoin(root_url, '/contact'),
        urljoin(root_url, '/about'),
        urljoin(root_url, '/support'),
        urljoin(root_url, '/help'),
        urljoin(root_url, '/team'),
        urljoin(root_url, '/careers'),
        urljoin(root_url, '/jobs'),
        urljoin(root_url, '/faq'),
        urljoin(root_url, '/press'),
        urljoin(root_url, '/media'),
        urljoin(root_url, '/partners'),
        urljoin(root_url, '/company'),
        urljoin(root_url, '/privacy-policy'),
        urljoin(root_url, '/terms'),
        urljoin(root_url, '/legal'),
        urljoin(root_url, '/get-in-touch'),
        urljoin(root_url, '/reach-us'),
        urljoin(root_url, '/enquiries'),
        urljoin(root_url, '/feedback'),
        urljoin(root_url, '/customer-support'),
        urljoin(root_url, '/customer-service'),
        urljoin(root_url, '/connect'),
        urljoin(root_url, '/who-we-are'),
        urljoin(root_url, '/meet-the-team'),
        urljoin(root_url, '/en/contact'),
        urljoin(root_url, '/en/about'),
        urljoin(root_url, '/en/support'),
        urljoin(root_url, '/info/contact'),
        urljoin(root_url, '/company/contact'),
    ]

    all_emails = set()

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(extract_emails, urls_to_check)

    for emails in results:
        all_emails.update(emails)

    return all_emails

# Main function
def main():
    parser = argparse.ArgumentParser(description='Email Finder | Designed by YogSec')
    parser.add_argument('-v', '--version', action='store_true', help='Show version information')
    parser.add_argument('-l', '--list', type=str, help='Provide a file containing list of URLs')
    parser.add_argument('-d', '--domain', type=str, help='Provide a single URL')
    parser.add_argument('-s', '--save', type=str, help='Save output to a file')
    parser.add_argument('--verbose', action='store_true', help='Show detailed request logs')
    args = parser.parse_args()

    if args.verbose:
        global VERBOSE
        VERBOSE = True

    print(BANNER)

    if args.version:
        print(f'Email Finder | Version {VERSION}')
        return

    urls = []

    if args.list:
        with open(args.list, 'r') as file:
            urls = [line.strip() for line in file.readlines()]

    if args.domain:
        urls.append(args.domain.strip())

    all_emails = set()
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(crawl_emails_from_website, [url if url.startswith('http') else 'https://' + url for url in urls])

    for emails in results:
        all_emails.update(emails)

    if args.save:
        with open(args.save, 'w') as output_file:
            for email in all_emails:
                output_file.write(email + '\n')
        print(f'Emails saved to {args.save}')
    else:
        for email in all_emails:
            print(email)

if __name__ == '__main__':
    main()
