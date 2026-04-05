from __future__ import annotations

import os
from dataclasses import dataclass

import numpy as np
import pandas as pd


# ----------------------------
# Config
# ----------------------------


@dataclass
class MinioConfig:
    endpoint: str  # e.g. "localhost:9000"
    access_key: str
    secret_key: str
    bucket: str
    secure: bool = False  # True if https


@dataclass
class GenConfig:
    seed: int = 7

    n_users: int = 50_000
    days: int = 90

    # user activity
    avg_sessions_per_user: float = 4.0  # typical 2..8
    avg_views_per_session: float = 18.0  # typical 10..30

    # taste profile
    min_fav_cats: int = 2
    max_fav_cats: int = 6
    fav_cat_strength: float = 0.82  # 0..1 share of views from favorite categories

    # view time thresholds
    min_view_s: float = 5.0  # ignore shorter than this
    long_view_s: float = 30.0  # long view threshold

    # funnel probabilities (base rates; boosted by taste + long view)
    p_cart_base: float = 0.05  # given a view
    p_buy_given_cart_base: float = 0.30  # given cart

    # boosts
    cart_boost_if_fav: float = 2.5
    cart_boost_if_long: float = 1.8
    buy_boost_if_fav: float = 1.8
    buy_boost_if_long: float = 1.4

    # event weights for IALS confidence
    w_view: float = 1.0
    w_long_view: float = 2.0
    w_cart: float = 6.0
    w_purchase: float = 12.0
    alpha: float = 10.0  # confidence = 1 + alpha * strength_sum


# ----------------------------
# Core generator
# ----------------------------


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def generate_events_simple(
    books: pd.DataFrame,
    cfg: GenConfig,
) -> pd.DataFrame:
    """
    books must have columns:
      - item_id (int)
      - category_id (int from 0..82)  (or any int labels)

    Returns:
      events_df: user_id, item_id, ts, event, view_time_s
      ials_df: user_id, item_id, confidence
    """
    required = {"item_id", "category_id"}
    missing = required - set(books.columns)
    if missing:
        raise ValueError(f"books is missing columns: {missing}")

    rng = np.random.default_rng(cfg.seed)

    # Normalize category ids to 0..(n_cats-1) if needed
    cat_vals = np.sort(books["category_id"].unique())
    cat_to_idx = {c: i for i, c in enumerate(cat_vals)}
    n_cats = len(cat_vals)

    books = books.copy()
    books["cat_idx"] = books["category_id"].map(cat_to_idx).astype(np.int32)

    # Pre-index items by category for fast sampling
    items_by_cat = []
    for ci in range(n_cats):
        arr = books.loc[books["cat_idx"] == ci, "item_id"].to_numpy(dtype=np.int32)
        if arr.size == 0:
            # should not happen with real data, but keep safe
            arr = books["item_id"].to_numpy(dtype=np.int32)
        items_by_cat.append(arr)

    # Popularity inside category (optional): a few items get more views
    # We'll create per-category weights ~ Zipf-ish by rank
    cat_weights = []
    for ci in range(n_cats):
        m = items_by_cat[ci].size
        ranks = np.arange(1, m + 1, dtype=np.float64)
        w = 1.0 / np.power(ranks, 1.1)
        w /= w.sum()
        # shuffle so item_id order isn't tied to rank
        perm = rng.permutation(m)
        w = w[perm]
        items_by_cat[ci] = items_by_cat[ci][perm]
        cat_weights.append(w)

    # Sessions per user: lognormal -> most small, few huge (реалистично)
    base = rng.lognormal(
        mean=np.log(cfg.avg_sessions_per_user + 1e-9), sigma=0.8, size=cfg.n_users
    )
    sessions_per_user = np.clip(
        np.round(base).astype(np.int32), 1, int(cfg.avg_sessions_per_user * 25)
    )

    # Helper: choose session days
    # mild weekly seasonality
    day_idx = np.arange(cfg.days)
    day_mult = 1.0 + 0.15 * np.sin(2 * np.pi * day_idx / 7.0)
    day_mult = day_mult.astype(np.float64)
    day_mult /= day_mult.sum()

    t0 = pd.Timestamp("2025-01-01")

    events = []

    # User taste profiles
    # Each user has k favorite categories with Dirichlet weights
    for u in range(cfg.n_users):
        k = int(rng.integers(cfg.min_fav_cats, cfg.max_fav_cats + 1))
        fav_cats = rng.choice(n_cats, size=k, replace=False)
        fav_w = rng.dirichlet(alpha=np.ones(k, dtype=np.float64) * 0.7)  # spiky-ish
        # Blend: favorite categories vs "exploration"
        # fav_cat_strength controls how many views come from favorites.
        # We implement by sampling from favorites with that probability.
        n_sess = int(sessions_per_user[u])
        sess_days = rng.choice(
            np.arange(cfg.days), size=n_sess, replace=True, p=day_mult
        )

        for d in sess_days:
            # number of views in session (Poisson)
            n_views_target = int(
                np.clip(rng.poisson(lam=cfg.avg_views_per_session), 5, 120)
            )
            # random time of day
            ts_base = t0 + pd.Timedelta(
                days=int(d), seconds=int(rng.integers(0, 24 * 3600))
            )

            for _ in range(n_views_target):
                use_fav = rng.random() < cfg.fav_cat_strength

                if use_fav:
                    # pick a favorite category according to user weights
                    ci = int(rng.choice(fav_cats, p=fav_w))
                    # sample item within category with popularity weights
                    it = int(rng.choice(items_by_cat[ci], p=cat_weights[ci]))
                    is_fav = True
                else:
                    # exploration: random category and item
                    ci = int(rng.integers(0, n_cats))
                    it = int(rng.choice(items_by_cat[ci], p=cat_weights[ci]))
                    is_fav = ci in set(fav_cats)

                # view time:
                # base exp (short by default) + boost if favorite category
                base_time = rng.exponential(scale=14.0)
                boost = 35.0 if is_fav else 0.0
                view_time = float(base_time + boost + rng.normal(0, 3.0))

                if view_time < cfg.min_view_s:
                    continue

                # timestamp slightly jittered per view
                ts = ts_base + pd.Timedelta(seconds=int(rng.integers(0, 25 * 60)))

                # record view
                events.append((u, it, ts, "view", view_time))

                is_long = view_time >= cfg.long_view_s
                if is_long:
                    events.append((u, it, ts, "long_view", view_time))

                # funnel
                p_cart = cfg.p_cart_base
                if is_fav:
                    p_cart *= cfg.cart_boost_if_fav
                if is_long:
                    p_cart *= cfg.cart_boost_if_long
                p_cart = float(min(p_cart, 0.95))

                if rng.random() < p_cart:
                    events.append((u, it, ts, "cart", view_time))

                    p_buy = cfg.p_buy_given_cart_base
                    if is_fav:
                        p_buy *= cfg.buy_boost_if_fav
                    if is_long:
                        p_buy *= cfg.buy_boost_if_long
                    p_buy = float(min(p_buy, 0.98))

                    if rng.random() < p_buy:
                        # purchase a bit later
                        ts_buy = ts + pd.Timedelta(
                            minutes=int(rng.integers(1, 12 * 60))
                        )
                        events.append((u, it, ts_buy, "purchase", view_time))

    events_df = pd.DataFrame(
        events, columns=["user_id", "item_id", "ts", "event", "view_time_s"]
    )

    return events_df


