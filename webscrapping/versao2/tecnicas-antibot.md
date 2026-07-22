Bots now make up 51% of all web traffic. Websites know this and they’re fighting back. Anti-bot systems from Cloudflare, Akamai, and DataDome now combine IP reputation, TLS fingerprinting, browser fingerprinting, and behavioral analysis to block scrapers before a single line of HTML is returned. If your scraper keeps getting blocked, this guide explains exactly why and gives you 12 specific techniques to fix it.

Quick Summary: How to Scrape Without Getting Blocked

Rotate IP addresses using residential proxies. Datacenter IPs are easily flagged.
Set complete, browser-like HTTP headers including User-Agent and Referer.
Randomize request timing with variable delays between 2 and 10 seconds.
Use a headless browser with stealth plugins to pass fingerprint checks.
Handle CAPTCHAs automatically as manual solving doesn’t scale.
Match proxy geolocation to the target site’s expected user base.
Use a managed scraping API (like Bright Data’s Web Unlocker) to automate all of the above.
Why Websites Block Web Scrapers
Understanding why you get blocked is the first step to not getting blocked. Detection doesn’t happen after you’ve downloaded a page. It often happens in the first few milliseconds of the connection, before any HTML is served. The most common anti-scraping techniques work in layered combination — and bypassing them requires matching all layers simultaneously.

IP-Based Detection
Every request you make carries a source IP address. Anti-bot systems maintain reputation databases of known datacenter IP ranges (AWS, GCP, Azure, DigitalOcean), previously flagged IPs, and IPs exhibiting high request volume. A single IP firing 500 requests per minute is trivially identified. Datacenter IPs are flagged by default on many high-security sites because no real residential user visits from an AWS data center.

Browser and TLS Fingerprinting
Every HTTPS connection begins with a TLS handshake. During the ClientHello phase, your client broadcasts its supported cipher suites, TLS version, extensions, and elliptic curve preferences, all in plaintext, before any content is exchanged. Anti-bot systems hash this data into a fingerprint (the JA3 or JA4 standard) and compare it against known-bot signatures. Python’s requests library has a distinctive TLS fingerprint that differs from any real browser and is trivially detected by Cloudflare and Akamai.

Beyond TLS, websites detect your browser type through dozens of JavaScript signals: navigator.webdriver, canvas rendering output, WebGL GPU strings, installed fonts, screen resolution, audio context behavior, and plugin lists. Headless Chrome exposes HeadlessChrome in its User-Agent string and leaves navigator.webdriver = true set, which is an immediate detection signal on most major anti-bot platforms.

Behavioral Analysis
Websites don’t just look at individual requests. They watch patterns across an entire session. PerimeterX/HUMAN and similar systems measure inter-request timing, scroll patterns, mouse movement trajectories, click behavior, navigation depth, and session duration. A scraper that fires requests at exactly 1.0-second intervals, never scrolls, never moves a mouse, and jumps directly to deep product pages without visiting a homepage is immediately distinguishable from a human.

CAPTCHAs and JavaScript Challenges
When a site suspects automation but isn’t certain, it issues a challenge. Cloudflare Turnstile, reCAPTCHA v3, and hCaptcha run JavaScript probes that check for automation artifacts. Failing these challenges, or not having JavaScript execution at all, results in a block or infinite redirect loop.

Honeypot Traps
Some sites inject hidden links into their HTML, invisible to real users via CSS (display: none), but fully accessible to scrapers that parse raw HTML. Following these links flags you as a bot instantly. A scraper that blindly follows every <a href> tag in a document will eventually walk into one.

The Top Techniques to Scrape Websites Without Getting Blocked
1. Rotate Your IP Addresses with Proxies
IP rotation is the most fundamental anti-detection technique. Instead of sending all requests from a single IP address, a proxy pool distributes traffic across hundreds or thousands of IPs so no single IP accumulates a suspicious request volume. Learning how to rotate proxies in Python is an essential skill for anyone building a serious scraper.

The basic pattern: route each request through a different proxy endpoint, and implement automatic retry logic when an IP gets blocked.

