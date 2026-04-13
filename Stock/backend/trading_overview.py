# -*- coding: utf-8 -*-
"""
주식 거래 현황 모듈
- pykrx 기반 국내 시장 현황 (거래대금, 상승/하락, 등락률 상위)
- KRX(data.krx.co.kr) 연결 실패 시 None/빈 목록 반환 (앱 크래시 방지)
- KRX/pykrx 종목명 실패 시 네이버 모바일 주식 API 로 한글명 보강
"""

import json
import math
import re
from datetime import datetime, timedelta


def _json_safe_float(value, *, ndigits: int | None = 2) -> float | None:
    """
    JSON 직렬화용 실수: nan/inf 는 표준 JSON 에 불가하므로 None(null)로 치환.
    ndigits: None 이면 반올림 없이 유한 실수만 반환.
    """
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(f) or math.isinf(f):
        return None
    if ndigits is not None:
        return round(f, ndigits)
    return f


# pykrx get_market_ohlcv_by_ticker 반환 컬럼: 시가, 고가, 저가, 종가, 거래량, 거래대금, 등락률, 시가총액
# 인덱스 fallback (컬럼명 인코딩 이슈 대비)
_COL_거래대금 = "거래대금"
_COL_거래량 = "거래량"
_COL_등락률 = "등락률"
_COL_종가 = "종가"


def _normalize_top_traded_sort(sort_by: str | None) -> str:
    """거래순위 정렬: 거래대금(기본) | 거래량. 쿼리는 volume 등 ASCII 별칭 권장."""
    if sort_by is None:
        return "거래대금"
    raw = str(sort_by).strip()
    low = raw.casefold()
    if low in ("volume", "vol", "v", "shares") or raw == "거래량":
        return "거래량"
    return "거래대금"


def _normalize_krx_ticker(raw) -> str:
    """
    pykrx/yfinance 혼용 시 인덱스가 '035720.KQ,0P0000...,...' 형태로 깨질 수 있음 → 6자리 숫자만 추출.
    """
    if raw is None:
        return ""
    if isinstance(raw, tuple) and raw:
        raw = raw[0]
    s = str(raw).strip()
    if not s:
        return ""
    if "," in s:
        s = s.split(",")[0].strip()
    if "." in s:
        s = s.split(".")[0].strip()
    m = re.search(r"\d{6}", s)
    return m.group(0) if m else ""


def _티커인덱스_6자리(ix) -> str:
    """KRX 시리즈 인덱스가 5930(int), '5930', '005930' 등으로 올 때 6자리 문자열로 통일."""
    if ix is None:
        return ""
    if isinstance(ix, str):
        s = ix.strip()
        if re.fullmatch(r"\d{6}", s):
            return s
    s = str(ix).strip()
    try:
        fv = float(s)
        if fv >= 0 and fv == int(fv) and int(fv) < 10**7:
            return str(int(fv)).zfill(6)
    except ValueError:
        pass
    m = re.search(r"\d{6}", s)
    return m.group(0) if m else ""


def _krx_한글명_맵_최근일(market: str, 최대_과거일: int = 12) -> dict[str, str]:
    """휴장일·당일 미반영 시 전일 KRX 전종목 명칭 표로 맵 구축."""
    try:
        from pykrx.website.krx.market.wrap import get_market_ticker_and_name
    except Exception:
        return {}
    for d in range(0, 최대_과거일):
        날 = (datetime.now() - timedelta(days=d)).strftime("%Y%m%d")
        try:
            m = _krx_이름_series를_맵으로(get_market_ticker_and_name(날, market))
            if m:
                return m
        except Exception:
            continue
    return {}


