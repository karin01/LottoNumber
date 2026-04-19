# -*- coding: utf-8 -*-
"""
로또 6/45 확률 계산 모듈.
1회차부터의 당첨 기록을 이용해 번호별 출현 횟수·비율(확률)을 구하고,
최근 N회차 가중 확률을 지원합니다.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Optional

# 로또 6/45 번호 범위
MIN_NUM = 1
MAX_NUM = 45
NUM_COUNT = 6


def _draw_to_main_numbers(draw: dict) -> list[int]:
    """한 회차 레코드에서 본당첨 6개 번호만 리스트로 추출."""
    out: list[int] = []
    for i in range(1, 7):
        v = draw.get(f"drwtNo{i}")
        if v is not None and isinstance(v, int):
            out.append(v)
    return out


def _draw_to_all_numbers(draw: dict) -> list[int]:
    """한 회차 레코드에서 본당첨 6개 + 보너스 번호 (분석용)."""
    main = _draw_to_main_numbers(draw)
    bnus = draw.get("bnusNo")
    if bnus is not None and isinstance(bnus, int):
        main.append(bnus)
    return main


def compute_frequency(
    draws: list[dict],
    include_bonus: bool = False,
) -> dict[int, int]:
    """
    번호별 출현 횟수 계산.
    include_bonus=True 이면 보너스 번호도 포함해 집계.
    반환: { 번호: 출현횟수 } (1~45만 키로 가짐)
    """
    counter: dict[int, int] = defaultdict(int)
    for num in range(MIN_NUM, MAX_NUM + 1):
        counter[num] = 0

    for d in draws:
        nums = _draw_to_all_numbers(d) if include_bonus else _draw_to_main_numbers(d)
        for n in nums:
            if MIN_NUM <= n <= MAX_NUM:
                counter[n] += 1

    return dict(counter)


def frequency_to_probability(frequency: dict[int, int]) -> dict[int, float]:
    """
    출현 횟수를 비율(확률)로 변환.
    합이 1이 되도록 정규화. (0이면 균등 비율로 처리)
    """
    total = sum(frequency.values())
    if total <= 0:
        n_keys = len([k for k in frequency if MIN_NUM <= k <= MAX_NUM])
        if n_keys == 0:
            n_keys = MAX_NUM - MIN_NUM + 1
        return {i: 1.0 / n_keys for i in range(MIN_NUM, MAX_NUM + 1)}

    return {k: v / total for k, v in frequency.items()}


def compute_weighted_frequency(
    draws: list[dict],
    last_n: int,
    include_bonus: bool = False,
) -> dict[int, float]:
    """
    최근 last_n 회차만 사용하고, 최근일수록 가중치를 높게 부여한 출현 점수.
    가중치: 가장 최근 = last_n, 그 이전 = last_n-1, ... → 합으로 나누어 확률로 사용 가능.
    반환: { 번호: 가중 출현 점수 } (정규화는 generator에서 확률로 변환 시 사용)
    """
    if not draws or last_n <= 0:
        return {i: 1.0 for i in range(MIN_NUM, MAX_NUM + 1)}

    recent = draws[-last_n:]
    weighted: dict[int, float] = defaultdict(float)
    for i in range(MIN_NUM, MAX_NUM + 1):
        weighted[i] = 0.0

    for weight, d in enumerate(recent, start=1):
        nums = _draw_to_all_numbers(d) if include_bonus else _draw_to_main_numbers(d)
        for n in nums:
            if MIN_NUM <= n <= MAX_NUM:
                weighted[n] += weight

    return dict(weighted)


def get_probability_map(
    draws: list[dict],
    use_recent_only: Optional[int] = None,
    include_bonus: bool = False,
    sharpen: float = 1.0,
) -> dict[int, float]:
    """
    생성기에 쓸 번호별 확률 맵 반환.
    - use_recent_only=None: 전체 회차 출현 비율
    - use_recent_only=N: 최근 N회 가중 확률
    - sharpen>1: 출현 비율에 거듭제곱 후 재정규화 → 자주 나온 번호 쪽으로 뽑힐 비중 증가(1.0=기존과 동일)
    """
    if use_recent_only is not None and use_recent_only > 0:
        freq = compute_weighted_frequency(draws, use_recent_only, include_bonus)
    else:
        freq = compute_frequency(draws, include_bonus)
        freq = {k: float(v) for k, v in freq.items()}
    base = frequency_to_probability(freq)
    try:
        s = float(sharpen)
    except (TypeError, ValueError):
        s = 1.0
    if s <= 1.0001:
        return base
    s = min(s, 4.0)
    raw = {k: max(float(base.get(k, 1e-12)) ** s, 1e-15) for k in range(MIN_NUM, MAX_NUM + 1)}
    tot = sum(raw.values())
    if tot <= 0:
        return base
    return {k: raw[k] / tot for k in raw}