import requests
from itertools import cycle
import random
import time

proxies = [
    "http://proxy1.example.com:8080",
    "http://proxy2.example.com:8080",
    "http://proxy3.example.com:8080",
]

proxy_pool = cycle(proxies)

def fetch(url):
    proxy = next(proxy_pool)
    try:
        response = requests.get(
            url,
            proxies={"http": proxy, "https": proxy},
            timeout=10
        )
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Proxy {proxy} failed: {e}")
        return None

# Add a random delay between requests to avoid rate limiting
time.sleep(random.uniform(2, 6))
A high-volume operation needs more than simple round-robin rotation. It needs intelligent session management, automatic IP retirement, and geo-targeted selection. That’s why production scrapers use managed proxy infrastructure rather than a static list.

2. Use Residential or Mobile Proxies
Not all proxies are equal. Datacenter proxies vs. residential proxies represent a fundamental trade-off between cost and detection risk. Datacenter proxies route traffic through cloud server IPs: fast, cheap, but immediately identifiable as non-human by any anti-bot system with an ASN blocklist.

Residential proxies route traffic through real ISP-assigned IP addresses tied to actual home and business connections. To a target site, the request looks like it originates from a real user in a specific city on a specific ISP. Mobile proxies go further by routing traffic through real mobile carrier IPs (4G/5G), which are even less likely to be blacklisted because carriers use CGNAT (one IP shared by many real users).

Proxy Type	Detectability	Speed	Best For
Datacenter	High	Very fast	Low-security sites, high volume
ISP/Static Residential	Medium	Fast	Consistent identity, account-based scraping
Residential	Low	Medium	E-commerce, travel, social platforms
Mobile	Very low	Medium	Mobile-specific content, aggressive sites
Bright Data operates a network of 400M+ residential IPs across 195+ countries, the largest ethically-sourced proxy network available. For scenarios where even residential IPs get flagged, 7M+ mobile IPs provide the highest trust signal possible.

3. Set Realistic Request Headers
Python’s requests library sends a bare-minimum set of headers by default. Compared to a real Chrome browser, the difference is immediately obvious:

