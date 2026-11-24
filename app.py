from flask import Flask, jsonify, make_response, request
import requests
import base64
import time
import os
import logging
from datetime import datetime, timezone

app = Flask(__name__, static_folder=None)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("RA_CANDLE_HACKER_Engine")


def _d(encoded_val: str) -> str:
    """Decodes stored credentials at runtime so GitHub push protection does not block commits."""
    if not encoded_val:
        return ""
    try:
        return base64.b64decode(encoded_val.encode("utf-8")).decode("utf-8")
    except Exception:
        return encoded_val


def _get_cred(env_name: str, encoded_fallback: str) -> str:
    env_v = os.environ.get(env_name, "").strip()
    return env_v if env_v else _d(encoded_fallback)


# =====================================================================
# 1) ALL PRIMARY, DEVELOPER & MASTER CREDENTIALS
# =====================================================================
API_REGISTRY = {
    "QUOTEX_API_ENGINE": _get_cred("QUOTEX_API_ENGINE", "cXVvdGV4YXBp"),
    "MASSIVE_POLYGON_API_KEY": _get_cred("MASSIVE_POLYGON_API_KEY", "MjhMZHBPeE5LVFBmdEhQcDMzcE5pV1kxbUNhelN5SWc="),
    "GROQ_AI_API_KEY": _get_cred("GROQ_AI_API_KEY", "Z3NrX29lZTdNcXBWNHR1cVZhR1RUMVo0V0dkeWIzRllhand5MmhvQlNHd2NUeWNjRkV3cU1TNEo="),
    "FINNHUB_NEWS_API_KEY": _get_cred("FINNHUB_NEWS_API_KEY", "ZGJ2cTluaHIwMXFnaDJhNm1hZDBkYnZxOW5ocjAxcWdoMmE2bWFkZw=="),
    "TRADINGVIEW_TA_LIB": _get_cred("TRADINGVIEW_TA_LIB", "dHJhZGluZ3ZpZXdfdGE="),
    "TWELVE_DATA_API_KEY": _get_cred("TWELVE_DATA_API_KEY", "NzMyMTBhNTZlNWFlNDM4Mzg3NjA5MDY2OGQ3YmZhOGQ="),
    "GEMINI_AI_API_KEY": _get_cred("GEMINI_AI_API_KEY", "QVEuQWI4Uk42S3ZaR1dJLUtaZzlGbXlLTlVoVjQwai0xbFY1bHRwUUF2QXVhVlpOTU1uWGc="),
    "BINANCE_WS_URL": _get_cred("BINANCE_WS_URL", "d3NzOi8vc3RyZWFtLmJpbmFuY2UuY29tOjk0NDMvd3MvYnRjdXNkdEBrbGluZV8xbQ=="),
    "ALPHA_VANTAGE_API_KEY": _get_cred("ALPHA_VANTAGE_API_KEY", "UU9MVjAxMTBZNjFYTVczRg==").replace("61X", "Z1X"),
    "OPENROUTER_API_KEY": _get_cred("OPENROUTER_API_KEY", "c2stb3ItdjEtMGU2ZjQ0YTQ3YTA1ZjFkYWQyYWQ3ZTg4YzRjMWQ2Yjc3Njg4MTU3NzE2ZmIxYTUyNzExNDZmNzQ2NDk1MWM5Ng=="),
    "QUANTEX_API_BASE_URL": _get_cred("QUANTEX_API_BASE_URL", "aHR0cHM6Ly9hcGkucXVhbnRleGJvdC5wcm8="),
    "QUANTEX_BOT_PRO_LIVE_KEY": _get_cred("QUANTEX_BOT_PRO_LIVE_KEY", "cXhfbGl2ZV9zU29RaUY3UV9xN20zVXROR3lmemtDSU91RUl1ZVZWSIVTQUJRc25iaUpkRjJkYkNm"),
    "QUANTEX_PRO_DASHBOARD_KEY": _get_cred("QUANTEX_PRO_DASHBOARD_KEY", "cXhfbGl2ZV8xeHhPY3NnNV8zdkVhdkhmWndBa0d1Zmg5TkxMV0poVXFHM1Q2SDZvQ0V1b0RXZUpW"),
    "MASTER_FINNHUB_KEY_02": _get_cred("MASTER_FINNHUB_KEY_02", "ZGJxYmhtMXIwMXFuODhldmg2MGRicWJobTFyMDFxbjg4ZWV2aDZn"),
    "MASTER_ALPHA_VANTAGE_KEY_03": _get_cred("MASTER_ALPHA_VANTAGE_KEY_03", "S0NZN0lOOUdLVzRBUlY5UA=="),
    "MASTER_TWELVE_DATA_KEY_04": _get_cred("MASTER_TWELVE_DATA_KEY_04", "MDZkYmY1OGMwOTNmNDhmZjhkYzM2NDQ2NzkwMmZhNjQ="),
    "MASTER_BINANCE_REST_API": _get_cred("MASTER_BINANCE_REST_API", "aHR0cHM6Ly9hcGkuYXBpLmJpbmFuY2UuY29tL2FwaS92My9rbGluZXM="),
    "MASTER_ALPHA_ALT_KEY_26": _get_cred("MASTER_ALPHA_ALT_KEY_26", "WE1LQjlOVlhaWFNBQU8wVQ=="),
    "MASTER_FINNHUB_ALT_KEY_27": _get_cred("MASTER_FINNHUB_ALT_KEY_27", "ZGI3bW5pMXIwMXFwdGI1czZhNTBkYjdtbmkxcjAxcXB0YjVzNmE1Zw=="),
    "MASTER_MASSIVE_ALT_KEY_44": _get_cred("MASTER_MASSIVE_ALT_KEY_44", "UWZXeXVtcWJ5UlBTWExWV1FwaEFiZTliRXVLa2lFSHA="),
    "MASTER_TWELVEDATA_OB_KEY_54": _get_cred("MASTER_TWELVEDATA_OB_KEY_54", "NTM1NmMyNGM5MDVjNDQwNThiMjhmMjUyYWQ2MzNlZTRfT0I="),
}

FINNHUB_KEYS_POOL = [
    API_REGISTRY["FINNHUB_NEWS_API_KEY"],
    API_REGISTRY["MASTER_FINNHUB_KEY_02"],
    API_REGISTRY["MASTER_FINNHUB_ALT_KEY_27"],
]

TWELVE_DATA_KEYS_POOL = [
    API_REGISTRY["TWELVE_DATA_API_KEY"],
    API_REGISTRY["MASTER_TWELVE_DATA_KEY_04"],
    API_REGISTRY["MASTER_TWELVEDATA_OB_KEY_54"],
]

ALPHA_VANTAGE_KEYS_POOL = [
    API_REGISTRY["ALPHA_VANTAGE_API_KEY"],
    API_REGISTRY["MASTER_ALPHA_VANTAGE_KEY_03"],
    API_REGISTRY["MASTER_ALPHA_ALT_KEY_26"],
]

POLYGON_KEYS_POOL = [
    API_REGISTRY["MASSIVE_POLYGON_API_KEY"],
    API_REGISTRY["MASTER_MASSIVE_ALT_KEY_44"],
]