def _krx_이름_series를_맵으로(이름_series) -> dict[str, str]:
    """get_market_ticker_and_name 결과 → { '005930': '삼성전자', ... } (인덱스 타입 혼합 대응)."""
    if 이름_series is None or len(이름_series) == 0:
        return {}
    out: dict[str, str] = {}
    try:
        for ix, val in 이름_series.items():
            k = _티커인덱스_6자리(ix)
            if not k:
                continue
            name = str(val).strip()
            if (
                name
                and name.lower() not in ("nan", "none")
                and not re.fullmatch(r"\d{6}", name)
            ):
                out[k] = name
    except Exception:
        return {}
    return out


def _종목명_pykrx(티커_6: str) -> str:
    """pykrx 단건 조회. 선행 0 유무·숫자형 티커 등 KRX 쪽 표기 차이를 순차 시도."""
    t = (티커_6 or "").strip()
    if not re.fullmatch(r"\d{6}", t):
        return t or "—"
    candidates = [t, str(int(t))]
    try:
        from pykrx import stock

        for c in candidates:
            try:
                n = stock.get_market_ticker_name(c)
                if n and str(n).strip():
                    ns = str(n).strip()
                    if not re.fullmatch(r"\d{6}", ns):
                        return ns
            except Exception:
                continue
    except Exception:
        pass
    return t


# 네이버 m.stock UTF-8 JSON — KRX 가 막힌 PC 에서도 한글 종목명 확보
_NAVER_NAME_CACHE: dict[str, str] = {}
_NAVER_REQ_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "ko-KR,ko;q=0.9",
}


def _종목명_네이버(티커_6: str) -> str:
    """https://m.stock.naver.com/api/stock/{코드}/basic 의 stockName (성공 시만 캐시)."""
    t = (티커_6 or "").strip()
    if not re.fullmatch(r"\d{6}", t):
        return t or "—"
    if t in _NAVER_NAME_CACHE:
        return _NAVER_NAME_CACHE[t]
    url = f"https://m.stock.naver.com/api/stock/{t}/basic"
    try:
        try:
            import requests

            r = requests.get(url, headers=_NAVER_REQ_HEADERS, timeout=6)
            r.raise_for_status()
            data = r.json()
        except ImportError:
            import urllib.request

            req = urllib.request.Request(url, headers=_NAVER_REQ_HEADERS)
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        name = (data.get("stockName") or "").strip()
        if name and not re.fullmatch(r"\d{6}", name):
            _NAVER_NAME_CACHE[t] = name
            return name
    except Exception:
        pass
    return t


def _네이버_종목명_병렬(티커_목록: list[str]) -> None:
    """티커별 네이버 조회(최대 10동시). 성공분은 _NAVER_NAME_CACHE 에 적재."""
    uniq = list(
        dict.fromkeys(x for x in 티커_목록 if re.fullmatch(r"\d{6}", str(x)))
    )
    todo = [x for x in uniq if x not in _NAVER_NAME_CACHE]
    if not todo:
        return
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=10) as pool:
        list(pool.map(_종목명_네이버, todo))


# pykrx 실패 시 yfinance 폴백용 유동성 큰 종목 (중복 제거·충분한 개수 확보)
_FALLBACK_KOSPI = list(
    dict.fromkeys(
        [
            "005930", "000660", "035420", "051910", "006400", "068270", "207940", "005380",
            "000270", "012330", "066570", "003550", "034730", "051900", "018880", "000810",
            "009150", "017670", "009540", "010950", "096770", "000720", "042660", "010140",
            "329180", "003670", "011200", "004170", "008930", "009830", "032830", "000860",
            "105560", "024110", "009290", "161390", "033780", "018260", "034020", "086790",
            "018670", "011070", "316140", "373220", "028260", "047810", "086280", "071050",
            "088350", "003490", "015760", "030200", "033530", "016360", "079550", "180640",
            "326030", "352820", "017800", "010130", "011790", "030000", "004020", "090430",
            "009240", "003230", "001040", "128940", "139480", "241560", "298040",
            "259960", "003090", "011170", "004990", "006800", "009420", "012450", "021240",
            "023530", "030610", "034220", "039490", "051600", "055550", "064350",
        ]
    )
)
_FALLBACK_KOSDAQ = list(
    dict.fromkeys(
        [
            "035720", "247540", "086520", "036570", "068760", "263750", "207760", "041020",
            "067160", "058970", "214150", "036190", "293490", "039030",
            "086900", "054540", "064960", "068290", "950210", "034810", "053290", "038870",
            "214420", "089970", "033250", "052460", "067370", "058470", "036200", "263720",
            "054620", "065650", "043150", "214370", "054780", "290650",
            "277810", "196170", "377300", "403870", "417200", "086450", "348370", "225570",
            "310210", "328130", "357780", "140410", "278470", "183300", "237690", "122870",
            "323410", "376300", "417970", "439090", "084370", "131970", "222800", "253450",
            "145020", "272210", "281740", "298380", "319660", "352480", "356860", "358570",
        ]
    )
)