# ----------------------------
# Parquet + MinIO upload
# ----------------------------


def save_parquet(df: pd.DataFrame, path: str) -> None:
    # requires pyarrow installed (recommended)
    df.to_parquet(path, index=False)


def upload_to_minio(local_path: str, object_name: str, mc: MinioConfig) -> None:
    """
    Uses MinIO Python SDK.
    Install: pip install minio
    """
    from minio import Minio

    client = Minio(
        mc.endpoint,
        access_key=mc.access_key,
        secret_key=mc.secret_key,
        secure=mc.secure,
    )

    # create bucket if missing
    found = client.bucket_exists(mc.bucket)
    if not found:
        client.make_bucket(mc.bucket)

    # upload
    client.fput_object(mc.bucket, object_name, local_path)


# ----------------------------
# Example usage
# ----------------------------
if __name__ == "__main__":
    # Example books table:
    # books.csv should contain item_id, category_id
    # If your category is string, map it to int before.
    books = pd.read_csv("books.csv")  # must have item_id, category_id

    cfg = GenConfig(
        seed=7,
        n_users=1000,
        days=90,
        avg_sessions_per_user=4.0,
        avg_views_per_session=18.0,
    )

    events_df = generate_events_simple(books, cfg)

    os.makedirs("out", exist_ok=True)
    events_path = "out/events.parquet"

    # save_parquet(events_df, events_path)

    # MinIO config from env (recommended)
    mc = MinioConfig(
        endpoint=os.environ["MINIO_ENDPOINT"],  # "localhost:9000"
        access_key=os.environ["MINIO_ACCESS_KEY"],
        secret_key=os.environ["MINIO_SECRET_KEY"],
        bucket=os.environ.get("MINIO_BUCKET", "recsys"),
        secure=os.environ.get("MINIO_SECURE", "false").lower() == "true",
    )

    upload_to_minio(events_path, "synthetic/events.parquet", mc)

    print("Done.")
    print("events rows:", len(events_df))