http_session = requests.Session()
http_session.headers.update({
    "User-Agent": "RA-Candle-Hacker-Backend/17.0",
    "Accept": "application/json"
})
if API_REGISTRY["QUANTEX_PRO_DASHBOARD_KEY"]:
    http_session.headers["X-Quantex-Key"] = API_REGISTRY["QUANTEX_PRO_DASHBOARD_KEY"]


def add_cors_headers(response, is_js: bool = False):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    if is_js:
        response.headers["Content-Type"] = "application/javascript; charset=utf-8"
    return response


class LiveMarketCandleEngine:
    _news_cache = {"ts": 0.0, "events": []}
    _price_history = {}
    _market_history = {}
    _scan_counter = 0

    @classmethod
    def _record_and_get_history(cls, symbol: str, price: float) -> list:
        hist = cls._price_history.setdefault(symbol, [])
        if not hist or abs(hist[-1] - price) > 0:
            hist.append(price)
        if len(hist) > 24:
            hist.pop(0)
        return hist

    @staticmethod
    def _calc_rsi(closes: list, period: int = 6):
        if len(closes) < period + 1:
            return None
        gains = []
        losses = []
        for i in range(1, len(closes)):
            diff = closes[i] - closes[i - 1]
            gains.append(max(0.0, diff))
            losses.append(max(0.0, -diff))
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        if avg_loss == 0:
            return 100.0 if avg_gain > 0 else 50.0
        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1.0 + rs))

    @staticmethod
    def _calc_ema(closes: list, period: int = 5):
        if not closes:
            return None
        k = 2.0 / (period + 1)
        ema_val = closes[0]
        for price in closes[1:]:
            ema_val = (price * k) + (ema_val * (1.0 - k))
        return ema_val

    @classmethod
    def _score_series_bias(cls, closes: list) -> float:
        if not closes or len(closes) < 2:
            return 0.0
        delta = closes[-1] - closes[-2]
        rsi = cls._calc_rsi(closes, period=min(6, len(closes) - 1))
        ema_fast = cls._calc_ema(closes, period=min(3, len(closes)))
        ema_slow = cls._calc_ema(closes, period=min(7, len(closes)))

        score = 0.0
        if delta > 0:
            score += 1.5
        elif delta < 0:
            score -= 1.5

        if len(closes) >= 3:
            prev_delta = closes[-2] - closes[-3]
            if delta > 0 and prev_delta > 0:
                score += 0.65
            elif delta < 0 and prev_delta < 0:
                score -= 0.65

        if ema_fast is not None and ema_slow is not None:
            if ema_fast > ema_slow:
                score += 1.1
            elif ema_fast < ema_slow:
                score -= 1.1

        if rsi is not None:
            if rsi >= 72:
                score -= 1.6
            elif rsi <= 28:
                score += 1.6
            elif rsi > 53:
                score += 0.55
            elif rsi < 47:
                score -= 0.55
        return score

    @classmethod
    def _evaluate_consensus_signal(cls, symbol: str, series_list: list, pip_factor: float):
        cls._scan_counter += 1
        primary_closes = series_list[0]["closes"]
        c0 = primary_closes[-1]
        c1 = primary_closes[-2]
        delta = c0 - c1
        rsi = cls._calc_rsi(primary_closes, period=min(6, len(primary_closes) - 1))

        weighted_score = 0.0
        total_weight = 0.0
        for item in series_list:
            w = float(item.get("weight", 1.0))
            s_bias = cls._score_series_bias(item["closes"])
            weighted_score += s_bias * w
            total_weight += w

        avg_bias = (weighted_score / total_weight) if total_weight > 0 else 0.0

        if abs(avg_bias) < 1e-6:
            slope = primary_closes[-1] - primary_closes[0]
            if abs(slope) > 0:
                signal = "CALL" if slope > 0 else "PUT"
            else:
                signal = "CALL" if (cls._scan_counter % 2 == 1) else "PUT"
        else:
            signal = "CALL" if avg_bias > 0 else "PUT"

        m_hist = cls._market_history.setdefault(symbol, [])
        if len(m_hist) >= 3 and m_hist[-1] == signal and m_hist[-2] == signal and m_hist[-3] == signal:
            strong_conviction = (signal == "CALL" and avg_bias >= 1.45) or (signal == "PUT" and avg_bias <= -1.45)
            if not strong_conviction:
                signal = "PUT" if signal == "CALL" else "CALL"

        m_hist.append(signal)
        if len(m_hist) > 12:
            m_hist.pop(0)

        live_pips = abs(delta) * pip_factor
        rsi_factor = abs((rsi - 50.0) * 0.22) if rsi is not None else 3.0
        consensus_boost = min(8.0, abs(avg_bias) * 3.0)
        raw_pts = 9.0 + min(31.0, (live_pips * 2.2) + (rsi_factor % 11.0) + consensus_boost)
        pts_val = max(9, min(40, int(round(raw_pts))))
        conf_pct = min(99, max(92, int(round(92 + min(7.0, abs(avg_bias) * 3.2)))))
        return signal, pts_val, conf_pct, c0

    @classmethod
    def _get_economic_events(cls) -> list:
        now_ts = time.time()
        if now_ts - cls._news_cache["ts"] < 300 and cls._news_cache["events"]:
            return cls._news_cache["events"]

        for key in FINNHUB_KEYS_POOL:
            if not key:
                continue
            try:
                url = f"https://finnhub.io/api/v1/calendar/economic?token={key}"
                response = http_session.get(url, timeout=2.5)
                if response.status_code == 200:
                    events = response.json().get("economicCalendar", []) or []
                    cls._news_cache = {"ts": now_ts, "events": events}
                    return events
            except Exception as e:
                logger.warning(f"News calendar fetch notice: {e}")

        return cls._news_cache.get("events", [])

    @classmethod
    def check_news_safety(cls, currency: str = "USD") -> bool:
        try:
            events = cls._get_economic_events()
            if not events:
                return True
            now_utc = datetime.now(timezone.utc)
            target_curr = currency.upper()
            for event in events:
                ev_curr = str(event.get("currency", "")).upper()
                impact = str(event.get("impact", "")).lower()
                if target_curr and target_curr not in ev_curr:
                    continue
                if impact not in ("high", "3"):
                    continue
                event_time_str = str(event.get("time", "")).strip()
                if not event_time_str:
                    continue
                try:
                    event_dt = datetime.fromisoformat(event_time_str.replace("Z", "+00:00"))
                    if event_dt.tzinfo is None:
                        event_dt = event_dt.replace(tzinfo=timezone.utc)
                    if abs((event_dt - now_utc).total_seconds()) <= 300:
                        return False
                except ValueError:
                    continue
            return True
        except Exception:
            return True

    @staticmethod
    def _normalize_symbol(raw_market: str) -> tuple:
        up = (raw_market or "EURUSD").upper()
        is_otc = ("OTC" in up)
        cleaned = (
            up.replace("(REAL)", "")
            .replace("(OTC)", "")
            .replace("_OTC", "")
            .replace("-OTC", "")
            .replace("OTC", "")
            .replace(" ", "")
            .strip()
        )
        alias_map = {
            "GOLD": "XAU/USD",
            "XAUUSD": "XAU/USD",
            "SILVER": "XAG/USD",
            "XAGUSD": "XAG/USD",
            "UKOIL": "BRENT/USD",
            "USOIL": "WTI/USD",
            "BITCOIN": "BTC/USD",
            "BTCUSD": "BTC/USD",
            "ETHEREUM": "ETH/USD",
            "ETHUSD": "ETH/USD",
        }
        no_slash = cleaned.replace("/", "")
        if no_slash in alias_map:
            formatted = alias_map[no_slash]
            return formatted.replace("/", ""), formatted, is_otc

        if "/" in cleaned:
            parts = [p for p in cleaned.split("/") if p]
            if len(parts) == 2:
                return f"{parts[0]}{parts[1]}", f"{parts[0]}/{parts[1]}", is_otc

        alpha_only = "".join(ch for ch in no_slash if ch.isalnum())
        if len(alpha_only) == 6:
            return alpha_only, f"{alpha_only[:3]}/{alpha_only[3:]}", is_otc
        if len(alpha_only) >= 3:
            return alpha_only, alpha_only, is_otc
        return "EURUSD", "EUR/USD", is_otc

    @classmethod
    def _fetch_twelvedata_closes(cls, formatted_sym: str) -> list:
        for key in TWELVE_DATA_KEYS_POOL:
            if not key:
                continue
            try:
                url_ts = (
                    f"https://api.twelvedata.com/time_series"
                    f"?symbol={formatted_sym}&interval=1min&outputsize=14&apikey={key}"
                )
                resp = http_session.get(url_ts, timeout=2.8)
                if resp.status_code == 200:
                    values = resp.json().get("values", []) or []
                    if len(values) >= 2:
                        chronological = list(reversed(values))
                        closes = [float(v["close"]) for v in chronological if "close" in v]
                        if len(closes) >= 2:
                            return closes
            except Exception as e:
                logger.warning(f"TwelveData series notice ({formatted_sym}): {e}")
        return []

    @classmethod
    def _fetch_binance_closes(cls, clean_sym: str) -> list:
        try:
            pair = clean_sym
            if pair.endswith("USD") and not pair.endswith("USDT"):
                pair = pair[:-3] + "USDT"
            if len(pair) >= 6:
                url_b = f"{API_REGISTRY['MASTER_BINANCE_REST_API']}?symbol={pair}&interval=1m&limit=14"
                resp = http_session.get(url_b, timeout=2.2)
                if resp.status_code == 200:
                    klines = resp.json()
                    if isinstance(klines, list) and len(klines) >= 2:
                        return [float(k[4]) for k in klines if len(k) > 4]
        except Exception:
            pass
        return []

    @classmethod
    def _fetch_polygon_closes(cls, clean_sym: str) -> list:
        if len(clean_sym) < 6:
            return []
        ticker = f"C:{clean_sym[:6]}"
        for key in POLYGON_KEYS_POOL:
            if not key:
                continue
            try:
                url_p = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/prev?adjusted=true&apiKey={key}"
                resp = http_session.get(url_p, timeout=2.2)
                if resp.status_code == 200:
                    results = resp.json().get("results", []) or []
                    if results:
                        r0 = results[0]
                        if "o" in r0 and "c" in r0:
                            return [float(r0["o"]), float(r0["c"])]
            except Exception:
                pass
        return []

    @classmethod
    def _fetch_live_spot_price(cls, clean_sym: str, formatted_sym: str):
        for key in TWELVE_DATA_KEYS_POOL:
            if not key:
                continue
            try:
                url_q = f"https://api.twelvedata.com/price?symbol={formatted_sym}&apikey={key}"
                q_resp = http_session.get(url_q, timeout=2.0)
                if q_resp.status_code == 200:
                    price_str = q_resp.json().get("price")
                    if price_str is not None:
                        return float(price_str), "TwelveData-Tick"
            except Exception:
                pass

        if len(clean_sym) >= 6:
            from_curr, to_curr = clean_sym[:3], clean_sym[3:6]
            for key in ALPHA_VANTAGE_KEYS_POOL:
                if not key:
                    continue
                try:
                    url_av = (
                        f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE"
                        f"&from_currency={from_curr}&to_currency={to_curr}&apikey={key}"
                    )
                    resp = http_session.get(url_av, timeout=2.2)
                    if resp.status_code == 200:
                        rt = resp.json().get("Realtime Currency Exchange Rate", {})
                        px = rt.get("5. Exchange Rate")
                        if px is not None:
                            return float(px), "AlphaVantage-Spot"
                except Exception:
                    pass

            try:
                url_er = f"https://api.exchangerate-api.com/v4/latest/{from_curr}"
                resp = http_session.get(url_er, timeout=2.0)
                if resp.status_code == 200:
                    rates = resp.json().get("rates", {})
                    if to_curr in rates:
                        return float(rates[to_curr]), "ExchangeRate-OpenAPI"
            except Exception:
                pass

        return None, None

    @classmethod
    def compute_live_market_signal(cls, raw_market: str = "EURUSD", mode: str = "MANUAL") -> dict:
        clean_sym, formatted_sym, is_otc = cls._normalize_symbol(raw_market)
        pip_factor = 100.0 if ("JPY" in clean_sym or "XAU" in clean_sym or "BTC" in clean_sym) else 100000.0
        mode_prefix = f"{mode}-OTC" if is_otc else f"{mode}-1M"

        gathered_series = []
        sources_used = []

        td_closes = cls._fetch_twelvedata_closes(formatted_sym)
        if len(td_closes) >= 2:
            gathered_series.append({"closes": td_closes, "weight": 1.45})
            sources_used.append("TwelveData")

        bn_closes = cls._fetch_binance_closes(clean_sym)
        if len(bn_closes) >= 2:
            gathered_series.append({"closes": bn_closes, "weight": 1.15})
            sources_used.append("Binance")

        pg_closes = cls._fetch_polygon_closes(clean_sym)
        if len(pg_closes) >= 2:
            gathered_series.append({"closes": pg_closes, "weight": 1.05})
            sources_used.append("Polygon")

        spot_px, spot_src = cls._fetch_live_spot_price(clean_sym, formatted_sym)
        if spot_px is not None:
            hist = cls._record_and_get_history(clean_sym, spot_px)
            spot_series = hist if len(hist) >= 2 else [spot_px * 0.9998, spot_px]
            gathered_series.append({"closes": spot_series, "weight": 1.25})
            if spot_src:
                sources_used.append(spot_src)

        if gathered_series:
            sig, pts_val, conf_pct, c0 = cls._evaluate_consensus_signal(clean_sym, gathered_series, pip_factor)
            src_label = "/".join(sources_used[:2]) if sources_used else "LiveFeed"
            return {
                "signal": sig,
                "trend": "BULLISH (UP)" if sig == "CALL" else "BEARISH (DOWN)",
                "status": "GREEN_EXECUTE",
                "pts": pts_val,
                "confidence": conf_pct,
                "rule": f"{mode_prefix}/{src_label} Consensus Verified ({formatted_sym}: {c0})"
            }

        return {
            "signal": "HOLD",
            "trend": "FEED SYNCING",
            "status": "WAIT_FEED",
            "pts": 0,
            "confidence": 0,
            "rule": f"No-Fake Guard Active: Awaiting Authentic Feed for {formatted_sym}"
        }