def _최근_영업일(오프셋: int = 0) -> str:
    """최근 영업일 YYYYMMDD (0=오늘, 1=전일, ...)"""
    d = datetime.now() - timedelta(days=오프셋)
    return d.strftime("%Y%m%d")


def _yfinance_지수_또는_프록시(심볼_순서: list[str]) -> tuple[float | None, float | None]:
    """
    Yahoo 지수(^KS11 등)가 NaN/빈 경우가 있어, 동일 루프에서 유효한 종가가 나올 때까지 심볼 목록을 순회.
    ETF(069500.KS KODEX200 등)는 지수와 수치가 다르지만 UI 에 '값 없음' 보다 나음.
    """
    import yfinance as yf

    for sym in 심볼_순서:
        try:
            hist = yf.Ticker(sym).history(period="15d")
            if hist is None or hist.empty or "Close" not in hist.columns:
                continue
            close_s = hist["Close"].dropna()
            if close_s.empty:
                continue
            curr_f = _json_safe_float(close_s.iloc[-1], ndigits=2)
            if curr_f is None:
                continue
            pct_f: float | None = None
            if len(close_s) >= 2:
                prev_f = _json_safe_float(close_s.iloc[-2], ndigits=None)
                if prev_f is not None and prev_f != 0:
                    pct_f = _json_safe_float(
                        (float(close_s.iloc[-1]) - float(close_s.iloc[-2]))
                        / float(close_s.iloc[-2])
                        * 100.0,
                        ndigits=2,
                    )
            return curr_f, pct_f
        except Exception:
            continue
    return None, None


def get_market_overview() -> dict | None:
    """
    시장 거래 현황 요약 반환.
    - yfinance 기반 코스피/코스닥 지수 및 등락률 조회
    - 지수 심볼이 NaN 인 환경에서는 국내 대표 ETF 로 대체
    - 네트워크/API 오류 시 None 반환
    """
    import yfinance as yf

    결과 = {"조회일": datetime.now().strftime("%Y-%m-%d"), "코스피": {}, "코스닥": {}, "환율": {}}

    try:
        for market, ticker_name in [("코스피", "^KS11"), ("코스닥", "^KQ11"), ("환율", "KRW=X")]:
            try:
                hist = yf.Ticker(ticker_name).history(period="15d")
                if hist is None or hist.empty or "Close" not in hist.columns:
                    continue
                close_s = hist["Close"].dropna()
                if close_s.empty:
                    continue
                curr_f = _json_safe_float(close_s.iloc[-1], ndigits=2)
                pct_f: float | None = None
                if len(close_s) >= 2:
                    prev_f = _json_safe_float(close_s.iloc[-2], ndigits=None)
                    if curr_f is not None and prev_f is not None and prev_f != 0:
                        pct_f = _json_safe_float(
                            (float(close_s.iloc[-1]) - float(close_s.iloc[-2]))
                            / float(close_s.iloc[-2])
                            * 100.0,
                            ndigits=2,
                        )
                결과[market] = {"현재가": curr_f, "등락률": pct_f}
            except Exception:
                continue
        # 지수만 Close 가 비는 경우(환율은 정상) — ETF 프록시
        if not 결과.get("코스피") or 결과["코스피"].get("현재가") is None:
            c, p = _yfinance_지수_또는_프록시(["^KS11", "069500.KS", "122630.KS"])
            if c is not None:
                결과["코스피"] = {"현재가": c, "등락률": p}
        if not 결과.get("코스닥") or 결과["코스닥"].get("현재가") is None:
            c, p = _yfinance_지수_또는_프록시(["^KQ11", "229200.KS"])
            if c is not None:
                결과["코스닥"] = {"현재가": c, "등락률": p}
    except Exception:
        return None

    return 결과


