from __future__ import annotations


def _sorted(values: list[float]) -> list[float]:
    return sorted(values)


def mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def median(values: list[float]) -> float:
    if not values:
        return 0.0
    s = _sorted(values)
    n = len(s)
    mid = n // 2
    if n % 2 == 1:
        return float(s[mid])
    return (s[mid - 1] + s[mid]) / 2.0


def quartiles(values: list[float]) -> tuple[float, float, float]:
    if not values:
        return 0.0, 0.0, 0.0
    s = _sorted(values)

    def _percentile(data: list[float], pct: float) -> float:
        if not data:
            return 0.0
        idx = pct / 100.0 * (len(data) - 1)
        lo = int(idx)
        hi = lo + 1
        if hi >= len(data):
            return float(data[lo])
        return data[lo] + (idx - lo) * (data[hi] - data[lo])

    return _percentile(s, 25), _percentile(s, 50), _percentile(s, 75)


def std_deviation(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = mean(values)
    return (sum((x - m) ** 2 for x in values) / len(values)) ** 0.5


def percentile_ranks(scores: list[float]) -> list[dict]:
    if not scores:
        return []

    import math
    s = sorted(scores)
    n = len(s)
    score_min = int(s[0])

    def at_pct(pct: int) -> int:
        idx = math.ceil((pct / 100) * n) - 1
        return int(s[max(0, min(idx, n - 1))])

    p25, p50, p75, p90 = at_pct(25), at_pct(50), at_pct(75), at_pct(90)

    return [
        {"label": "P25", "description": "Bottom quarter", "score_range": f"{score_min} - {p25} pts", "pct_range": "0 - 25th pct"},
        {"label": "P50", "description": "Median half",    "score_range": f"{p25} - {p50} pts",       "pct_range": "25 - 50th pct"},
        {"label": "P75", "description": "Top quarter",    "score_range": f"{p50} - {p75} pts",       "pct_range": "50 - 75th pct"},
        {"label": "P90", "description": "Top 10%",        "score_range": f"{p90}+ pts",              "pct_range": "90th pct+"},
    ]


def score_distribution(values: list[float], num_buckets: int = 5) -> list[dict]:
    if not values:
        return []
    lo = min(values)
    hi = max(values)
    if lo == hi:
        return [{"range": f"{int(lo)}", "bucket": f"{int(lo)}", "count": len(values), "percentage": 100.0}]

    bucket_size = (hi - lo) / num_buckets
    buckets: list[int] = [0] * num_buckets
    for v in values:
        idx = min(int((v - lo) / bucket_size), num_buckets - 1)
        buckets[idx] += 1

    n = len(values)
    result = []
    for i, count in enumerate(buckets):
        label = f"{int(lo + i * bucket_size)}-{int(lo + (i + 1) * bucket_size)}"
        result.append({"bucket": label, "range": label, "count": count, "percentage": round(count / n * 100, 1)})
    return result


def full_stats(scores: list[float]) -> dict:
    if not scores:
        return {
            "count": 0, "mean": 0.0, "median": 0.0,
            "q1": 0.0, "q3": 0.0, "min": 0.0, "max": 0.0,
            "std_deviation": 0.0, "percentile_ranks": [], "score_distribution": [],
        }

    q1, med, q3 = quartiles(scores)
    return {
        "count": len(scores),
        "mean": round(mean(scores), 2),
        "median": round(med, 2),
        "q1": round(q1, 2),
        "q3": round(q3, 2),
        "min": min(scores),
        "max": max(scores),
        "std_deviation": round(std_deviation(scores), 2),
        "percentile_ranks": percentile_ranks(scores),
        "score_distribution": score_distribution(scores),
    }
