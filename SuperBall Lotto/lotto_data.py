# -*- coding: utf-8 -*-
"""
로또 6/45 당첨 기록 수집 모듈.
- common.do(getLottoNumber) → lt645 JSON(selectPstLt645Info) 순, 재시도·추첨결과 페이지 선요청(크롤링 유사)·srchDir=latest 폴백
- 뉴스 기사 URL에서 당첨번호 파싱 (전부 실패 시 대안)
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

# 동행복권 API (비공식) — 1등 당첨 번호(본당첨 6개+보너스) 조회, 접속 제한 있을 수 있음
# 참고: 당첨번호 조회는 common.do?method=getLottoNumber 사용. roeniss/dhlottery-api(dhapi)는 구매·예치금용이라 당첨조회 미제공.
# 최신 회차 번호는 메인 페이지(method=main) HTML에서 lottoDrwNo 파싱 (https://boramchan-corgi.tistory.com/53 등 참고)
API_URL = "https://www.dhlottery.co.kr/common.do"
MAIN_URL = "https://www.dhlottery.co.kr/common.do?method=main"
DEFAULT_CACHE_PATH = Path(__file__).resolve().parent / "lotto_history.json"
# 요청 간 대기(초) — 서버 부하·차단 완화 (너무 빠르면 차단될 수 있음)
REQUEST_DELAY_SEC = 0.8

# 브라우저처럼 보이도록 헤더 (차단 완화)
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.dhlottery.co.kr/",
}

# HTML 페이지 요청용 헤더 (메인 페이지 파싱 시)
MAIN_PAGE_HEADERS = {
    **REQUEST_HEADERS,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# 로또6/45 공식 추첨결과 페이지(https://www.dhlottery.co.kr/lt645/result)가 호출하는 JSON API
# getLottoNumber(common.do)이 일부 서버 IP에서 HTML 리다이렉트로 막힐 때 대안으로 사용
LT645_RESULT_PAGE = "https://www.dhlottery.co.kr/lt645/result"
LT645_SELECT_INFO_URL = "https://www.dhlottery.co.kr/lt645/selectPstLt645Info.do"
LT645_AJAX_HEADERS = {
    **REQUEST_HEADERS,
    "Referer": LT645_RESULT_PAGE,
    "X-Requested-With": "XMLHttpRequest",
}

# 동일 호스트 연속 요청 시 차단 완화용 재시도 횟수
LT645_FETCH_RETRIES = 3


def _lt645_request_json(query: dict[str, Any], session: Any = None) -> dict | None:
    """selectPstLt645Info.do GET — query 예: srchLtEpsd=1220 또는 srchDir=latest."""
    q = {k: str(v) for k, v in query.items()}
    q.setdefault("_", str(int(time.time() * 1000) % 1_000_000))
    url = f"{LT645_SELECT_INFO_URL}?{urlencode(q)}"
    try:
        if session is not None:
            resp = session.get(url, timeout=15, headers=LT645_AJAX_HEADERS)
            if resp.status_code != 200:
                return None
            return resp.json()
        import urllib.request

        req = urllib.request.Request(url, headers=LT645_AJAX_HEADERS)
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def _lt645_first_list_row(body: dict | None, expect_drw: int | None) -> dict | None:
    """응답 JSON에서 data.list[0] 추출. expect_drw가 있으면 ltEpsd 일치할 때만."""
    if not isinstance(body, dict):
        return None
    data = body.get("data")
    if not isinstance(data, dict):
        return None
    lst = data.get("list")
    if not isinstance(lst, list) or not lst:
        return None
    row = lst[0]
    if not isinstance(row, dict):
        return None
    if expect_drw is not None and int(row.get("ltEpsd", 0)) != int(expect_drw):
        return None
    return row


def _warm_visit_lt645_result_page(session: Any = None) -> None:
    """공식 추첨결과 HTML을 한 번 받아 브라우저 접속 순서와 유사하게 함(크롤링·세션 워밍)."""
    try:
        if session is not None:
            session.get(LT645_RESULT_PAGE, timeout=12, headers=MAIN_PAGE_HEADERS)
        else:
            import urllib.request

            req = urllib.request.Request(LT645_RESULT_PAGE, headers=MAIN_PAGE_HEADERS)
            with urllib.request.urlopen(req, timeout=12):
                pass
    except Exception:
        pass


def _lt645_latest_draw_row(session: Any = None) -> dict | None:
    """최신 회차 한 건(srchDir=latest). get_latest_draw_no 등에 사용."""
    body = _lt645_request_json({"srchDir": "latest"}, session)
    return _lt645_first_list_row(body, None)


def _lt645_row_to_common_raw(row: dict, expect_drw: int) -> dict | None:
    """selectPstLt645Info 응답 한 행을 getLottoNumber과 동일 필드 형태로 변환."""
    try:
        epsd = int(row.get("ltEpsd", 0))
        if epsd != int(expect_drw):
            return None
        nums = [int(row.get(f"tm{i}WnNo", -1)) for i in range(1, 7)]
        if not all(1 <= n <= 45 for n in nums):
            return None
        bonus = int(row.get("bnsWnNo", 0))
        if not (1 <= bonus <= 45):
            return None
    except (TypeError, ValueError):
        return None
    ymd = str(row.get("ltRflYmd", "") or "").strip()
    if len(ymd) == 8 and ymd.isdigit():
        drw_date = f"{ymd[:4]}-{ymd[4:6]}-{ymd[6:]}"
    else:
        drw_date = ""
    try:
        first_n = int(row["rnk1WnNope"]) if row.get("rnk1WnNope") is not None else 0
    except (TypeError, ValueError):
        first_n = 0
    try:
        first_amt = int(row["rnk1WnAmt"]) if row.get("rnk1WnAmt") is not None else 0
    except (TypeError, ValueError):
        first_amt = 0
    try:
        tot_sales = int(row["wholEpsdSumNtslAmt"]) if row.get("wholEpsdSumNtslAmt") is not None else 0
    except (TypeError, ValueError):
        tot_sales = 0
    return {
        "returnValue": "success",
        "drwNo": epsd,
        "drwNoDate": drw_date,
        "drwtNo1": nums[0],
        "drwtNo2": nums[1],
        "drwtNo3": nums[2],
        "drwtNo4": nums[3],
        "drwtNo5": nums[4],
        "drwtNo6": nums[5],
        "bnusNo": bonus,
        "firstPrzwnerCo": first_n,
        "firstWinamnt": first_amt,
        "totSellamnt": tot_sales,
    }


def _fetch_one_draw_lt645(drw_no: int, session: Any = None) -> dict | None:
    """
    lt645 selectPstLt645Info JSON — 재시도, 최신 조회 폴백, 추첨결과 페이지 선방문 순으로 시도(크롤링).
    """
    drw_no = int(drw_no)

    def _from_epsd(attempts: int) -> dict | None:
        for attempt in range(attempts):
            body = _lt645_request_json({"srchLtEpsd": drw_no}, session)
            row = _lt645_first_list_row(body, drw_no)
            if row:
                conv = _lt645_row_to_common_raw(row, drw_no)
                if conv:
                    return conv
            if attempt + 1 < attempts:
                time.sleep(REQUEST_DELAY_SEC)
        return None

    out = _from_epsd(LT645_FETCH_RETRIES)
    if out:
        return out
    # 회차 지정이 일시 실패할 때 최신 한 건으로 동일 회차인지 확인
    latest = _lt645_latest_draw_row(session)
    if latest and int(latest.get("ltEpsd", 0)) == drw_no:
        conv = _lt645_row_to_common_raw(latest, drw_no)
        if conv:
            return conv
    _warm_visit_lt645_result_page(session)
    time.sleep(REQUEST_DELAY_SEC)
    out = _from_epsd(2)
    if out:
        return out
    latest = _lt645_latest_draw_row(session)
    if latest and int(latest.get("ltEpsd", 0)) == drw_no:
        return _lt645_row_to_common_raw(latest, drw_no)
    return None


def get_latest_draw_no(session: Any = None) -> int | None:
    """
    최신 회차: lt645 JSON(srchDir=latest) 우선, 실패 시 메인 HTML lottoDrwNo.
    """
    for _ in range(2):
        row = _lt645_latest_draw_row(session)
        if row and row.get("ltEpsd") is not None:
            try:
                return int(row["ltEpsd"])
            except (TypeError, ValueError):
                pass
        time.sleep(REQUEST_DELAY_SEC)
    try:
        if session is not None:
            resp = session.get(MAIN_URL, timeout=10, headers=MAIN_PAGE_HEADERS)
            if resp.status_code != 200:
                return None
            html = resp.text
        else:
            import urllib.request

            req = urllib.request.Request(MAIN_URL, headers=MAIN_PAGE_HEADERS)
            with urllib.request.urlopen(req, timeout=10) as r:
                html = r.read().decode("utf-8", errors="replace")
        m = re.search(r'<strong\s+id="lottoDrwNo">\s*(\d+)\s*</strong>', html)
        if m:
            return int(m.group(1))
        if "lottoDrwNo" in html:
            parts = html.split('id="lottoDrwNo">')
            if len(parts) >= 2:
                num_str = parts[1].split("</strong>")[0].strip()
                if num_str.isdigit():
                    return int(num_str)
        return None
    except Exception:
        return None


def _fetch_get_lotto_number_only(drw_no: int, session: Any = None) -> dict | None:
    """common.do getLottoNumber 단독 조회(재시도 포함)."""
    url = f"{API_URL}?method=getLottoNumber&drwNo={drw_no}"
    for attempt in range(2):
        try:
            if session is not None:
                resp = session.get(url, timeout=15)
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                    except (ValueError, TypeError):
                        data = None
                    else:
                        if isinstance(data, dict) and data.get("returnValue") == "success":
                            return data
            else:
                import urllib.request

                req = urllib.request.Request(url, headers=REQUEST_HEADERS)
                with urllib.request.urlopen(req, timeout=15) as r:
                    data = json.loads(r.read().decode("utf-8"))
                if isinstance(data, dict) and data.get("returnValue") == "success":
                    return data
        except Exception:
            pass
        if attempt == 0:
            time.sleep(REQUEST_DELAY_SEC)
    return None


def _fetch_one_draw(drw_no: int, session: Any = None) -> dict | None:
    """
    특정 회차 1등 당첨 정보 한 건 조회 (본당첨 6개 + 보너스).
    getLottoNumber → lt645(재시도·페이지 워밍·latest 폴백) 순.
    """
    raw = _fetch_get_lotto_number_only(drw_no, session)
    if raw:
        return raw
    raw = _fetch_one_draw_lt645(drw_no, session)
    if raw:
        return raw
    # getLotto만 재시도 한 번 더(lt645 워밍 후)
    _warm_visit_lt645_result_page(session)
    time.sleep(REQUEST_DELAY_SEC)
    raw = _fetch_get_lotto_number_only(drw_no, session)
    if raw:
        return raw
    return _fetch_one_draw_lt645(drw_no, session)


def fetch_lotto_draw_raw(drw_no: int) -> dict | None:
    """getLottoNumber → lt645 순으로 한 회차 원시 dict 조회(urllib만 사용). 웹 서버 등에서 호출."""
    return _fetch_one_draw(int(drw_no), None)


def _draw_to_record(raw: dict) -> dict:
    """API 응답 한 건을 저장용 레코드로 변환."""
    return {
        "drwNo": raw.get("drwNo"),
        "drwNoDate": raw.get("drwNoDate", ""),
        "drwtNo1": raw.get("drwtNo1"),
        "drwtNo2": raw.get("drwtNo2"),
        "drwtNo3": raw.get("drwtNo3"),
        "drwtNo4": raw.get("drwtNo4"),
        "drwtNo5": raw.get("drwtNo5"),
        "drwtNo6": raw.get("drwtNo6"),
        "bnusNo": raw.get("bnusNo"),
    }


def load_history(cache_path: Path | str | None = None) -> list[dict]:
    """
    로컬 캐시에서 당첨 기록 목록 로드.
    파일이 없거나 빈 목록이면 [] 반환.
    """
    path = Path(cache_path or DEFAULT_CACHE_PATH)
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "draws" in data:
        return data["draws"]
    return []


def save_history(draws: list[dict], cache_path: Path | str | None = None) -> None:
    """당첨 기록 목록을 로컬 JSON으로 저장."""
    path = Path(cache_path or DEFAULT_CACHE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"draws": draws, "total": len(draws)}, f, ensure_ascii=False, indent=2)


def fetch_one_round_from_api(
    drw_no: int,
    cache_path: Path | str | None = None,
    use_requests: bool = True,
) -> tuple[dict | None, str]:
    """
    특정 회차 1건만 API로 조회 후 캐시에 추가.
    반환: (레코드, None) 또는 (None, 에러 메시지)
    """
    session = None
    if use_requests:
        try:
            import requests
            session = requests.Session()
            session.headers.update(REQUEST_HEADERS)
        except ImportError:
            pass
    raw = _fetch_one_draw(drw_no, session)
    # requests가 막혔을 수 있으므로 urllib로 한 번 더 시도
    if raw is None and session is not None:
        raw = _fetch_one_draw(drw_no, None)
    if raw is None:
        return None, f"제{drw_no}회 데이터를 가져오지 못했습니다. (동행복권 접속 제한 또는 해당 회차 없음)"
    record = _draw_to_record(raw)
    path = Path(cache_path or DEFAULT_CACHE_PATH)
    existing = load_history(path)
    by_no = {d["drwNo"]: d for d in existing}
    by_no[record["drwNo"]] = record
    merged = [by_no[n] for n in sorted(by_no.keys())]
    save_history(merged, path)
    return record, ""


def fetch_all_from_api(
    start_no: int = 1,
    max_attempts: int = 2000,
    cache_path: Path | str | None = None,
    use_requests: bool = True,
) -> tuple[list[dict], int]:
    """
    1회차부터 순차적으로 API로 당첨 기록을 가져와 (전체 목록, 이번에 새로 수집한 개수) 반환.
    연속 실패(해당 회차 없음 또는 접속 차단)가 나오면 수집 종료.
    """
    session = None
    if use_requests:
        try:
            import requests
            session = requests.Session()
            session.headers.update(REQUEST_HEADERS)
        except ImportError:
            pass

    collected: list[dict] = []
    consecutive_fail = 0
    max_consecutive_fail = 5  # 연속 5회 실패 시 종료 (API 차단 시 빠르게 포기)

    for drw_no in range(start_no, start_no + max_attempts):
        raw = _fetch_one_draw(drw_no, session)
        time.sleep(REQUEST_DELAY_SEC)

        if raw is None:
            consecutive_fail += 1
            if consecutive_fail >= max_consecutive_fail:
                break
            continue
        consecutive_fail = 0
        record = _draw_to_record(raw)
        collected.append(record)

    if collected:
        existing = load_history(cache_path)
        by_no = {d["drwNo"]: d for d in existing}
        for d in collected:
            by_no[d["drwNo"]] = d
        merged = [by_no[n] for n in sorted(by_no.keys())]
        save_history(merged, cache_path)
        return merged, len(collected)
    # API에서 한 건도 못 가져옴 → 기존 캐시만 반환, 새로 수집한 건수 0
    return load_history(cache_path), 0


def ensure_history(
    cache_path: Path | str | None = None,
    try_api: bool = True,
) -> list[dict]:
    """
    캐시가 있으면 로드하고, 없거나 try_api=True이면 API로 수집 시도 후 반환.
    """
    path = cache_path or DEFAULT_CACHE_PATH
    existing = load_history(path)
    if try_api:
        from_api, _ = fetch_all_from_api(cache_path=path, use_requests=True)
        if from_api:
            return from_api
    return existing


def parse_round_from_news_text(text: str, drw_no_hint: int | None = None) -> dict | None:
    """
    뉴스 기사 본문에서 당첨 회차·번호·보너스를 추출.
    예: "1214회 당첨번호 '10·15·19·27·30·33'", "보너스 번호는 '14'"
    """
    if not text or len(text) < 20:
        return None
    drw_no = drw_no_hint
    if drw_no is None:
        for pattern in [
            r"제\s*(\d{3,5})\s*회",
            r"로또\s*(\d{3,5})\s*회",
            r"(\d{3,5})\s*회\s*당첨",
            r"(\d{3,5})\s*회\s*로또",  # "[오늘 로또]1214회 로또 1등..."
        ]:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                drw_no = int(m.group(1))
                break
    if drw_no is None:
        return None
    main_nums: list[int] = []
    for pattern in [
        r"당첨번호[로]*\s*[\['\"]([0-9\s·,]+)[\]'\"]",
        r"1등\s*당첨번호[로]*\s*[\['\"]([0-9\s·,]+)[\]'\"]",
        r"당첨\s*번호\s*[\['\"]([0-9\s·,]+)[\]'\"]",
        r"['\"]([0-9]{1,2}\s*[·,]\s*[0-9]{1,2}\s*[·,]\s*[0-9]{1,2}\s*[·,]\s*[0-9]{1,2}\s*[·,]\s*[0-9]{1,2}\s*[·,]\s*[0-9]{1,2})['\"]",
    ]:
        m = re.search(pattern, text)
        if m:
            raw = re.sub(r"[\s·]+", " ", m.group(1)).replace(",", " ").strip()
            parts = [int(x) for x in raw.split() if x.strip().isdigit()]
            if len(parts) >= 6:
                main_nums = sorted(parts[:6])
                break
    if len(main_nums) != 6 or not all(1 <= n <= 45 for n in main_nums):
        return None
    bnus_no = 0
    for pattern in [
        r"보너스\s*번호[는]*\s*[\['\"]?\s*(\d{1,2})\s*[\]'\"]?",
        r"2등\s*보너스\s*[\['\"]?\s*(\d{1,2})\s*[\]'\"]?",
    ]:
        m = re.search(pattern, text)
        if m:
            b = int(m.group(1))
            if 1 <= b <= 45:
                bnus_no = b
                break
    return {
        "drwNo": drw_no,
        "drwNoDate": "",
        "drwtNo1": main_nums[0],
        "drwtNo2": main_nums[1],
        "drwtNo3": main_nums[2],
        "drwtNo4": main_nums[3],
        "drwtNo5": main_nums[4],
        "drwtNo6": main_nums[5],
        "bnusNo": bnus_no,
    }


def add_manual_draw(
    drw_no: int,
    numbers: list[int],
    bonus: int | None = None,
    cache_path: Path | str | None = None,
) -> tuple[dict | None, str]:
    """
    사용자가 직접 입력한 회차·당첨번호 6개·보너스(선택)를 캐시에 추가.
    numbers: 6개 번호 (1~45), 정렬 안 되어 있어도 내부에서 정렬함.
    bonus: 없으면 None 또는 0.
    """
    if not isinstance(numbers, (list, tuple)) or len(numbers) != 6:
        return None, "당첨번호는 6개를 입력해 주세요."
    try:
        main_nums = sorted([int(x) for x in numbers])
    except (TypeError, ValueError):
        return None, "당첨번호는 1~45 사이 숫자 6개로 입력해 주세요."
    if not all(1 <= n <= 45 for n in main_nums):
        return None, "당첨번호는 1~45 사이여야 합니다."
    if len(set(main_nums)) != 6:
        return None, "당첨번호 6개는 서로 달라야 합니다."
    if drw_no < 1 or drw_no > 2000:
        return None, "회차는 1~2000 사이로 입력해 주세요."
    bnus_no: int | None = None
    if bonus is not None and bonus != 0:
        if 1 <= bonus <= 45 and bonus not in main_nums:
            bnus_no = int(bonus)
        elif 1 <= bonus <= 45:
            bnus_no = int(bonus)  # 본번호와 같아도 저장은 함 (실제 추첨에선 보통 다름)
    path = Path(cache_path or DEFAULT_CACHE_PATH)
    existing = load_history(path)
    by_no = {d["drwNo"]: d for d in existing}
    record = {
        "drwNo": drw_no,
        "drwNoDate": "",
        "drwtNo1": main_nums[0],
        "drwtNo2": main_nums[1],
        "drwtNo3": main_nums[2],
        "drwtNo4": main_nums[3],
        "drwtNo5": main_nums[4],
        "drwtNo6": main_nums[5],
        "bnusNo": bnus_no,
    }
    by_no[drw_no] = record
    merged = [by_no[n] for n in sorted(by_no.keys())]
    save_history(merged, path)
    return record, f"제{drw_no}회 직접 추가됨. 총 {len(merged)}회차 보유."


def fetch_one_from_news_url(
    url: str,
    cache_path: Path | str | None = None,
) -> tuple[dict | None, str]:
    """뉴스 기사 URL을 열어 당첨번호를 파싱하고, 성공 시 캐시에 추가."""
    headers = {**REQUEST_HEADERS, "Referer": ""}  # 뉴스 사이트는 Referer 비움
    try:
        import urllib.request
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode("utf-8", errors="replace")
    except Exception as e:
        return None, f"URL 요청 실패: {e!s}"
    record = parse_round_from_news_text(html)
    if record is None:
        return None, "기사에서 당첨번호를 찾지 못했습니다. '1214회 당첨번호', '보너스 번호' 형식이 있는지 확인해 주세요."
    path = Path(cache_path or DEFAULT_CACHE_PATH)
    existing = load_history(path)
    by_no = {d["drwNo"]: d for d in existing}
    by_no[record["drwNo"]] = record
    merged = [by_no[n] for n in sorted(by_no.keys())]
    save_history(merged, path)
    return record, f"제{record['drwNo']}회 추가됨. 총 {len(merged)}회차 보유."


def add_from_text(
    text: str,
    cache_path: Path | str | None = None,
) -> tuple[dict | None, str]:
    """
    한 줄 문장(예: 기사 제목)에서 회차·당첨번호·보너스를 파싱해 캐시에 추가.
    예: "[오늘 로또]1214회 로또 1등... 당첨번호 '10, 15, 19, 27, 30, 33'"
    """
    record = parse_round_from_news_text(text)
    if record is None:
        return None, "문장에서 회차·당첨번호 6개를 찾지 못했습니다. 예: 1214회 당첨번호 '10, 15, 19, 27, 30, 33'"
    path = Path(cache_path or DEFAULT_CACHE_PATH)
    existing = load_history(path)
    by_no = {d["drwNo"]: d for d in existing}
    by_no[record["drwNo"]] = record
    merged = [by_no[n] for n in sorted(by_no.keys())]
    save_history(merged, path)
    return record, f"제{record['drwNo']}회 추가됨. 총 {len(merged)}회차 보유."