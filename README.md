# LECC Meta Product Feed

Automated product feed for Lake Erie Clothing Company's Facebook/Instagram Shopping catalog.

## How it works

1. A GitHub Action runs every 6 hours (and can be triggered manually)
2. It calls the Wix Stores API to fetch all published products
3. It generates a `feed.csv` in Meta's required format
4. The CSV is committed back to this repo and publicly accessible

## Feed URL (use this in Meta Commerce Manager)

```
https://raw.githubusercontent.com/pharleg/lecc-product-feed/main/feed.csv
```

## Setup (one-time)

Add the following secrets in **GitHub → Settings → Secrets and variables → Actions**:

| Secret | Value |
|--------|-------|
| `WIX_API_KEY` | Your Wix Admin API key |
| `WIX_SITE_ID` | `09171792-a043-4b5c-80b6-4f8e917d9c04` |

## Manual trigger

Go to **Actions → Generate Meta Product Feed → Run workflow** to trigger a run immediately.
