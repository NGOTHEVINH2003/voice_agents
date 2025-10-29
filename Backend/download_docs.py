import os
import requests
from bs4 import BeautifulSoup

# Danh sách link docs (ví dụ bạn đã có)
DOCS = [
    "https://docs.stripe.com/testing.md",
    "https://docs.stripe.com/api.md",
    "https://docs.stripe.com/payouts.md",
    "https://docs.stripe.com/connect.md",
    "https://docs.stripe.com/currencies.md",
    "https://docs.stripe.com/upgrades.md",
    "https://docs.stripe.com/sdks.md",
    "https://docs.stripe.com/webhooks.md",
    "https://docs.stripe.com/declines.md",
    "https://docs.stripe.com/refunds.md",
    "https://docs.stripe.com/security.md",
    "https://docs.stripe.com/checkout/quickstart.md",
    "https://docs.stripe.com/payments/quickstart.md",
    "https://docs.stripe.com/billing/quickstart.md",
    "https://docs.stripe.com/webhooks/quickstart.md",
    "https://docs.stripe.com/api/events/types.md",
    "https://docs.stripe.com/security/guide.md",
    "https://docs.stripe.com/payments/analytics.md",
    "https://docs.stripe.com/event-destinations.md",
    "https://docs.stripe.com/webhooks/signature.md",
    "https://docs.stripe.com/get-started/account/teams.md",
    "https://docs.stripe.com/api/errors.md",
    "https://docs.stripe.com/api/versioning.md",
]

SAVE_DIR = "data\stripe_docs"
os.makedirs(SAVE_DIR, exist_ok=True)

def download_file(url):
    filename = url.split("/")[-1]
    filepath = os.path.join(SAVE_DIR, filename)

    print(f"⬇️  Downloading: {url}")
    resp = requests.get(url)
    if resp.status_code == 200:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(resp.text)
        print(f"✅ Saved to {filepath}")
    else:
        print(f"❌ Failed ({resp.status_code}) — {url}")

if __name__ == "__main__":
    for url in DOCS:
        download_file(url)
