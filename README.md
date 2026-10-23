# Requisio handbook — Hugo version (for comparison)

> **This is a copy of [requisio-ux-demo](https://github.com/saanchi365/requisio-ux-demo), made only to compare website builders.**
> This copy builds the handbook with **Hugo**: https://saanchi365.github.io/requisio-ux-demo-hugo/
> The same design is built with **Docusaurus** in [requisio-ux-demo-docusaurus](https://github.com/saanchi365/requisio-ux-demo-docusaurus).

**Don't add issues, flowcharts or wireframes here.** Everything comes from the main project
(issues, board, flowcharts, wireframes, user documents). On every update it publishes
`handbook-data.json`, and this website is built from that file.

| What | Where |
|---|---|
| The pages (how each tab looks) | `layouts/` — Hugo templates |
| Which pages exist | `content/_content.gotmpl` — one page per feature and tab, made from the data |
| Clicks (slideshow, filters, flowcharts, search) | `static/handbook.js` |
| Look | `static/handbook.css` (the same file as the Docusaurus version) |
| Getting the data | `scripts/prepare_data.py` (the same file as the Docusaurus version) |
| Sample wireframes (only in the copies, because the main project has none yet) | `sample-wireframes/` |

The website rebuilds every hour, on every change here, and with **Actions → Build handbook (Hugo) → Run workflow**.