def get_top_traded_stocks(
    limit: int = 10, market: str = "KOSPI", sort_by: str = "거래대금"
) -> tuple[list[dict], str | None]:
    """
    거래대금 또는 거래량 상위 종목 반환. 장 마감 후에도 최근 영업일 기준.
    market: KOSPI, KOSDAQ
    sort_by: 거래대금(기본) | 거래량 또는 volume/vol 별칭
    반환: (목록, 기준일 YYYY-MM-DD 또는 None)
    - KRX 연결 실패 시 yfinance 폴백
    """
    sort_by = _normalize_top_traded_sort(sort_by)
    try:
        from pykrx import stock
    except ImportError:
        return _get_top_traded_yfinance_fallback(limit, market, sort_by=sort_by)

    def _col(df, name: str, idx: int):
        if name in df.columns:
            return df[name]
        if 0 <= idx < len(df.columns):
            return df.iloc[:, idx]
        return None

    def _safe_float(v):
        try:
            if v is None:
                return 0.0
            f = float(v)
            import math
            return 0.0 if math.isnan(f) else f
        except (TypeError, ValueError):
            return 0.0

    try:
        # 장 마감·휴일·동기화 지연 포함해 최근 35일까지 시도
        for d in range(0, 35):
            날짜 = _최근_영업일(d)
            try:
                df = stock.get_market_ohlcv_by_ticker(날짜, market=market)
            except Exception:
                continue
            if df is None or df.empty:
                continue
            col_거래대금 = _col(df, _COL_거래대금, 5)
            col_거래량 = _col(df, _COL_거래량, 4)
            if sort_by == "거래량":
                if col_거래량 is None:
                    continue
            else:
                if col_거래대금 is None:
                    continue
            df = df.copy()
            df["_거래대금"] = col_거래대금 if col_거래대금 is not None else 0
            df["_거래량"] = col_거래량 if col_거래량 is not None else 0
            # 등락률: 컬럼명 인코딩 깨짐 시 iloc[6] 이 어긋날 수 있어 _col 로 고정
            col_등락률 = _col(df, _COL_등락률, 6)
            if col_등락률 is not None:
                df["_등락률"] = col_등락률
            else:
                df["_등락률"] = 0.0
            sort_col = "_거래량" if sort_by == "거래량" else "_거래대금"
            df_top = df.sort_values(sort_col, ascending=False).head(limit)
            # 코스닥 등에서 인덱스 중복 시 df.loc[라벨] 이 DataFrame 이 되어 두 번째 행에서 전체 요청이 실패할 수 있음 → iterrows
            이름맵: dict[str, str] = {}
            try:
                from pykrx.website.krx.market.wrap import get_market_ticker_and_name

                이름맵 = _krx_이름_series를_맵으로(get_market_ticker_and_name(날짜, market))
            except Exception:
                이름맵 = {}
            if not 이름맵:
                이름맵 = _krx_한글명_맵_최근일(market)

            def _이름_찾기(티커6: str) -> str:
                if len(티커6) == 6:
                    nm = 이름맵.get(티커6)
                    if nm:
                        return nm
                return _종목명_pykrx(티커6)

            결과 = []
            for 티커_raw, row in df_top.iterrows():
                티커 = _normalize_krx_ticker(티커_raw) or str(티커_raw).strip()
                if not re.fullmatch(r"\d{6}", str(티커)):
                    m = re.search(r"\d{6}", str(티커))
                    티커 = m.group(0) if m else str(티커)
                이름 = _이름_찾기(str(티커)) if re.fullmatch(r"\d{6}", str(티커)) else str(티커)
                거래대금 = _safe_float(
                    row.get("_거래대금")
                    or row.get(_COL_거래대금)
                    or (row.iloc[5] if len(row) > 5 else 0)
                )
                거래량 = _safe_float(
                    row.get("_거래량")
                    or row.get(_COL_거래량)
                    or (row.iloc[4] if len(row) > 4 else 0)
                )
                종가 = _safe_float(
                    row.get(_COL_종가) or (row.iloc[3] if len(row) > 3 else 0)
                )
                등락률 = _safe_float(row.get("_등락률"))
                결과.append({
                    "티커": str(티커),
                    "종목명": 이름 or str(티커),
                    "종가": 종가,
                    "거래대금": 거래대금,
                    "거래량": 거래량,
                    "등락률": 등락률,
                })
            # KRX 맵/pykrx 가 빈 환경 → 네이버 API 로 한글명 일괄 보강
            need_nv = [
                r["티커"]
                for r in 결과
                if re.fullmatch(r"\d{6}", str(r["티커"]))
                and (
                    str(r["종목명"]) == str(r["티커"])
                    or re.fullmatch(r"\d{6}", str(r["종목명"]))
                )
            ]
            if need_nv:
                _네이버_종목명_병렬(need_nv)
                for r in 결과:
                    tc = str(r["티커"])
                    if tc in _NAVER_NAME_CACHE:
                        r["종목명"] = _NAVER_NAME_CACHE[tc]
            # 기준일을 YYYY-MM-DD 형태로 반환 (장 마감 후에도 '최근 영업일 종가'임을 표시용)
            기준일 = f"{날짜[:4]}-{날짜[4:6]}-{날짜[6:8]}"
            return (결과, 기준일)
    except Exception:
        pass
    # pykrx 실패 시 yfinance로 대표 종목 추정
    return _get_top_traded_yfinance_fallback(limit, market, sort_by=sort_by)


