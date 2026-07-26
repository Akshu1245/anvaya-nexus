from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from statistics import median

from backend.anvaya.api.errors import ApiError
from backend.anvaya.repositories.search_filter import CaseSearchFilter
from backend.anvaya.services.policy import evaluate


MAX_ANALYTICS_CASES = 500
PAGE_SIZE = 25
SMALL_CELL_THRESHOLD = 2
SPIKE_MULTIPLIER = 2.0


def _month(value: str) -> str:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%Y-%m")


def _authorised_rows(repository, user, purpose, source_system_ids):
    sources = tuple(dict.fromkeys(source_system_ids))
    decision = evaluate(user, purpose, list(sources), "SEARCH", PAGE_SIZE)
    if not decision.allowed:
        raise ApiError(decision.denial_code, decision.explanation, 403, False)

    rows = []
    for offset in range(0, MAX_ANALYTICS_CASES, PAGE_SIZE):
        page = repository.search_case_candidates(
            CaseSearchFilter(source_system_ids=sources, limit=PAGE_SIZE, offset=offset)
        )
        for row in page:
            row_decision = evaluate(
                user,
                purpose,
                list(sources),
                "SEARCH",
                PAGE_SIZE,
                row["station_id"],
                row["district_id"],
            )
            if row_decision.allowed:
                rows.append(row)
        if len(page) < PAGE_SIZE:
            break
    return rows, sources, decision


def _visible(counter: Counter, key: str):
    return [
        {key: label, "count": count}
        for label, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
        if count >= SMALL_CELL_THRESHOLD
    ]


def _monthly_anomalies(monthly: Counter):
    ordered = sorted(monthly.items())
    if len(ordered) < 3:
        return []
    counts = [count for _, count in ordered[:-1]]
    baseline = median(counts) if counts else 0
    flags = []
    for month, count in ordered:
        if baseline >= SMALL_CELL_THRESHOLD and count >= max(
            SMALL_CELL_THRESHOLD * 2, baseline * SPIKE_MULTIPLIER
        ):
            flags.append(
                {
                    "month": month,
                    "count": count,
                    "baseline_median": baseline,
                    "rule": f"count >= max({SMALL_CELL_THRESHOLD * 2}, {SPIKE_MULTIPLIER}x trailing median)",
                    "interpretation": "Unusual recorded FIR volume versus recent authorised history. Not a forecast.",
                }
            )
    return flags


def _hotspot_deltas(rows):
    months = sorted({_month(row["incident_at"]) for row in rows})
    if len(months) < 2:
        return []
    current_month, previous_month = months[-1], months[-2]
    current = Counter(
        row["station_id"] for row in rows if _month(row["incident_at"]) == current_month
    )
    previous = Counter(
        row["station_id"] for row in rows if _month(row["incident_at"]) == previous_month
    )
    deltas = []
    for station_id in sorted(set(current) | set(previous)):
        cur = current.get(station_id, 0)
        prev = previous.get(station_id, 0)
        delta = cur - prev
        if abs(delta) < SMALL_CELL_THRESHOLD and max(cur, prev) < SMALL_CELL_THRESHOLD:
            continue
        if abs(delta) < SMALL_CELL_THRESHOLD:
            continue
        deltas.append(
            {
                "station_id": station_id,
                "current_month": current_month,
                "previous_month": previous_month,
                "current_count": cur,
                "previous_count": prev,
                "delta": delta,
            }
        )
    deltas.sort(key=lambda item: (-abs(item["delta"]), item["station_id"]))
    return deltas[:10]


def _month_of_year_counts(rows):
    """Descriptive calendar-month seasonality (not a forecast)."""
    labels = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ]
    counter: Counter = Counter()
    for row in rows:
        try:
            month_index = datetime.fromisoformat(row["incident_at"].replace("Z", "+00:00")).month
        except (TypeError, ValueError, KeyError):
            continue
        counter[month_index] += 1
    return [
        {"month_of_year": index, "month_label": labels[index - 1], "count": counter[index]}
        for index in range(1, 13)
        if counter[index] >= SMALL_CELL_THRESHOLD
    ]


