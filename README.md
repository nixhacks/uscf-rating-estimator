# USCF Rating Estimator

Author: Sudhakar Gandhi

Disclaimer: This is an unofficial community tool and is not affiliated with, endorsed by, or maintained by US Chess.

Estimate a US Chess (USCF) tournament performance rating and post-event rating change, from the command line or a browser.

## Files

- `app/uscf-rating-estimator.py` — interactive CLI script.
- `web/uscf-rating-estimator.html` — browser version (no install needed).
- `app/uscf-lookup-server.py` — optional local proxy so the HTML page can auto-fetch a player's prior rated games count from a USCF ID (works around a browser CORS restriction; not needed for the CLI script).
- `docs/` — optional place for local reference files or screenshots.

## Usage

### CLI

```bash
./app/uscf-rating-estimator.py
```

You'll be prompted for:
- Opponents' ratings (comma separated)
- Total score (e.g. `2.5`)
- Current rating
- USCF ID (optional — auto-fetches prior rated games) or total prior rated games (optional, manual)

It prints the **Performance Rating** and **Estimated New Rating**.

### HTML

Open `web/uscf-rating-estimator.html` directly in a browser. To enable the USCF ID auto-lookup, first run:

```bash
python3 app/uscf-lookup-server.py
```

and leave it running, then use the "USCF ID" field on the page.

### GitHub Pages

This repo includes a workflow at `.github/workflows/page.yml` that deploys the `web/` folder to GitHub Pages when you push to `main`.

Important: GitHub Pages is static hosting, so the USCF ID auto-lookup will not work there because it depends on the local proxy server (`app/uscf-lookup-server.py`).

## Formulas

Implements the US Chess rating system's standard formula, including the K-factor based on "effective number of games" and the bonus-point rule for over-performance:

$$R_s = R_0 + K(S-E) + \max\left(0,\ K(S-E) - 14\sqrt{\max(m,4)}\right)$$

References:
- [US Chess Rating System (revised Sept 2020)](https://new.uschess.org/sites/default/files/media/documents/the-us-chess-rating-system-revised-september-2020.pdf)
- [Glickman, "Approximating Formulas for the US Chess Rating System"](https://www.glicko.net/ratings/approx.pdf)

### Should I Upload the Two PDF Files?

Short answer: no, they are not required for this project to run.

- Recommended: keep links to the official sources (already in this README), and do not upload local copies.
- Optional: you may place personal reference copies under `docs/` for your own convenience.
- If you upload copies, verify redistribution is allowed under the original document terms.

## Notes / Limitations

- This is not an official US Chess rating calculator; use official US Chess published ratings for tournament/official purposes.
- The USCF ID lookup scrapes the public US Chess MSA player page (not an official API) and may break if that page's format changes.
- Performance Rating is solved numerically (binary search) from the standard winning-expectancy formula, matching the tournament performance rating concept.
- Assumes the player is not in a duplicate-opponent (faced twice) event when applying the bonus rule.

## License

MIT — see [LICENSE](LICENSE).