def _get_top_traded_yfinance_fallback(
    limit: int, market: str, sort_by: str = "거래대금"
) -> tuple[list[dict], str | None]:
    """
    pykrx 실패 시 yfinance 배치 다운로드로 종가·거래량·거래대금(추정) 후 상위 반환.
    - 종목명은 yfinance info 를 쓰지 않음(한국 종목에서 '035720.KQ,0P0000...' 등 오염).
    - 티커 풀·배치 요청으로 코스피 0건·7건만 나오는 현상 완화.
    """
    sort_by = _normalize_top_traded_sort(sort_by)
    import yfinance as yf

    tickers_raw = _FALLBACK_KOSPI if market == "KOSPI" else _FALLBACK_KOSDAQ
    suffix = ".KS" if market == "KOSPI" else ".KQ"
    tickers = [t + suffix for t in tickers_raw]
    result_list: list[dict] = []
    기준일: str | None = None
    _배치크기 = 35
    # yfinance 폴백도 당일 KRX 명칭 표로 한글명 매칭 (get_market_ticker_name 만으로는 빈 문자가 나오는 환경 있음)
    한글맵: dict[str, str] = _krx_한글명_맵_최근일(market)

    try:
        for i in range(0, len(tickers), _배치크기):
            chunk = tickers[i : i + _배치크기]
            try:
                raw = yf.download(
                    chunk,
                    period="5d",
                    interval="1d",
                    group_by="ticker",
                    threads=False,
                    progress=False,
                    auto_adjust=True,
                )
            except Exception:
                continue
            if raw is None or raw.empty:
                continue
            for sym in chunk:
                t_clean = sym.replace(suffix, "")
                ckey = (sym, "Close")
                if ckey not in raw.columns:
                    continue
                close_s = raw[ckey].dropna()
                if close_s.empty:
                    continue
                last_c_ok = _json_safe_float(close_s.iloc[-1], ndigits=4)
                if last_c_ok is None:
                    continue
                vkey = (sym, "Volume")
                if vkey in raw.columns:
                    vol_series = raw[vkey].dropna()
                    vol_raw = float(vol_series.iloc[-1]) if not vol_series.empty else 0.0
                else:
                    vol_raw = 0.0
                last_v_ok = _json_safe_float(vol_raw, ndigits=None) or 0.0
                money_ok = _json_safe_float(last_c_ok * last_v_ok, ndigits=2) or 0.0
                pct = 0.0
                if len(close_s) >= 2:
                    prev_ok = _json_safe_float(close_s.iloc[-2], ndigits=None)
                    if prev_ok is not None and prev_ok != 0:
                        pct_val = (last_c_ok - prev_ok) / prev_ok * 100.0
                        pct_round = _json_safe_float(pct_val, ndigits=2)
                        pct = pct_round if pct_round is not None else 0.0
                if 기준일 is None:
                    last_ix = close_s.index[-1]
                    if hasattr(last_ix, "strftime"):
                        기준일 = last_ix.strftime("%Y-%m-%d")
                result_list.append({
                    "티커": t_clean,
                    "종목명": 한글맵.get(t_clean) or _종목명_pykrx(t_clean),
                    "종가": round(last_c_ok, 2),
                    "거래대금": money_ok,
                    "거래량": last_v_ok,
                    "등락률": pct,
                })
        # 배치가 일부만 성공할 때(코스닥 1건 등) 남은 티커는 심볼 단위로 보충
        sort_key = "거래량" if sort_by == "거래량" else "거래대금"
        seen_tickers = {r["티커"] for r in result_list}
        for t in tickers_raw:
            if t in seen_tickers:
                continue
            sym = t + suffix
            try:
                hist = yf.Ticker(sym).history(period="5d")
                if hist is None or hist.empty or "Close" not in hist.columns:
                    continue
                close_s = hist["Close"].dropna()
                if close_s.empty:
                    continue
                last_c_ok = _json_safe_float(close_s.iloc[-1], ndigits=4)
                if last_c_ok is None:
                    continue
                vol_series = hist["Volume"].dropna() if "Volume" in hist.columns else None
                vol_raw = float(vol_series.iloc[-1]) if vol_series is not None and not vol_series.empty else 0.0
                last_v_ok = _json_safe_float(vol_raw, ndigits=None) or 0.0
                money_ok = _json_safe_float(last_c_ok * last_v_ok, ndigits=2) or 0.0
                pct = 0.0
                if len(close_s) >= 2:
                    prev_ok = _json_safe_float(close_s.iloc[-2], ndigits=None)
                    if prev_ok is not None and prev_ok != 0:
                        pct_val = (last_c_ok - prev_ok) / prev_ok * 100.0
                        pr = _json_safe_float(pct_val, ndigits=2)
                        pct = pr if pr is not None else 0.0
                if 기준일 is None:
                    lix = close_s.index[-1]
                    if hasattr(lix, "strftime"):
                        기준일 = lix.strftime("%Y-%m-%d")
                result_list.append({
                    "티커": t,
                    "종목명": 한글맵.get(t) or _종목명_pykrx(t),
                    "종가": round(last_c_ok, 2),
                    "거래대금": money_ok,
                    "거래량": last_v_ok,
                    "등락률": pct,
                })
                seen_tickers.add(t)
            except Exception:
                continue
        need_nv = [
            r["티커"]
            for r in result_list
            if re.fullmatch(r"\d{6}", str(r["티커"]))
            and (
                str(r["종목명"]) == str(r["티커"])
                or re.fullmatch(r"\d{6}", str(r["종목명"]))
            )
        ]
        if need_nv:
            _네이버_종목명_병렬(need_nv)
            for r in result_list:
                tc = str(r["티커"])
                if tc in _NAVER_NAME_CACHE:
                    r["종목명"] = _NAVER_NAME_CACHE[tc]
        merged: dict[str, dict] = {}
        for r in result_list:
            tk = r["티커"]
            if tk not in merged or r[sort_key] > merged[tk][sort_key]:
                merged[tk] = r
        result_list = sorted(merged.values(), key=lambda x: x[sort_key], reverse=True)
        if not 기준일:
            기준일 = datetime.now().strftime("%Y-%m-%d")
        return (result_list[:limit], 기준일)
    except Exception:
        return ([], None)


