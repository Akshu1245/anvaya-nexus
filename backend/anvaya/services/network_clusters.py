"""Candidate investigative clusters from stored factual edges only.

Never infers offender identity, guilt, or risk. Clusters are connected components
over case–case relationships discovered via list_related_case_facts.
"""
from __future__ import annotations

from collections import defaultdict, deque

from backend.anvaya.api.errors import ApiError
from backend.anvaya.services.investigation import related_cases
from backend.anvaya.services.policy import evaluate


MAX_SEED_CASES = 40
MAX_NEIGHBOURS = 8
MAX_CLUSTER_SIZE = 12


def _bfs_component(adjacency: dict[str, set[str]], seed: str) -> set[str]:
    seen = {seed}
    queue: deque[str] = deque([seed])
    while queue:
        node = queue.popleft()
        for neighbour in adjacency.get(node, ()):
            if neighbour in seen:
                continue
            if len(seen) >= MAX_CLUSTER_SIZE:
                return seen
            seen.add(neighbour)
            queue.append(neighbour)
    return seen


def candidate_network_clusters(repository, user, purpose, case_id, source_system_ids, limit=5):
    """Return connected-component clusters seeded from a case's stored related facts."""
    if not case_id:
        raise ApiError("CASE_REQUIRED", "A case id is required for candidate clusters.", 400, False)

    base = repository.find_case_360_case(case_id)
    if not base:
        raise ApiError("CASE_NOT_FOUND", "Case was not found.", 404)
    decision = evaluate(
        user, purpose, source_system_ids, "DISCOVER", MAX_NEIGHBOURS, base["station_id"], base["district_id"]
    )
    if not decision.allowed:
        raise ApiError(decision.denial_code or "POLICY_DENIED", decision.explanation, 403)

    adjacency: dict[str, set[str]] = defaultdict(set)
    edge_meta: dict[tuple[str, str], list[dict]] = defaultdict(list)
    visited_seeds: set[str] = set()
    frontier = [case_id]

    while frontier and len(visited_seeds) < MAX_SEED_CASES:
        seed = frontier.pop(0)
        if seed in visited_seeds:
            continue
        visited_seeds.add(seed)
        try:
            related = related_cases(repository, user, purpose, seed, source_system_ids, MAX_NEIGHBOURS)
        except ApiError:
            continue
        for candidate in related.get("related_cases") or []:
            other = candidate["case_id"]
            adjacency[seed].add(other)
            adjacency[other].add(seed)
            reasons = [
                {
                    "label": reason.get("label"),
                    "reason_type": reason.get("reason_type"),
                    "confidence_class": reason.get("confidence_class"),
                    "source_record_id": reason.get("source_record_id"),
                }
                for reason in (candidate.get("related_reasons") or [])[:4]
            ]
            key = tuple(sorted((seed, other)))
            edge_meta[key].extend(reasons)
            if other not in visited_seeds and len(visited_seeds) + len(frontier) < MAX_SEED_CASES:
                frontier.append(other)

    component = sorted(_bfs_component(adjacency, case_id))
    clusters = []
    if len(component) >= 2:
        edges = []
        for left, right in edge_meta:
            if left in component and right in component:
                edges.append(
                    {
                        "left_case_id": left,
                        "right_case_id": right,
                        "reasons": edge_meta[(left, right)][:6],
                    }
                )
        clusters.append(
            {
                "cluster_id": f"CAND-CLUSTER-{case_id}",
                "seed_case_id": case_id,
                "member_case_ids": component,
                "member_count": len(component),
                "edge_count": len(edges),
                "edges": edges[:40],
                "interpretation": (
                    "Candidate connected component over stored related-case facts only. "
                    "Membership does not imply a common offender, guilt, or investigative priority score."
                ),
            }
        )

    return {
        "seed_case_id": case_id,
        "clusters": clusters[:limit],
        "methodology": {
            "method": "Connected components over authorised related-case factual edges.",
            "max_seed_cases": MAX_SEED_CASES,
            "max_neighbours": MAX_NEIGHBOURS,
            "max_cluster_size": MAX_CLUSTER_SIZE,
            "limitations": [
                "Synthetic stored edges only; not a social graph or predictive network.",
                "Does not score people or recommend arrests.",
                "Incomplete source coverage can under- or over-connect cases.",
            ],
        },
    }
