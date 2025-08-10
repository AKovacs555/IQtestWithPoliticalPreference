"""Additional features used by the FastAPI backend."""

import io
import json
import os
import time
from typing import List, Optional

from db import get_all_users
from dp import add_laplace

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:  # Pillow not installed
    Image = ImageDraw = ImageFont = None

MIN_BUCKET_SIZE = int(os.getenv("DP_MIN_COUNT", "100"))


def dp_average(
    values: List[float], epsilon: float, min_count: int = MIN_BUCKET_SIZE
) -> Optional[float]:
    """Return the differentially private average of ``values``.

    If ``values`` has fewer than ``min_count`` elements the function returns
    ``None`` to avoid revealing small aggregates. Laplace noise scaled by
    ``epsilon`` is applied to the resulting mean.
    """
    if len(values) < min_count:
        return None
    mean = sum(values) / len(values)
    return add_laplace(mean, epsilon, sensitivity=1 / len(values))


async def leaderboard_by_party(epsilon: float = 1.0) -> List[dict]:
    """Return average IQ by party with differential privacy.

    Parties with fewer than ``min_count`` submissions are omitted to
    preserve privacy. Laplace noise is added using :func:`dp_average`.
    """
    buckets: dict[int, List[float]] = {}
    users = get_all_users()
    for user in users:
        latest = user.get("party_log", [])
        latest = latest[-1]["party_ids"] if latest else []
        parties = latest
        scores = [s.get("iq") for s in (user.get("scores") or [])]
        if not parties or not scores:
            continue
        avg_score = sum(scores) / len(scores)
        for pid in parties:
            buckets.setdefault(pid, []).append(avg_score)

    results = []
    for pid, vals in buckets.items():
        if not vals:
            continue
        true_mean = sum(vals) / len(vals)
        noisy = dp_average(vals, epsilon, min_count=MIN_BUCKET_SIZE)
        if noisy is None:
            continue
        results.append(
            {
                "party_id": pid,
                "avg_iq": noisy,
                "n": len(vals),
                "noise": noisy - true_mean,
            }
        )

    return sorted(results, key=lambda r: r["avg_iq"], reverse=True)


def generate_share_image(user_id: str, iq: float, percentile: float) -> str:
    """Return a URL to a generated result image for social sharing.

    The image is created with :mod:`Pillow` and uploaded to Supabase
    storage if the credentials are configured.  When running locally
    without Supabase, the file is written to ``static/share/`` and the
    relative URL is returned.
    """

    if Image is None:
        # Pillow not installed; unable to generate image
        return ""

    width, height = 1200, 630
    img = Image.new("RGB", (width, height), "#f9fafb")
    draw = ImageDraw.Draw(img)

    title_font = ImageFont.load_default()
    small_font = ImageFont.load_default()

    draw.text((40, 40), "Your IQ Score", font=title_font, fill="#111827")
    draw.text((40, 120), f"IQ {iq:.1f}", font=title_font, fill="#2563eb")
    draw.text((40, 200), f"Top {percentile:.1f}%", font=title_font, fill="#16a34a")
    draw.text(
        (40, 280),
        "Take the test and compare with your party!",
        font=small_font,
        fill="#6b7280",
    )

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_API_KEY")
    bucket = os.getenv("SUPABASE_SHARE_BUCKET", "share")
    filename = f"{user_id}_{int(time.time())}.png"

    if supabase_url and supabase_key:
        try:
            from supabase import create_client

            supa = create_client(supabase_url, supabase_key)
            resp = supa.storage.from_(bucket).upload(
                filename, buf.getvalue(), {"content-type": "image/png"}
            )
            if getattr(resp, "error", None):
                raise Exception(resp.error)
            return supa.storage.from_(bucket).get_public_url(filename)
        except Exception:
            # fall back to writing under static/share below
            pass

    # fallback to local static path
    out_dir = os.path.join(os.path.dirname(__file__), "..", "static", "share")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, filename)
    with open(out_path, "wb") as f:
        f.write(buf.getvalue())
    return f"/static/share/{filename}"


def update_normative_distribution(new_scores: List[float]) -> None:
    """Recompute normative distribution with incoming scores.

    The existing distribution is loaded from ``data/normative_distribution.json``.
    ``new_scores`` are appended and the list is truncated to keep only the most
    recent 5000 values.  This simple rolling window prevents small sample
    skew while remaining lightweight for the demo application.
    """

    if not new_scores:
        return

    path = os.path.join(
        os.path.dirname(__file__), "data", "normative_distribution.json"
    )
    try:
        with open(path) as f:
            dist = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        dist = []

    dist.extend(new_scores)
    if len(dist) > 5000:
        dist = dist[-5000:]

    with open(path, "w") as f:
        json.dump(dist, f)