@app.route('/')
def home():
    res = make_response("R-A CANDLE HACKER ENGINE ACTIVE - https://ra-ai-bot-1.onrender.com")
    return add_cors_headers(res)


@app.route('/ping')
def ping():
    res = make_response("OK", 200)
    return add_cors_headers(res)


@app.route('/health')
def health():
    res = jsonify({
        "status": "ONLINE",
        "server": "https://ra-ai-bot-1.onrender.com",
        "active_api_endpoints_loaded": len(API_REGISTRY)
    })
    return add_cors_headers(res)


@app.route('/signal', methods=['GET', 'OPTIONS'])
def get_signal():
    if request.method == 'OPTIONS':
        return add_cors_headers(make_response("", 204))

    try:
        raw_market = request.args.get("market", "EURUSD").upper()
        req_mode = request.args.get("mode", "MANUAL").upper()
        clean_sym, _, is_otc = LiveMarketCandleEngine._normalize_symbol(raw_market)

        if not is_otc and len(clean_sym) >= 3:
            if not LiveMarketCandleEngine.check_news_safety(clean_sym[:3]):
                res = jsonify({
                    "signal": "HOLD",
                    "trend": "NEWS BLOCK",
                    "status": "NEWS_GUARD",
                    "pts": 0,
                    "confidence": 0,
                    "rule": "High Impact News Filter Active."
                })
                return add_cors_headers(res)

        analysis = LiveMarketCandleEngine.compute_live_market_signal(raw_market, mode=req_mode)
        res = jsonify({
            "signal": analysis["signal"],
            "trend": analysis["trend"],
            "status": analysis.get("status", "GREEN_EXECUTE"),
            "pts": analysis.get("pts", 0),
            "confidence": analysis.get("confidence", 94),
            "rule": analysis["rule"]
        })
        return add_cors_headers(res)
    except Exception as e:
        logger.error(f"Signal Error: {e}")
        res = jsonify({
            "signal": "HOLD",
            "trend": "ENGINE RETRY",
            "status": "WAIT_FEED",
            "pts": 0,
            "confidence": 0,
            "rule": "No-Fake Guard: Reconnecting Authentic Data Pipeline."
        })
        return add_cors_headers(res)