def get_top_traded_etfs(limit: int = 10) -> list[dict]:
    """
    ETF 거래대금 상위 종목 반환.
    - KRX 연결 실패 시 [] 반환
    """
    try:
        from pykrx import stock
    except ImportError:
        return []

    try:
        for d in range(0, 5):
            날짜 = _최근_영업일(d)
            try:
                df = stock.get_etf_ohlcv_by_ticker(날짜)
            except Exception:
                continue
            if df is not None and not df.empty and "거래대금" in df.columns:
                df = df.sort_values("거래대금", ascending=False).head(limit)
                결과 = []
                for 티커 in df.index:
                    try:
                        이름 = stock.get_etf_ticker_name(티커)
                    except Exception:
                        이름 = str(티커)
                    row = df.loc[티커]
                    거래대금 = row.get("거래대금", 0) or 0
                    종가 = row.get("종가", 0) or 0
                    등락률 = row.get("등락률", 0) or 0  # ETF는 등락률 없을 수 있음
                    결과.append({
                        "티커": str(티커),
                        "종목명": 이름 or str(티커),
                        "종가": _json_safe_float(종가, ndigits=2) or 0.0,
                        "거래대금": _json_safe_float(거래대금, ndigits=2) or 0.0,
                        "등락률": _json_safe_float(등락률, ndigits=2) or 0.0,
                    })
                return 결과
    except Exception:
        return []
    return []


