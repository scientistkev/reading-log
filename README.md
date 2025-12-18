# reading-log

This is a place where I track my reading. One day, I might make this into a place where you can
visualize my reading. For now, it's just a collection of `.txt` files.

Enjoy!

Current structure:

```
├── 2025
│   ├── april-articles.txt
│   ├── march-articles.txt
│   └── march-books.txt
├── LICENSE
└── README.md
```

## Changelog

### December 18, 2025

**Fixed: CLI now works with bot-protected websites**

Some websites (like `conversationswithtyler.com`) were returning `403 Forbidden` errors when the CLI tried to fetch their content. This was happening because these sites use JavaScript-based bot detection that blocks simple HTTP requests—even those with browser-like User-Agent headers.

**Changes made:**

1. **Switched from `requests` to `playwright` for fetching URLs**

   - Playwright uses a real headless Chromium browser, which executes JavaScript and passes bot detection checks that block traditional HTTP libraries
   - Added a 2-second wait after page load to allow dynamic content (like transcripts) to render

2. **Improved text extraction logic**

   - Previously, the code would find the _first_ HTML element matching content patterns (`main`, `article`, or divs with classes like `content`, `article`, `post`, `entry`)
   - Problem: Some sites have multiple matching elements, and the first match might be a wrapper with little content while the actual content is in a later match
   - Fix: Now finds _all_ matching elements and selects the one with the most text content
   - Also expanded the pattern to match additional common content classes: `text-block`, `transcript`, `body`

3. **Updated dependencies**
   - Added `playwright>=1.40.0` to `requirements.txt`
   - After installing, run `playwright install chromium` to download the browser binary