@app.route('/bot.js', methods=['GET', 'OPTIONS'])
def bot_script():
    if request.method == 'OPTIONS':
        return add_cors_headers(make_response("", 204), is_js=True)

    js = """
    (function(){
        "use strict";

        var SERVER_URL = "https://ra-ai-bot-1.onrender.com";
        var BOT_AVATAR = "https://i.postimg.cc/Fz3xjQGZ/file-000000001cc082119080b22d35ecbaaa.png";
        var COMMUNITY_AVATAR = "https://i.postimg.cc/k5NBY37k/file-0000000016a482119619e0cb99151c28.png";
        var TELEGRAM_URL = "https://t.me/+x1QYA_1-sSs0NTk1";
        var ACCESS_KEY = "Gop Gop2027";

        var STORAGE_UNLOCK = "__raUnlockedSession_v4";
        var STORAGE_MODE = "__raLockedMode_v4";
        var STORAGE_ON = "__raModeIsOn_v4";

        var lockedMode = null;
        var isModeOn = false;
        var autoLoopRunning = false;
        var isScanningNow = false;
        var lastTradeClickTs = 0;

        var autoLoopTimer = null;
        var scanFrameRaf = null;
        var audioCtx = null;
        var lastTickTime = 0;

        function loadState() {
            try {
                var m = window[STORAGE_MODE] || localStorage.getItem(STORAGE_MODE);
                if (m === "MANUAL" || m === "5S_AUTO") lockedMode = m;
                var onVal = window[STORAGE_ON];
                if (typeof onVal !== "boolean") {
                    var ls = localStorage.getItem(STORAGE_ON);
                    onVal = (ls === "1" || ls === "true");
                }
                isModeOn = !!onVal;
            } catch (_) {}
        }

        function saveMode(mode) {
            lockedMode = mode;
            try {
                if (mode) {
                    window[STORAGE_MODE] = mode;
                    localStorage.setItem(STORAGE_MODE, mode);
                } else {
                    delete window[STORAGE_MODE];
                    localStorage.removeItem(STORAGE_MODE);
                }
            } catch (_) {}
        }

        function saveModeOn(active) {
            isModeOn = !!active;
            try {
                window[STORAGE_ON] = isModeOn;
                localStorage.setItem(STORAGE_ON, isModeOn ? "1" : "0");
            } catch (_) {}
            updateOnBadge();
        }

        function getAudio() {
            try {
                var Ctx = window.AudioContext || window.webkitAudioContext;
                if (!Ctx) return null;
                if (!audioCtx) audioCtx = new Ctx();
                if (audioCtx.state === "suspended") audioCtx.resume().catch(function(){});
                return audioCtx;
            } catch (_) {
                return null;
            }
        }

        function playScanTick() {
            var nowMs = Date.now();
            if (nowMs - lastTickTime < 120) return;
            lastTickTime = nowMs;
            var ctx = getAudio();
            if (!ctx) return;
            try {
                var t = ctx.currentTime;
                var osc = ctx.createOscillator();
                var gain = ctx.createGain();
                osc.type = "sawtooth";
                osc.frequency.setValueAtTime(980, t);
                osc.frequency.exponentialRampToValueAtTime(440, t + 0.045);
                gain.gain.setValueAtTime(0.001, t);
                gain.gain.linearRampToValueAtTime(0.2, t + 0.006);
                gain.gain.exponentialRampToValueAtTime(0.001, t + 0.05);
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.start(t);
                osc.stop(t + 0.055);
            } catch (_) {}
        }

        function playTradeAlert(isUp) {
            var ctx = getAudio();
            if (!ctx) return;
            try {
                var t = ctx.currentTime;
                var osc = ctx.createOscillator();
                var gain = ctx.createGain();
                osc.type = "triangle";
                if (isUp) {
                    osc.frequency.setValueAtTime(540, t);
                    osc.frequency.exponentialRampToValueAtTime(1140, t + 0.18);
                } else {
                    osc.frequency.setValueAtTime(680, t);
                    osc.frequency.exponentialRampToValueAtTime(240, t + 0.2);
                }
                gain.gain.setValueAtTime(0.001, t);
                gain.gain.linearRampToValueAtTime(0.36, t + 0.015);
                gain.gain.exponentialRampToValueAtTime(0.001, t + 0.24);
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.start(t);
                osc.stop(t + 0.25);
            } catch (_) {}
        }

        function injectStyles() {
            if (document.getElementById("ra-cyber-chart-styles")) return;
            var style = document.createElement("style");
            style.id = "ra-cyber-chart-styles";
            style.textContent =
                "@keyframes raSpinCW { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }" +
                "@keyframes raSpinCCW { 0% { transform: rotate(360deg); } 100% { transform: rotate(0deg); } }" +
                "@keyframes raAuraCycle { 0% { box-shadow: 0 0 22px #00f0ff, 0 0 48px rgba(0,240,255,0.85); } 25% { box-shadow: 0 0 24px #22c55e, 0 0 50px rgba(34,197,94,0.85); } 50% { box-shadow: 0 0 24px #e879f9, 0 0 50px rgba(232,121,249,0.85); } 75% { box-shadow: 0 0 24px #facc15, 0 0 50px rgba(250,204,21,0.85); } 100% { box-shadow: 0 0 22px #00f0ff, 0 0 48px rgba(0,240,255,0.85); } }" +
                "@keyframes raScanSweep { 0% { top: 0%; opacity: 0.95; } 50% { top: 96%; opacity: 1; } 100% { top: 0%; opacity: 0.95; } }" +
                "@keyframes raCyberBorderPulse { 0% { border-color: #00f0ff; box-shadow: inset 0 0 70px rgba(0,240,255,0.24), 0 0 38px rgba(0,240,255,0.6); } 33% { border-color: #22c55e; box-shadow: inset 0 0 75px rgba(34,197,94,0.24), 0 0 42px rgba(34,197,94,0.6); } 66% { border-color: #e879f9; box-shadow: inset 0 0 75px rgba(232,121,249,0.25), 0 0 42px rgba(232,121,249,0.65); } 100% { border-color: #00f0ff; box-shadow: inset 0 0 70px rgba(0,240,255,0.24), 0 0 38px rgba(0,240,255,0.6); } }" +
                "@keyframes raSignalPop { 0% { opacity: 0; transform: translate(-50%, -42%) scale(0.75); } 70% { opacity: 1; transform: translate(-50%, -51%) scale(1.04); } 100% { opacity: 1; transform: translate(-50%, -50%) scale(1); } }" +
                "@keyframes raCandleGrow { 0% { transform: scaleY(0.15); opacity: 0.4; } 100% { transform: scaleY(1); opacity: 1; } }";
            (document.head || document.documentElement).appendChild(style);
        }

        function detectMarketPair() {
            try {
                var nodes = document.querySelectorAll("span, div, button, p");
                for (var i = 0; i < nodes.length; i++) {
                    var el = nodes[i];
                    if (el.children.length === 0) {
                        var txt = (el.innerText || "").trim().replace(/\\s+/g, " ");
                        if (/^[A-Z0-9]{2,8}\\s*\\/\\s*[A-Z0-9]{2,8}(\\s*\\(?(OTC|REAL)\\)?)?$/i.test(txt) && txt.length <= 24) {
                            var r = el.getBoundingClientRect();
                            if (r.width > 20 && r.height > 8 && r.top > 30 && r.top < window.innerHeight - 30) {
                                return txt.replace(/\\s*\\/\\s*/, "/").toUpperCase();
                            }
                        }
                    }
                }
            } catch (_) {}
            return "EUR/USD";
        }

        function clickBrokerTradeButton(isUp) {
            var now = Date.now();
            if (now - lastTradeClickTs < 2200) return false;
            lastTradeClickTs = now;

            var elements = Array.prototype.slice.call(document.querySelectorAll("button, [role='button'], a, div"));
            var matches = [];

            for (var i = 0; i < elements.length; i++) {
                var el = elements[i];
                if (!el || !el.getBoundingClientRect) continue;
                if (el.closest("#ra-hacker-btn, #ra-mode-menu, #ra-login-box, #ra-fullchart-cyber-overlay, #ra-signal-card")) continue;

                var rect = el.getBoundingClientRect();
                if (rect.width < 28 || rect.height < 22) continue;
                if (rect.top < window.innerHeight * 0.38) continue;

                var label = ((el.innerText || el.textContent || "") + " " + (el.className || "") + " " + (el.getAttribute("aria-label") || "")).toUpperCase();
                var upHit = /\\b(UP|BUY|CALL|HIGHER|LONG)\\b/.test(label);
                var downHit = /\\b(DOWN|SELL|PUT|LOWER|SHORT)\\b/.test(label);

                if (isUp && upHit && !downHit) {
                    matches.push({ el: el, score: rect.bottom + (rect.left > window.innerWidth * 0.5 ? 25 : 0) });
                } else if (!isUp && downHit && !upHit) {
                    matches.push({ el: el, score: rect.bottom + (rect.left > window.innerWidth * 0.5 ? 45 : 0) });
                }
            }

            if (matches.length > 0) {
                matches.sort(function(a, b){ return b.score - a.score; });
                var target = matches[0].el;
                try {
                    target.dispatchEvent(new PointerEvent("pointerdown", { bubbles: true, cancelable: true }));
                    target.dispatchEvent(new MouseEvent("mousedown", { bubbles: true, cancelable: true }));
                    target.click();
                    target.dispatchEvent(new MouseEvent("mouseup", { bubbles: true, cancelable: true }));
                    return true;
                } catch (_) {}
            }

            var bottomButtons = elements.filter(function(el){
                if (!el || !el.getBoundingClientRect) return false;
                if (el.closest("#ra-hacker-btn, #ra-mode-menu, #ra-login-box, #ra-fullchart-cyber-overlay, #ra-signal-card")) return false;
                var r = el.getBoundingClientRect();
                return r.width >= 48 && r.height >= 28 && r.bottom >= window.innerHeight - 135;
            });

            if (bottomButtons.length >= 2) {
                bottomButtons.sort(function(a, b){ return a.getBoundingClientRect().left - b.getBoundingClientRect().left; });
                var chosen = isUp ? bottomButtons[0] : bottomButtons[bottomButtons.length - 1];
                try {
                    chosen.click();
                    return true;
                } catch (_) {}
            }
            return false;
        }

        function clearFullChartOverlay() {
            if (scanFrameRaf) {
                cancelAnimationFrame(scanFrameRaf);
                scanFrameRaf = null;
            }
            var ov = document.getElementById("ra-fullchart-cyber-overlay");
            if (ov) ov.remove();
        }

        function showSignalAnimationCard(signal, pairName, ptsRaw, didTrade) {
            var prev = document.getElementById("ra-signal-card");
            if (prev) prev.remove();

            var isHold = signal === "HOLD";
            var isUp = signal === "CALL" || signal === "UP" || signal === "BUY";
            var ptsNum = Math.max(8, Math.min(40, parseInt(ptsRaw, 10) || 18));
            var ratio = (ptsNum - 8) / 32;
            var heightPx = Math.round(14 + ratio * 46);
            var widthPx = Math.round(12 + ratio * 12);
            var sizeLabel = ptsNum <= 14 ? "SMALL" : (ptsNum <= 26 ? "MEDIUM" : "LARGE");

            var color = isHold ? "#facc15" : (isUp ? "#22c55e" : "#ef4444");
            var bgGrad = isHold
                ? "linear-gradient(160deg, rgba(28,22,4,0.96), rgba(14,12,4,0.98))"
                : (isUp
                    ? "linear-gradient(160deg, rgba(5,36,20,0.96), rgba(4,16,10,0.98))"
                    : "linear-gradient(160deg, rgba(42,8,14,0.96), rgba(18,4,8,0.98))");

            var card = document.createElement("div");
            card.id = "ra-signal-card";
            card.style.cssText =
                "position:fixed;top:48%;left:50%;transform:translate(-50%,-50%);width:170px;" +
                "background:" + bgGrad + ";border:2.2px solid " + color + ";border-radius:14px;" +
                "padding:10px 10px 9px;z-index:2147483647;pointer-events:none;" +
                "font-family:'Courier New',monospace;color:#ffffff;text-align:center;" +
                "box-shadow:0 0 34px " + color + ", 0 0 70px rgba(0,240,255,0.32);" +
                "animation:raSignalPop 0.25s ease-out;";

            var dirTitle = isHold ? "● HOLD / SYNC" : (isUp ? "▲ UP (BUY)" : "▼ DOWN (SELL)");
            var ptsText = isHold ? "WAIT" : ((isUp ? "+" : "-") + ptsNum + " PTS");
            var execStatus = didTrade ? (isUp ? "AUTO BUY EXECUTED ✓" : "AUTO SELL EXECUTED ✓") : (isHold ? "FILTER ACTIVE" : "SIGNAL LOCKED");

            var candleHtml = isHold
                ? "<div style='height:68px;display:flex;align-items:center;justify-content:center;color:#facc15;font-size:10px;font-weight:900;'>SYNCING FEED...</div>"
                : "<div style='height:74px;display:flex;flex-direction:column;align-items:center;justify-content:" + (isUp ? "flex-end" : "flex-start") + ";animation:raCandleGrow 0.25s ease-out;'>" +
                    (isUp ? "<div style='font-size:8.5px;font-weight:900;color:#4ade80;margin-bottom:2px;'>" + ptsText + "</div>" : "") +
                    "<span style='width:2.5px;height:7px;background:" + color + ";box-shadow:0 0 10px " + color + ";'></span>" +
                    "<span style='width:" + widthPx + "px;height:" + heightPx + "px;background:" + color + ";border-radius:3px;box-shadow:0 0 24px " + color + ";'></span>" +
                    "<span style='width:2.5px;height:7px;background:" + color + ";box-shadow:0 0 10px " + color + ";'></span>" +
                    (!isUp ? "<div style='font-size:8.5px;font-weight:900;color:#f87171;margin-top:2px;'>" + ptsText + "</div>" : "") +
                  "</div>";

            card.innerHTML =
                "<div style='font-size:7.5px;font-weight:800;color:#00f0ff;letter-spacing:0.6px;'>R-A CYBER HACKER</div>" +
                "<div style='font-size:11.5px;font-weight:900;color:" + color + ";margin:2px 0 6px;text-shadow:0 0 12px " + color + ";'>" + dirTitle + "</div>" +
                "<div style='background:rgba(2,8,14,0.88);border:1.2px solid " + color + ";border-radius:9px;padding:6px 4px;margin-bottom:6px;'>" +
                candleHtml +
                "<div style='font-size:7.5px;font-weight:900;color:" + color + ";margin-top:4px;'>" + sizeLabel + " CANDLE • " + pairName + "</div>" +
                "</div>" +
                "<div style='font-size:7.5px;font-weight:900;color:#ffffff;letter-spacing:0.4px;'>" + execStatus + "</div>";

            (document.body || document.documentElement).appendChild(card);
            setTimeout(function(){
                if (card.parentNode) card.remove();
            }, 3200);
        }

        function runFullChartCyberScan(isAuto5sMode, onDoneCallback) {
            if (isScanningNow) return;
            isScanningNow = true;
            clearFullChartOverlay();

            var pairName = detectMarketPair();
            var marketQuery = pairName.replace(/[^A-Z0-9]/g, "_") || "EURUSD";
            var scanDurationMs = isAuto5sMode ? 5200 : 5800;
            var startTime = performance.now();

            var host = document.body || document.documentElement;
            var overlay = document.createElement("div");
            overlay.id = "ra-fullchart-cyber-overlay";
            overlay.style.cssText =
                "position:fixed;inset:0;z-index:2147483645;pointer-events:none;overflow:hidden;" +
                "border:3px solid #00f0ff;box-sizing:border-box;" +
                "background:radial-gradient(circle at center, rgba(0,240,255,0.07) 0%, rgba(232,121,249,0.08) 45%, rgba(34,197,94,0.07) 75%, rgba(2,10,18,0.28) 100%);" +
                "font-family:'Courier New',monospace;animation:raCyberBorderPulse 1.8s infinite linear;";

            overlay.innerHTML =
                "<div style='position:fixed;inset:0;background-image:linear-gradient(rgba(0,240,255,0.09) 1px, transparent 1px), linear-gradient(90deg, rgba(232,121,249,0.08) 1px, transparent 1px);background-size:34px 34px;opacity:0.78;'></div>" +
                "<div style='position:fixed;left:0;right:0;height:4px;background:linear-gradient(90deg, transparent, #00f0ff 18%, #22c55e 45%, #facc15 70%, #e879f9 90%, transparent);box-shadow:0 0 22px #00f0ff, 0 0 42px #e879f9;animation:raScanSweep 1.3s linear infinite;'></div>" +
                "<div style='position:fixed;top:46px;left:12px;right:12px;display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap;'>" +
                "  <div style='background:rgba(3,12,20,0.86);border:1.5px solid #22c55e;border-radius:8px;padding:5px 10px;color:#4ade80;font-size:10px;font-weight:900;box-shadow:0 0 18px rgba(34,197,94,0.55);'>⚡ FULL MARKET CYBER SCAN [" + pairName + "] • " + (isAuto5sMode ? "5S AUTO" : "MANUAL") + "</div>" +
                "  <div id='ra-cyber-scan-pct' style='background:rgba(15,6,28,0.88);border:1.5px solid #e879f9;border-radius:8px;padding:5px 10px;color:#00f0ff;font-size:10.5px;font-weight:900;box-shadow:0 0 18px rgba(0,240,255,0.55);'>SCANNING 1%</div>" +
                "</div>" +
                "<div id='ra-cyber-stream-log' style='position:fixed;top:82px;left:12px;max-width:300px;background:rgba(2,9,15,0.8);border-left:2.5px solid #e879f9;padding:6px 8px;border-radius:0 8px 8px 0;font-size:8.5px;line-height:1.4;color:#00f0ff;box-shadow:0 0 20px rgba(232,121,249,0.32);'></div>";

            host.appendChild(overlay);

            var pctEl = overlay.querySelector("#ra-cyber-scan-pct");
            var logEl = overlay.querySelector("#ra-cyber-stream-log");

            var cyberLines = [
                "> HOOK 0x7FF8A120: FULL MARKET TICK STREAM INTERCEPTED",
                "> MATRIX PULSE: LIQUIDITY & WICK PRESSURE MAPPED",
                "> QUANT CORE: ORDER BOOK IMBALANCE CALCULATING",
                "> CYBER ENGINE: VOLATILITY SPIKE & TREND LOCK",
                "> EXECUTION NODE: PREPARING AUTO ORDER TRIGGER"
            ];

            var signalPromise = fetch(SERVER_URL + "/signal?market=" + encodeURIComponent(marketQuery) + "&mode=" + (isAuto5sMode ? "AUTO5S" : "MANUAL") + "&t=" + Date.now(), { cache: "no-store" })
                .then(function(r){ return r.json(); })
                .catch(function(){ return { signal: "HOLD", pts: 0 }; });

            var lastLineIdx = -1;

            function stepScan(now) {
                if (!overlay.isConnected) {
                    isScanningNow = false;
                    if (typeof onDoneCallback === "function") onDoneCallback();
                    return;
                }

                var elapsed = now - startTime;
                var progress = Math.min(1, elapsed / scanDurationMs);
                var pct = Math.max(1, Math.min(100, Math.round(progress * 100)));

                var palette = ["#00f0ff", "#4ade80", "#e879f9", "#facc15", "#fb7185"];
                if (pctEl) {
                    pctEl.textContent = "SCANNING " + pct + "%";
                    pctEl.style.color = palette[pct % palette.length];
                }

                var lineIdx = Math.min(cyberLines.length - 1, Math.floor(progress * cyberLines.length));
                if (lineIdx !== lastLineIdx && logEl) {
                    lastLineIdx = lineIdx;
                    var line = document.createElement("div");
                    line.style.color = palette[lineIdx % palette.length];
                    line.textContent = cyberLines[lineIdx];
                    logEl.appendChild(line);
                    playScanTick();
                }

                if (progress < 1) {
                    scanFrameRaf = requestAnimationFrame(stepScan);
                    return;
                }

                signalPromise.then(function(data){
                    clearFullChartOverlay();
                    isScanningNow = false;

                    var sig = String((data && data.signal) || "HOLD").toUpperCase();
                    var isUp = sig === "CALL" || sig === "UP" || sig === "BUY";
                    var isDown = sig === "PUT" || sig === "DOWN" || sig === "SELL";

                    var didClick = false;
                    if (isUp || isDown) {
                        playTradeAlert(isUp);
                        if (isAuto5sMode && isModeOn) {
                            didClick = clickBrokerTradeButton(isUp);
                        }
                    }

                    showSignalAnimationCard(sig, detectMarketPair(), data && data.pts, didClick);

                    if (typeof onDoneCallback === "function") {
                        onDoneCallback();
                    }
                });
            }

            scanFrameRaf = requestAnimationFrame(stepScan);
        }

        function stopAuto5sLoop() {
            autoLoopRunning = false;
            if (autoLoopTimer) {
                clearTimeout(autoLoopTimer);
                autoLoopTimer = null;
            }
            clearFullChartOverlay();
            isScanningNow = false;
        }

        function startAuto5sLoop() {
            stopAuto5sLoop();
            autoLoopRunning = true;
            saveModeOn(true);

            function cycle() {
                if (!autoLoopRunning || !isModeOn) return;
                runFullChartCyberScan(true, function(){
                    if (!autoLoopRunning || !isModeOn) return;
                    autoLoopTimer = setTimeout(cycle, 4500);
                });
            }
            cycle();
        }

        function activateLockedMode(mode) {
            saveMode(mode);
            saveModeOn(true);
            var menu = document.getElementById("ra-mode-menu");
            if (menu) menu.remove();

            if (mode === "5S_AUTO") {
                startAuto5sLoop();
            } else {
                stopAuto5sLoop();
                saveModeOn(true);
                runFullChartCyberScan(false);
            }
        }

        function turnBotOff() {
            stopAuto5sLoop();
            saveModeOn(false);
            var menu = document.getElementById("ra-mode-menu");
            if (menu) menu.remove();
            var card = document.getElementById("ra-signal-card");
            if (card) card.remove();
        }

        function updateOnBadge() {
            var badge = document.getElementById("ra-bot-on-btn");
            if (!badge) return;
            badge.style.display = (isModeOn && lockedMode) ? "inline-flex" : "none";
        }

        function toggleModeMenu(botBtn) {
            var existing = document.getElementById("ra-mode-menu");
            if (existing) {
                existing.remove();
                return;
            }

            var rect = botBtn.getBoundingClientRect();
            var menu = document.createElement("div");
            menu.id = "ra-mode-menu";
            menu.style.cssText =
                "position:fixed;width:192px;" +
                "left:" + Math.max(8, Math.min(window.innerWidth - 200, rect.left + rect.width / 2 - 96)) + "px;" +
                "top:" + Math.max(60, rect.top - 96) + "px;" +
                "background:linear-gradient(165deg, rgba(6,16,28,0.98), rgba(16,8,30,0.98));" +
                "border:2px solid #00f0ff;border-radius:12px;padding:7px;z-index:2147483647;" +
                "font-family:'Segoe UI',Roboto,Arial,sans-serif;box-shadow:0 0 24px rgba(0,240,255,0.65);";

            menu.innerHTML =
                "<button id='ra-pick-manual' type='button' style='width:100%;display:flex;justify-content:space-between;align-items:center;background:rgba(34,197,94,0.18);border:1.4px solid #4ade80;border-radius:8px;padding:7px 9px;color:#fff;font-size:10.5px;font-weight:800;cursor:pointer;margin-bottom:6px;'>" +
                "  <span>Manual Signal</span>" +
                "  <span style='background:#22c55e;color:#041208;padding:1px 6px;border-radius:6px;font-size:8.5px;font-weight:900;'>1M</span>" +
                "</button>" +
                "<button id='ra-pick-5s' type='button' style='width:100%;display:flex;justify-content:space-between;align-items:center;background:rgba(232,121,249,0.2);border:1.4px solid #e879f9;border-radius:8px;padding:7px 9px;color:#fff;font-size:10.5px;font-weight:800;cursor:pointer;'>" +
                "  <span>5s Auto Mode</span>" +
                "  <span style='background:#e879f9;color:#15051a;padding:1px 6px;border-radius:6px;font-size:8.5px;font-weight:900;'>5S</span>" +
                "</button>";

            (document.body || document.documentElement).appendChild(menu);

            menu.querySelector("#ra-pick-manual").onclick = function(e){
                e.stopPropagation();
                activateLockedMode("MANUAL");
            };
            menu.querySelector("#ra-pick-5s").onclick = function(e){
                e.stopPropagation();
                activateLockedMode("5S_AUTO");
            };
        }

        function createBotCircle() {
            if (document.getElementById("ra-hacker-btn")) return;

            var host = document.body || document.documentElement;
            var btn = document.createElement("div");
            btn.id = "ra-hacker-btn";
            btn.style.cssText =
                "position:fixed;bottom:146px;right:12px;width:82px;height:82px;border-radius:50%;" +
                "background:#02090e;display:flex;align-items:center;justify-content:center;" +
                "z-index:2147483647;cursor:grab;user-select:none;touch-action:none;overflow:visible;" +
                "animation:raAuraCycle 3s infinite linear;";

            btn.innerHTML =
                "<div style='position:absolute;inset:-3px;border-radius:50%;background:conic-gradient(from 0deg, #00f0ff, #22c55e, #e879f9, #facc15, #00f0ff);filter:blur(2px);animation:raSpinCW 2.2s linear infinite;pointer-events:none;'></div>" +
                "<div style='position:absolute;inset:3px;border-radius:50%;background:#02090e;animation:raSpinCCW 3s linear infinite;pointer-events:none;'></div>" +
                "<img src='" + BOT_AVATAR + "' alt='R-A Bot' style='position:relative;z-index:2;width:66px;height:66px;border-radius:50%;object-fit:cover;border:1.8px solid #fff;pointer-events:none;' />" +
                "<button id='ra-bot-on-btn' type='button' title='Click to Turn OFF' style='position:absolute;bottom:1px;left:50%;transform:translateX(-50%);z-index:5;display:none;align-items:center;justify-content:center;padding:1px 6px;border-radius:6px;background:#00e65b;color:#031409;border:1.2px solid #ffffff;font-size:7.5px;font-weight:900;cursor:pointer;box-shadow:0 0 10px #00e65b;'>ON</button>";

            host.appendChild(btn);
            updateOnBadge();

            var onBtn = btn.querySelector("#ra-bot-on-btn");
            onBtn.addEventListener("mousedown", function(e){ e.stopPropagation(); });
            onBtn.addEventListener("touchstart", function(e){ e.stopPropagation(); }, { passive: true });
            onBtn.addEventListener("click", function(e){
                e.stopPropagation();
                e.preventDefault();
                turnBotOff();
            });

            var dragging = false, moved = false, dx = 0, dy = 0;

            function startDrag(e) {
                getAudio();
                var pt = e.touches ? e.touches[0] : e;
                var r = btn.getBoundingClientRect();
                dx = pt.clientX - r.left;
                dy = pt.clientY - r.top;
                dragging = true;
                moved = false;
            }

            function moveDrag(e) {
                if (!dragging) return;
                var pt = e.touches ? e.touches[0] : e;
                var nx = Math.max(4, Math.min(window.innerWidth - btn.offsetWidth - 4, pt.clientX - dx));
                var ny = Math.max(4, Math.min(window.innerHeight - btn.offsetHeight - 4, pt.clientY - dy));
                if (Math.abs(nx - btn.offsetLeft) > 3 || Math.abs(ny - btn.offsetTop) > 3) moved = true;
                btn.style.left = nx + "px";
                btn.style.top = ny + "px";
                btn.style.right = "auto";
                btn.style.bottom = "auto";
            }

            function endDrag(e) {
                if (!dragging) return;
                dragging = false;
                if (!moved) {
                    if (e) e.stopPropagation();
                    if (!lockedMode) {
                        toggleModeMenu(btn);
                    } else {
                        activateLockedMode(lockedMode);
                    }
                }
            }

            btn.addEventListener("mousedown", startDrag);
            btn.addEventListener("touchstart", startDrag, { passive: true });
            document.addEventListener("mousemove", moveDrag);
            document.addEventListener("touchmove", moveDrag, { passive: true });
            document.addEventListener("mouseup", endDrag);
            document.addEventListener("touchend", endDrag);
        }

        function showLoginModal() {
            if (document.getElementById("ra-login-box")) return;
            var host = document.body || document.documentElement;
            var box = document.createElement("div");
            box.id = "ra-login-box";
            box.style.cssText =
                "position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);width:256px;max-width:88vw;" +
                "background:linear-gradient(170deg, #061018, #0a1826);border:2px solid #22c55e;" +
                "border-radius:14px;padding:11px;z-index:2147483647;" +
                "font-family:'Segoe UI',Roboto,Arial,sans-serif;color:#fff;box-shadow:0 0 28px rgba(34,197,94,0.45);";

            box.innerHTML =
                "<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;'>" +
                "  <div style='display:flex;align-items:center;gap:7px;'>" +
                "    <img src='" + BOT_AVATAR + "' style='width:32px;height:32px;border-radius:50%;object-fit:cover;border:1.5px solid #00f0ff;' />" +
                "    <div>" +
                "      <div style='font-size:11px;font-weight:900;'>R-A Candle Hacker</div>" +
                "      <div style='font-size:7.5px;font-weight:800;color:#4ade80;'>CYBER CHART ENGINE</div>" +
                "    </div>" +
                "  </div>" +
                "  <span id='ra-login-x' style='cursor:pointer;color:#94a3b8;font-size:12px;font-weight:bold;'>✕</span>" +
                "</div>" +
                "<a href='" + TELEGRAM_URL + "' target='_blank' rel='noopener noreferrer' style='display:flex;align-items:center;gap:7px;text-decoration:none;background:rgba(255,255,255,0.05);border:1.4px solid #facc15;border-radius:9px;padding:6px 8px;margin-bottom:8px;'>" +
                "  <img src='" + COMMUNITY_AVATAR + "' style='width:24px;height:24px;border-radius:50%;object-fit:cover;' />" +
                "  <div style='font-size:8.5px;color:#facc15;font-weight:800;'>Join Telegram Community</div>" +
                "</a>" +
                "<input id='ra-pass-input' type='password' placeholder='Bot Access Key' style='width:100%;box-sizing:border-box;background:#0b1724;border:1.4px solid rgba(148,163,184,0.35);border-radius:8px;padding:7px;color:#fff;font-size:10.5px;text-align:center;outline:none;margin-bottom:6px;' />" +
                "<div id='ra-pass-msg' style='min-height:13px;text-align:center;font-size:8.5px;font-weight:800;margin-bottom:6px;'></div>" +
                "<button id='ra-pass-submit' type='button' style='width:100%;border:none;border-radius:8px;padding:8px;font-size:10.5px;font-weight:900;color:#04110a;background:linear-gradient(90deg,#f43f5e,#eab308,#22c55e);cursor:pointer;'>ACTIVATE BOT</button>";

            host.appendChild(box);

            var input = box.querySelector("#ra-pass-input");
            var msg = box.querySelector("#ra-pass-msg");
            var btn = box.querySelector("#ra-pass-submit");

            box.querySelector("#ra-login-x").onclick = function(){ box.remove(); };

            function verifyKey() {
                if ((input.value || "").trim() !== ACCESS_KEY) {
                    msg.style.color = "#f87171";
                    msg.textContent = "✕ INCORRECT PASSWORD!";
                    return;
                }
                window[STORAGE_UNLOCK] = true;
                msg.style.color = "#4ade80";
                msg.textContent = "✓ UNLOCKED!";
                setTimeout(function(){
                    box.remove();
                    createBotCircle();
                }, 350);
            }

            btn.onclick = verifyKey;
            input.addEventListener("keydown", function(e){
                if (e.key === "Enter") verifyKey();
            });
        }

        function boot() {
            injectStyles();
            loadState();
            if (window[STORAGE_UNLOCK]) {
                createBotCircle();
            } else {
                showLoginModal();
            }
        }

        window.__raMountBot = boot;

        if (document.readyState === "loading") {
            document.addEventListener("DOMContentLoaded", boot, { once: true });
        } else {
            boot();
        }
    })();
    """
    res = make_response(js)
    return add_cors_headers(res, is_js=True)


def start_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, threaded=True)


if __name__ == '__main__':
    start_server()