def get_top_gainers_losers(limit: int = 5, market: str = "KOSPI") -> dict:
    """
    등락률 상위/하위 종목 반환.
    - KRX 연결 실패 시 {"상승": [], "하락": []} 반환
    """
    try:
        from pykrx import stock
    except ImportError:
        return {"상승": [], "하락": []}

    try:
        for d in range(0, 5):
            날짜 = _최근_영업일(d)
            try:
                df = stock.get_market_ohlcv_by_ticker(날짜, market=market)
            except Exception:
                continue
            if df is not None and not df.empty and "등락률" in df.columns:
                df = df[df["등락률"].notna()]
                df_상승 = df[df["등락률"] > 0].sort_values("등락률", ascending=False).head(limit)
                df_하락 = df[df["등락률"] < 0].sort_values("등락률", ascending=True).head(limit)
                상승목록 = []
                하락목록 = []
                for 티커 in df_상승.index:
                    try:
                        이름 = stock.get_market_ticker_name(티커)
                    except Exception:
                        이름 = str(티커)
                    row = df_상승.loc[티커]
                    상승목록.append({
                        "티커": str(티커),
                        "종목명": 이름 or str(티커),
                        "종가": _json_safe_float(row.get("종가", 0) or 0, ndigits=2) or 0.0,
                        "등락률": _json_safe_float(row.get("등락률", 0) or 0, ndigits=2) or 0.0,
                    })
                for 티커 in df_하락.index:
                    try:
                        이름 = stock.get_market_ticker_name(티커)
                    except Exception:
                        이름 = str(티커)
                    row = df_하락.loc[티커]
                    하락목록.append({
                        "티커": str(티커),
                        "종목명": 이름 or str(티커),
                        "종가": _json_safe_float(row.get("종가", 0) or 0, ndigits=2) or 0.0,
                        "등락률": _json_safe_float(row.get("등락률", 0) or 0, ndigits=2) or 0.0,
                    })
                return {"상승": 상승목록, "하락": 하락목록}
    except Exception:
        pass
    return {"상승": [], "하락": []}