# What requests sends by default:
User-Agent: python-requests/2.31.0
Accept-Encoding: gzip, deflate
Accept: */*
Connection: keep-alive

# What Chrome 121 actually sends:
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8
Accept-Language: en-US,en;q=0.9
Accept-Encoding: gzip, deflate, br, zstd
Connection: keep-alive
Upgrade-Insecure-Requests: 1
Sec-Fetch-Dest: document
Sec-Fetch-Mode: navigate
Sec-Fetch-Site: none
Sec-Fetch-User: ?1
Sites check Accept, Accept-Language, Accept-Encoding, Sec-Fetch-* headers, and header order to distinguish real browsers from scripts. Set headers that match the actual browser you’re claiming to be, including the Referer header when navigating between pages on the same domain. For a deeper dive, see our guide on HTTP headers for web scraping.

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.google.com/",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "cross-site",
    "Upgrade-Insecure-Requests": "1",
}

response = requests.get(url, headers=headers)
4. Rotate User-Agents
Sending the same User-Agent string on every request is another easy flag. Real users don’t all run Chrome 121 on Windows 10. Build a pool of realistic, recently active User-Agent strings and rotate them. The critical rule: the User-Agent you rotate to must be internally consistent. If you claim to be Chrome on macOS, your Accept-Language and Sec-CH-UA headers should reflect that.

import random

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
]

headers["User-Agent"] = random.choice(user_agents)
Keep your User-Agent pool current. Browser versions from 2021 are themselves a detection signal, as they’re statistically unlikely to represent real traffic in 2026.

5. Manage TLS Fingerprinting
This is the most commonly missed technique and the one that defeats scrapers who have done everything else right.

When Python’s requests library initiates an HTTPS connection, the underlying TLS stack (OpenSSL or similar) sends a ClientHello with a specific combination of cipher suites and extensions. This combination hashes to a JA3 value that is distinctly non-browser. Cloudflare, Akamai, and DataDome check this fingerprint before serving any content, so you can be blocked before your headers are even evaluated.

The fix: use an HTTP client that impersonates a real browser’s TLS stack. curl_cffi is the current standard for Python:

from curl_cffi import requests as curl_requests

# impersonate="chrome121" tells curl_cffi to use Chrome 121's exact
# TLS cipher suites, extensions, and HTTP/2 settings
response = curl_requests.get(
    "https://example.com",
    impersonate="chrome121",
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ...",
    }
)

print(response.status_code)
curl_cffi wraps curl-impersonate, a build of libcurl that mimics real browser TLS fingerprints at the cryptographic level. The critical requirement: your User-Agent must match the browser profile you’re impersonating. Sending a Chrome 121 TLS fingerprint alongside a Firefox User-Agent creates an inconsistency that advanced systems detect.

For production-scale use, Bright Data’s Web Unlocker handles TLS fingerprint matching automatically with no library management required.

6. Use a Headless Browser with Stealth Plugins
When the target site runs JavaScript challenges, you need a real browser. Understanding what a headless browser is and how it works gives you a foundation for this technique. Playwright and Puppeteer automate Chromium, allowing full JavaScript execution, cookie handling, and dynamic content rendering.

The problem: default headless Chrome is trivially detected. It exposes navigator.webdriver = true, a HeadlessChrome User-Agent string, missing browser plugins, and abnormal screen dimensions. Cloudflare’s Turnstile and similar systems run 200+ JavaScript checks and will catch a default Playwright session in milliseconds.

The fix is playwright-stealth, a plugin that patches these detection vectors:

from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # Patches navigator.webdriver, chrome runtime, iframe content windows,
    # media codecs, and other automation artifacts
    stealth_sync(page)

    page.goto("https://example.com")
    print(page.title())
    browser.close()
playwright-stealth handles the most common detection vectors: navigator.webdriver, window.chrome, navigator.plugins, navigator.languages, and permissions API inconsistencies. For Selenium users, undetected-chromedriver is the equivalent, patching ChromeDriver at the binary level.

Important limitation: stealth plugins reduce detection risk but do not eliminate it. Cloudflare Turnstile and Akamai Bot Manager have evolved significantly and can still catch patched headless browsers. For maximum reliability, Bright Data’s Scraping Browser is a pre-hardened browser environment built specifically to pass these checks out of the box, without any plugin configuration.

7. Randomize Request Timing and Behavior
Scrapers that fire requests on a fixed interval, even a generous one, are detectable by timing analysis. Real users don’t visit pages every 2.0 seconds. They read, scroll, click around, pause, and navigate non-linearly.

Use Gaussian (normal) distribution for delays. This produces human-like variation where most delays cluster around a mean but occasionally run long:

import numpy as np
import time
import random

def human_delay(mean=4.0, std=1.5, min_delay=1.0):
    """Generate a human-like delay using normal distribution."""
    delay = np.random.normal(mean, std)
    # Ensure we don't go below minimum
    delay = max(delay, min_delay)
    time.sleep(delay)

# Between page requests
human_delay(mean=4.0, std=1.5)

# Between actions on the same page (faster)
human_delay(mean=1.2, std=0.4)
Beyond timing, simulate realistic session behavior with Playwright: scroll the page incrementally before extracting data, move the mouse to elements before clicking, and vary the entry point of your crawl rather than always navigating directly to the target URL.

# Simulate human scroll behavior before extracting content
page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.3)")
time.sleep(random.uniform(0.8, 2.0))
page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.7)")
time.sleep(random.uniform(0.5, 1.5))
8. Handle CAPTCHAs Automatically
CAPTCHAs are a wall, not a dead end, but manual solving does not scale. For production scraping, you need automated CAPTCHA handling. Reviewing the best CAPTCHA solvers for web scraping will help you choose the right tool for your use case.

The main approaches:

Third-party solver services (2captcha, Anti-Captcha): send the CAPTCHA image or site key to human solvers or AI models, receive the token, inject it into the form.
reCAPTCHA v3 score management: reCAPTCHA v3 runs silently and assigns a risk score. The higher your score, the less likely you are to see a challenge, so good session hygiene (realistic headers, timing, browsing history) keeps scores high.
Managed solutions: Bright Data’s Web Unlocker includes a built-in CAPTCHA solver that handles reCAPTCHA, hCaptcha, and Cloudflare Turnstile transparently with no integration required.
import requests

# With Bright Data Web Unlocker, CAPTCHAs are solved automatically
# before the response is returned. No solver integration needed.
response = requests.get(
    "https://target-site.com/product-page",
    proxies={
        "https": "https://username:password@brd.superproxy.io:33335"
    },
    verify=False  # Web Unlocker uses its own SSL certificate
)

print(response.status_code)  # Returns 200 with fully rendered content
9. Avoid Honeypot Traps
Honeypot links are invisible to real users but visible in the raw HTML. Following them is an instant bot signal.

Detect them before following links by checking CSS visibility:

from bs4 import BeautifulSoup

def is_visible(tag):
    """Return False if the element is hidden via CSS."""
    style = tag.get("style", "")
    if "display:none" in style.replace(" ", "") or
       "visibility:hidden" in style.replace(" ", ""):
        return False
    # Also check for common honeypot class names
    classes = tag.get("class", [])
    honeypot_classes = {"hidden", "invisible", "honeypot", "trap"}
    if honeypot_classes.intersection(set(classes)):
        return False
    return True

soup = BeautifulSoup(html_content, "html.parser")
safe_links = [
    a["href"] for a in soup.find_all("a", href=True)
    if is_visible(a)
]
This doesn’t catch every honeypot, since some are hidden through external CSS classes rather than inline styles. Playwright’s page.is_visible() method is more reliable because it evaluates computed CSS style rather than just inline attributes.

10. Handle Rate Limiting with Exponential Backoff
For HTTP 429 (Too Many Requests) responses, retrying immediately is counterproductive — it accelerates the block. Implement exponential backoff to back off gracefully and resume scraping without triggering a harder ban:

import time
import random
import requests

def fetch_with_backoff(url, headers, proxies, max_retries=5):
    """Retry with exponential backoff on rate limit responses."""
    for attempt in range(max_retries):
        response = requests.get(url, headers=headers, proxies=proxies, timeout=15)

        if response.status_code == 200:
            return response
        elif response.status_code == 429:
            # Respect Retry-After header if present
            retry_after = int(response.headers.get("Retry-After", 2 ** attempt))
            print(f"Rate limited. Waiting {retry_after}s (attempt {attempt + 1})")
            time.sleep(retry_after)
        elif response.status_code in (403, 503):
            # Likely blocked, rotate IP and back off
            print(f"Blocked (HTTP {response.status_code}). Backing off...")
            time.sleep(2 ** attempt + random.uniform(0, 1))
        else:
            response.raise_for_status()

    raise Exception(f"Max retries exceeded for {url}")
11. Match Geographic Context
Many sites serve different content or enforce stricter bot detection based on the geographic origin of requests. A product price scraper targeting a US e-commerce site should route requests through US residential IPs, not German or Singaporean ones. Mismatched geography creates an inconsistency between the request origin and the Accept-Language or locale headers, which behavioral analysis systems can flag.

Bright Data’s proxy network supports targeting by country, state, city, and carrier, allowing your requests to originate from the precise geographic context that the target site expects. You can explore all available proxy IP locations before building your geo-targeting strategy.

12. Tap Into Underlying APIs
Before building a complex scraper, check whether the target site exposes an internal API that its frontend consumes. Open your browser’s developer tools, go to the Network tab, and watch the XHR/Fetch requests as you navigate the site. Many sites, including large e-commerce platforms, load their data from JSON endpoints that are far easier to call directly than parsing HTML.

These internal APIs often have structured JSON responses (no HTML parsing required), lower anti-bot scrutiny than the main rendered page, and pagination parameters that are straightforward to automate.

The tradeoff: internal APIs are undocumented, may change without notice, and may require authentication tokens that need to be obtained via the main site. But when they’re available and stable, they’re the most efficient scraping path available.