def aggregate_crime_trends(repository, user, purpose, source_system_ids):
    """Aggregate authorised FIR facts without scoring people or forecasting crime."""
    rows, sources, _decision = _authorised_rows(repository, user, purpose, source_system_ids)

    monthly = Counter(_month(row["incident_at"]) for row in rows)
    offences = Counter(row["offence"] for row in rows)
    stations = Counter(row["station_id"] for row in rows)
    statuses = Counter(row["status"] for row in rows)
    seasonal = _month_of_year_counts(rows)
    mo_cards = modus_operandi_cooccurrence(repository, user, purpose, source_system_ids, limit=6)

    suppressed = sum(
        1
        for counter in (offences, stations, statuses)
        for count in counter.values()
        if count < SMALL_CELL_THRESHOLD
    )
    return {
        "summary": {
            "authorised_case_count": len(rows),
            "source_count": len(sources),
            "earliest_month": min(monthly, default=None),
            "latest_month": max(monthly, default=None),
            "sample_cap_reached": len(rows) >= MAX_ANALYTICS_CASES,
        },
        "monthly_incidents": [
            {"month": month, "count": monthly[month]} for month in sorted(monthly)
        ],
        "seasonal_month_of_year": seasonal,
        "mo_cooccurrence": mo_cards,
        "offence_distribution": _visible(offences, "offence"),
        "station_hotspots": _visible(stations, "station_id"),
        "status_distribution": _visible(statuses, "status"),
        "hotspot_deltas": _hotspot_deltas(rows),
        "volume_anomalies": _monthly_anomalies(monthly),
        "methodology": {
            "method": "Deterministic count aggregation over authorised synthetic FIR records.",
            "small_cell_threshold": SMALL_CELL_THRESHOLD,
            "maximum_records": MAX_ANALYTICS_CASES,
            "suppressed_group_count": suppressed,
            "delta_rule": "Current versus previous incident-month police-unit volume; suppress |delta| < 2.",
            "anomaly_rule": f"Month count >= max({SMALL_CELL_THRESHOLD * 2}, {SPIKE_MULTIPLIER}x median of earlier months).",
            "seasonality_rule": "Calendar month-of-year counts across authorised incident_at timestamps; descriptive only.",
            "mo_rule": "Shared stored modus-operandi feature labels across authorised cases; not offender identity.",
            "limitations": [
                "Descriptive counts only; this is not a crime forecast or offender-risk score.",
                "No protected demographic attribute is used.",
                "Hotspots and deltas reflect recorded FIR volume and source coverage, not underlying crime prevalence.",
                "Counts are source-, purpose-, role-, and jurisdiction-scoped.",
                "Volume anomaly flags describe unusual recorded volume versus recent authorised history only.",
                "Month-of-year seasonality describes recorded FIRs, not predicted future crime.",
                "MO co-occurrence uses fixture pattern labels only; never behavioural profiling.",
            ],
        },
    }


def modus_operandi_cooccurrence(repository, user, purpose, source_system_ids, limit=8):
    """Surface shared stored MO pattern labels across authorised cases. Not offender identity."""
    rows, sources, _decision = _authorised_rows(repository, user, purpose, source_system_ids)
    allowed_ids = {row["id"] for row in rows}
    features = []
    if hasattr(repository, "list_modus_operandi_features"):
        try:
            features = repository.list_modus_operandi_features()
        except NotImplementedError:
            features = []
    by_pattern = defaultdict(list)
    for item in features:
        case_id = item["case_id"]
        if case_id in allowed_ids:
            by_pattern[item["value"]].append(
                {"case_id": case_id, "source_record_id": item["source_record_id"]}
            )
    cards = []
    for pattern, members in sorted(
        by_pattern.items(), key=lambda item: (-len(item[1]), item[0])
    ):
        if len(members) < SMALL_CELL_THRESHOLD:
            continue
        cards.append(
            {
                "title": f"Stored MO pattern {pattern}",
                "pattern": pattern,
                "case_count": len(members),
                "case_ids": [item["case_id"] for item in members[:8]],
                "source_record_ids": list(
                    dict.fromkeys(item["source_record_id"] for item in members)
                )[:8],
                "why": [
                    "Multiple authorised FIRs share the same stored modus-operandi feature label.",
                    "This is a recorded pattern label, not behavioural profiling or offender identity.",
                ],
                "action": "review_only",
                "limitations": [
                    "Synthetic fixture feature only.",
                    "Does not establish a common offender, guilt, or operational recommendation.",
                ],
            }
        )
        if len(cards) >= limit:
            break
    return cards
