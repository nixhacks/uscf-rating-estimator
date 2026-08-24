#!/usr/bin/env python3
"""
USCF Rating Estimator

Author: Sudhakar Gandhi

Estimates a player's tournament performance rating and new post-event
rating using the formulas described in:
  - US Chess Rating System (revised Sept 2020):
    https://new.uschess.org/sites/default/files/media/documents/the-us-chess-rating-system-revised-september-2020.pdf
  - Glickman, "A Comprehensive Guide to Chess Ratings" (approx.pdf):
    https://www.glicko.net/ratings/approx.pdf
"""

import math
import re
import ssl
import sys
import urllib.request

MSA_URL = "https://www.uschess.org/msa/MbrDtlMain.php?{}"


def _ssl_context():
    # macOS python.org builds often lack a working default cert store; prefer certifi's bundle.
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def lookup_prior_games(uscf_id):
    """Fetch the 'Regular' rating games-played count from the public US Chess MSA page.

    Returns a dict: {"found": bool, "games": float|None}.
    'found' is False only when the USCF ID doesn't resolve to a player page.
    'games' is None when the player is established (MSA shows no games count,
    meaning enough games have been played that the cap doesn't apply).
    """
    url = MSA_URL.format(uscf_id)
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=10, context=_ssl_context()) as resp:
        html = resp.read().decode("utf-8", errors="replace")

    if "Could not retrieve data" in html:
        return {"found": False, "games": None}

    match = re.search(r"Regular Rating[^(]*\(Based on (\d+) games\)", html)
    games = float(match.group(1)) if match else None
    return {"found": True, "games": games}


def expected_score(rating, opponent_ratings):
    """Expected score for a player of `rating` against a list of opponent ratings."""
    return sum(1.0 / (1.0 + 10 ** ((ri - rating) / 400.0)) for ri in opponent_ratings)


def performance_rating(opponent_ratings, total_score):
    """Solve for the rating Rp whose expected score against the opponents equals total_score."""
    n = len(opponent_ratings)
    if total_score <= 0:
        return min(opponent_ratings) - 400
    if total_score >= n:
        return max(opponent_ratings) + 400

    lo, hi = -2000.0, 5000.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if expected_score(mid, opponent_ratings) < total_score:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def effective_games(rating, prior_games=None):
    """US Chess 'effective number of games' (N'), capped at 50 and at the player's actual game count."""
    n_star = 50.0 if rating >= 2355 else 50.0 / math.sqrt(0.662 + 0.00000739 * (2569 - rating) ** 2)
    if prior_games is None:
        return n_star
    return min(prior_games, n_star)


BONUS_MULTIPLIER = 14  # B, effective May 1, 2017 per the US Chess rating system document


def new_rating(current_rating, opponent_ratings, total_score, prior_games=None):
    n = effective_games(current_rating, prior_games)
    m = len(opponent_ratings)
    k = 800.0 / (n + m)
    we = expected_score(current_rating, opponent_ratings)
    base_change = k * (total_score - we)

    # Bonus for over-performance, only defined for events of 3+ games (US Chess Section 4.2)
    bonus = 0.0
    if m >= 3:
        m_prime = max(m, 4)
        bonus = max(0.0, base_change - BONUS_MULTIPLIER * math.sqrt(m_prime))

    return current_rating + base_change + bonus


def prompt_float_list(prompt_text):
    raw = input(prompt_text)
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    return [float(p) for p in parts]


def prompt_float(prompt_text):
    return float(input(prompt_text).strip())


def main():
    try:
        opponent_ratings = prompt_float_list("Enter opponents rating: ")
        if not opponent_ratings:
            print("Error: at least one opponent rating is required.")
            sys.exit(1)

        total_score = prompt_float("Enter Total Score: ")
        current_rating = prompt_float("Enter Current Rating: ")

        if total_score < 0 or total_score > len(opponent_ratings):
            print(f"Error: Total Score must be between 0 and {len(opponent_ratings)}.")
            sys.exit(1)

        uscf_id = input("Enter USCF ID (optional, auto-fetches prior rated games): ").strip()
        prior_games = None
        prior_games_resolved = False
        if uscf_id:
            try:
                result = lookup_prior_games(uscf_id)
                if not result["found"]:
                    print("Warning: USCF ID not found; falling back to manual entry.")
                elif result["games"] is None:
                    print(f"USCF ID {uscf_id} is an established player; using uncapped effective games.")
                    prior_games_resolved = True
                else:
                    prior_games = result["games"]
                    prior_games_resolved = True
                    print(f"Found {int(prior_games)} prior rated games for USCF ID {uscf_id}.")
            except OSError as exc:
                print(f"Warning: lookup failed ({exc}); falling back to manual entry.")

        if not prior_games_resolved:
            prior_raw = input("Enter total prior rated games (optional, press Enter if established): ").strip()
            prior_games = float(prior_raw) if prior_raw else None
    except ValueError:
        print("Error: please enter valid numeric values.")
        sys.exit(1)

    perf_rating = performance_rating(opponent_ratings, total_score)
    est_new_rating = new_rating(current_rating, opponent_ratings, total_score, prior_games)

    print()
    print(f"Performance Rating: {round(perf_rating)}")
    print(f"Estimated New rating: {round(est_new_rating)}")


if __name__ == "__main__":
    main()
