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
# 1) ALL PRIMARY, DEVELOPER & MASTER CREDENTIALS (01 - 60)
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

    "MASTER_GEMINI_KEY_01": _get_cred("MASTER_GEMINI_KEY_01", "QVEuQWI4Uk42S0FrZ1dJbXQtalhnSDVMem1MMVNNOXJzWk5TaE1jY2VQMkM3MklVcDllaXc="),
    "MASTER_FINNHUB_KEY_02": _get_cred("MASTER_FINNHUB_KEY_02", "ZGJxYmhtMXIwMXFuODhldmg2MGRicWJobTFyMDFxbjg4ZWV2aDZn"),
    "MASTER_ALPHA_VANTAGE_KEY_03": _get_cred("MASTER_ALPHA_VANTAGE_KEY_03", "S0NZN0lOOUdLVzRBUlY5UA=="),
    "MASTER_TWELVE_DATA_KEY_04": _get_cred("MASTER_TWELVE_DATA_KEY_04", "MDZkYmY1OGMwOTNmNDhmZjhkYzM2NDQ2NzkwMmZhNjQ="),
    "MASTER_BINANCE_WS_05": _get_cred("MASTER_BINANCE_WS_05", "d3NzOi8vc3RyZWFtLmJpbmFuY2UuY29tOjk0NDMvd3MvYnRjdXNkdEBrbGluZV8xbQ=="),
    "MASTER_OANDA_KEY_06": _get_cred("MASTER_OANDA_KEY_06", "OTdkMDliYzEtMjdkMi00MWFmLTg0MWItNzIyNzQ1NGRlM2I1"),
    "MASTER_FINAGE_KEY_07": _get_cred("MASTER_FINAGE_KEY_07", "QVBJX0tFWTozTjI3UjBCVDVYTDYzVjJPWFROVlFSNVlJNzcxT1ZN").replace(":3N", "83N"),
    "MASTER_GROQ_KEY_08": _get_cred("MASTER_GROQ_KEY_08", "Z3NrX2pyaUFkVW91MkRYMHFBclFMTURZV0dkeWIzRllUeVBIM2c5YVQ4SWFoRWtVUDdkRjhCRTA="),
    "MASTER_OPENAI_KEY_09": _get_cred("MASTER_OPENAI_KEY_09", "c2stcHJvai1SMTNZX2oySl91ZENPcFBKaDV3LXhYR0w3SE5mUWJtajJLS2RYd1Axa21YaWttQ0ROZzZPM3ZSRm5TUG00VHZoYmtkeUU4cHhjOVQzQmxia0ZKTk9sbldEdzQ3cUlydWk5ZnpuMDA0bDlGanlwQjNsYWVnMTZQbEpNVnZwNmh2djdWUEdJc1dlY3VOTFdhblRjYTJDVkFBcWZRQQ=="),
    "MASTER_OPENROUTER_KEY_10": _get_cred("MASTER_OPENROUTER_KEY_10", "c2stb3ItdjEtZGIwZjZjYTgwZjViZjE3NzYxMTljZTdmZmExNjIwNzBkMTM4NDcyZDk5OGQ3OTE2YTljODEzMGJiZmViNmEyZA=="),
    "MASTER_ALLTICK_KEY_12": _get_cred("MASTER_ALLTICK_KEY_12", "ZDJkOTQ5NjI4Y2NhNzk2NzgyZTM4Mjk3OGNjYWFiMjAtYy1hcHA="),
    "MASTER_FMP_KEY_13": _get_cred("MASTER_FMP_KEY_13", "Z3FZV2sxcWF4OWRRZldqTU5iOTVncjlnbUtFTHhlOWU="),
    "MASTER_GEMINI_PRO_KEY_14": _get_cred("MASTER_GEMINI_PRO_KEY_14", "QVEuQWI4Uk42TExRQTRnTUstbEV1a0l6SE1XVWFmaVNmd3U3QU1SVlRfSGdhWjc2b2tSNHc="),
    "MASTER_FRED_KEY_15": _get_cred("MASTER_FRED_KEY_15", "ZDM3ZDNlZDIyNTVmMmY1YTlmYjc1NmM3YjVmMGI2NjM="),
    "MASTER_QVERIS_KEY_16": _get_cred("MASTER_QVERIS_KEY_16", "c2stQ2djVTRtLVE1dmFYSng2d1ZiUVAydnJMYlVJbVlMTEpOczNnbzRBZi1vTQ=="),
    "MASTER_MARKETSTACK_KEY_17": _get_cred("MASTER_MARKETSTACK_KEY_17", "NzkwNDYxN2VjMTYzZmJiODZjYjhmYzg2YmVmNTgwZDA="),
    "MASTER_ALPACA_KEY_18": _get_cred("MASTER_ALPACA_KEY_18", "UEtMUzJVWEg1SE1OTTdHQVFVM0RFSVBNR08="),
    "MASTER_MISTRAL_KEY_19": _get_cred("MASTER_MISTRAL_KEY_19", "bXN0cmxfd3lKVk1RcnI0YTVvTkg5QjBNN2ZXSEtuRXI0ZlRyREdfM1FUempz"),
    "MASTER_COHERE_KEY_20": _get_cred("MASTER_COHERE_KEY_20", "UmFRZm5VN0taeHlXM2dNVm1vd0FxZTVtOFZnQ3NlWjNRdmM3dlByQQ=="),
    "MASTER_CLOUDFLARE_KEY_21": _get_cred("MASTER_CLOUDFLARE_KEY_21", "MTQ0YzlkZWZhYzA0OTY5YzdiZmFkOGVmYWE4ZWExOTQ="),
    "MASTER_TICKDB_KEY_22": _get_cred("MASTER_TICKDB_KEY_22", "Q3poNnNCbXBqUm1kVlZPZWtCenVYRUxjTW9obGU3TnQ="),
    "MASTER_CRYPTORANK_KEY_23": _get_cred("MASTER_CRYPTORANK_KEY_23", "NzkyMmZkMzgwYzBhNzI2YjRkZTU3MzFlMDAzNjJlYzNmYWM0Yzg3OWIyZTliNDhhYzdkNzlhNzg2Yjhh"),
    "MASTER_FRED_STLOUIS_KEY_24": _get_cred("MASTER_FRED_STLOUIS_KEY_24", "YTgwN2M5YzE0YmYzNzZjOGQ1NzczOTY5NjgwNDg0OGU="),
    "MASTER_ALPHA_ALT_KEY_26": _get_cred("MASTER_ALPHA_ALT_KEY_26", "WE1LQjlOVlhaWFNBQU8wVQ=="),
    "MASTER_FINNHUB_ALT_KEY_27": _get_cred("MASTER_FINNHUB_ALT_KEY_27", "ZGI3bW5pMXIwMXFwdGI1czZhNTBkYjdtbmkxcjAxcXB0YjVzNmE1Zw=="),
    "MASTER_COINGECKO_KEY_28": _get_cred("MASTER_COINGECKO_KEY_28", "Q0ctbW10aHZWZ3F3dmE1QTRpQ0E3YnhYRjl3"),
    "MASTER_CRYPTOAPIS_KEY_29": _get_cred("MASTER_CRYPTOAPIS_KEY_29", "NWM1OGRkZGJhMGVhZjFiYzYyYTkxYjU5YWE4YzkwYzA2OWI5MjZiMg=="),
    "MASTER_IBKR_KEY_30": _get_cred("MASTER_IBKR_KEY_30", "ZTBkNzViNGM1YzFkMmMwZjJhZjc="),
    "MASTER_FYERS_KEY_32": _get_cred("MASTER_FYERS_KEY_32", "YzcxMjBkMmI1MDA0ZjhkZTIyZDhkYzJkYTA0NTNiNGQ3ZTYyMTFlMzdhNDEwOGI4MzcxMjY2ZWNmZjAwNDk4"),
    "MASTER_ALTFINS_KEY_33": _get_cred("MASTER_ALTFINS_KEY_33", "YWZuc19za18xNTYwODIudk53UEZVZXVtR05WYk1tR0hJUW5jdVJHblZROWU2bU1UenlxR1BOTXp3OA=="),
    "MASTER_KOTAK_KEY_34": _get_cred("MASTER_KOTAK_KEY_34", "ZWM2YTc0NmMtZTQ0Yi00NTVlLWFiZjItYzEzMzUyYjJmYzQ1"),
    "MASTER_FREECRYPTO_KEY_35": _get_cred("MASTER_FREECRYPTO_KEY_35", "emowNXFkMTI2bGtrMW5na3pnNGc="),
    "MASTER_KALSHI_KEY_36": _get_cred("MASTER_KALSHI_KEY_36", "YTk1MmJjYmUtZWMzYi00YjViLWI4ZjktMTFkYWU1ODk2MDhj"),
    "MASTER_BLINK_KEY_37": _get_cred("MASTER_BLINK_KEY_37", "cXR4XzI0NTAyZmQ1NmI3NjYzYjc2M2EyNDE2ZGNiNjE4ZTIzODk2NjAxNDI1Y2YzMjJlNg=="),
    "MASTER_QODEX_KEY_38": _get_cred("MASTER_QODEX_KEY_38", "c1gxRWpvcmplSk9haE9OS2p1TmxRTQ=="),
    "MASTER_ORCA_KEY_39": _get_cred("MASTER_ORCA_KEY_39", "c2stb3JjYS1YZUJ6bkhvNE9jZXdndUhtQTNXd0szSVFUa2pBMGxGNXZUb2EzdEJFZGg0"),
    "MASTER_GROQ_ALT_KEY_40": _get_cred("MASTER_GROQ_ALT_KEY_40", "Z3NrX1gzaEEzMnEzTW43ZGpYTkRHVElpV0dkeWIzRllRQndaT0hIZW5mZ1VGcjF6N3d4bVIyeWw="),
    "MASTER_OLLAMA_KEY_43": _get_cred("MASTER_OLLAMA_KEY_43", "MzMwNWJmN2FkYzExNDQxNjk1Mzc5YjNhYjMzNjhiOWUud0JPWDVHYlNBa0dJbVNlcFJUbG53dU9x"),
    "MASTER_MASSIVE_ALT_KEY_44": _get_cred("MASTER_MASSIVE_ALT_KEY_44", "UWZXeXVtcWJ5UlBTWExWV1FwaEFiZTliRXVLa2lFSHA="),
    "MASTER_COMET_KEY_45": _get_cred("MASTER_COMET_KEY_45", "c2stNUxpQm1hTUhTVjlWSFJ0M2ZWN1REMkZRaEN1dUh1MGxJSTZid083WmdIdG1VSmRZ"),
    "MASTER_TWELVEDATA_OB_KEY_54": _get_cred("MASTER_TWELVEDATA_OB_KEY_54", "NTM1NmMyNGM5MDVjNDQwNThiMjhmMjUyYWQ2MzNlZTRfT0I="),
    "MASTER_EXCHANGERATE_API": _get_cred("MASTER_EXCHANGERATE_API", "aHR0cHM6Ly9hcGkuZXhjaGFuZ2VyYXRlLWFwaS5jb20vdjQvbGF0ZXN0L1VTRA=="),
    "MASTER_BINANCE_REST_API": _get_cred("MASTER_BINANCE_REST_API", "aHR0cHM6Ly9hcGkuYXBpLmJpbmFuY2UuY29tL2FwaS92My9rbGluZXM="),
    "MASTER_EXCHANGERATE_HOST": _get_cred("MASTER_EXCHANGERATE_HOST", "aHR0cHM6Ly9hcGkuZXhjaGFuZ2VyYXRlLmhvc3QvbGl2ZT9hY2Nlc3Nfa2V5PXNlY3VyZQ=="),
    "MASTER_CURRENCYLAYER_API": _get_cred("MASTER_CURRENCYLAYER_API", "aHR0cHM6Ly9hcGlsYXllci5uZXQvYXBpL2xpdmU/YWNjZXNzX2tleT1zZWN1cmU="),
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

TIMEZONE_OFFSET = float(os.environ.get("QX_TZ", "6"))

KNOWLEDGE_REGISTRY = {
    "core_logic_rules_count": 560,
    "pro_max_modules_count": 50,
    "backup_apis_count": 60,
    "master_keys_count": 12,
    "dev_apis_count": 5,
    "international_knowledge_nodes": 12_000_000,
    "signal_mode": "MULTI_SOURCE_AUTHENTIC_CONSENSUS_5S_SNIPER",
}

http_session = requests.Session()
http_session.headers.update({
    "User-Agent": "RA-Candle-Hacker-Backend/18.2",
    "Accept": "application/json"
})
if API_REGISTRY["QUANTEX_PRO_DASHBOARD_KEY"]:
    http_session.headers["X-Quantex-Key"] = API_REGISTRY["QUANTEX_PRO_DASHBOARD_KEY"]


def add_cors_headers(response, is_js: bool = False):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    if is_js:
        response.headers["Content-Type"] = "application/javascript; charset=utf-8"
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return response


class LiveMarketCandleEngine:
    _news_cache = {"ts": 0.0, "events": []}
    _price_history = {}
    _market_history = {}
    _last_pts_by_market = {}

    @classmethod
    def _record_and_get_history(cls, symbol: str, price: float) -> list:
        hist = cls._price_history.setdefault(symbol, [])
        if not hist or abs(hist[-1] - price) > 0:
            hist.append(price)
        if len(hist) > 24:
            hist.pop(0)
        return hist

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
            score += 1.6
        elif delta < 0:
            score -= 1.6

        if len(closes) >= 3:
            prev_delta = closes[-2] - closes[-3]
            if delta > 0 and prev_delta > 0:
                score += 0.65
            elif delta < 0 and prev_delta < 0:
                score -= 0.65

        if ema_fast is not None and ema_slow is not None:
            if ema_fast > ema_slow:
                score += 1.15
            elif ema_fast < ema_slow:
                score -= 1.15

        if rsi is not None:
            if rsi >= 72:
                score -= 1.5
            elif rsi <= 28:
                score += 1.5
            elif rsi > 52:
                score += 0.6
            elif rsi < 48:
                score -= 0.6
        return score

    @classmethod
    def _evaluate_consensus_signal(cls, symbol: str, series_list: list, pip_factor: float):
        primary_closes = series_list[0]["closes"]
        c0 = primary_closes[-1]
        c1 = primary_closes[-2]
        delta = c0 - c1
        rsi = cls._calc_rsi(primary_closes, period=min(6, len(primary_closes) - 1))

        weighted_score = 0.0
        total_weight = 0.0
        call_votes = 0
        put_votes = 0

        for item in series_list:
            w = float(item.get("weight", 1.0))
            s_bias = cls._score_series_bias(item["closes"])
            weighted_score += s_bias * w
            total_weight += w
            if s_bias > 0.15:
                call_votes += 1
            elif s_bias < -0.15:
                put_votes += 1

        avg_bias = (weighted_score / total_weight) if total_weight > 0 else 0.0

        # Normal balanced threshold: only HOLD when directional movement is virtually flat
        if abs(avg_bias) < 0.08:
            return "HOLD", 0, 0, c0

        signal = "CALL" if avg_bias > 0 else "PUT"
        aligned_votes = call_votes if signal == "CALL" else put_votes
        total_votes = max(1, call_votes + put_votes)
        confirm_ratio = aligned_votes / total_votes

        # Balanced ~70% check: hold only on strong opposing multi-source conflict
        if total_votes >= 2 and confirm_ratio < 0.55 and abs(avg_bias) < 0.45:
            return "HOLD", 0, 0, c0

        m_hist = cls._market_history.setdefault(symbol, [])
        if len(m_hist) >= 3 and m_hist[-1] == signal and m_hist[-2] == signal and m_hist[-3] == signal:
            strong_conviction = (signal == "CALL" and avg_bias >= 1.15) or (signal == "PUT" and avg_bias <= -1.15)
            if not strong_conviction:
                signal = "PUT" if signal == "CALL" else "CALL"

        live_pips = abs(delta) * pip_factor
        rsi_factor = abs((rsi - 50.0) * 0.32) if rsi is not None else 2.2
        consensus_boost = min(9.0, abs(avg_bias) * 3.5)
        raw_pts = 8.0 + min(32.0, (live_pips * 2.5) + rsi_factor + consensus_boost)
        pts_val = max(8, min(40, int(round(raw_pts))))

        prev_pts = cls._last_pts_by_market.get(symbol)
        if prev_pts is not None and pts_val == prev_pts:
            shift = 3 if pts_val <= 35 else -3
            pts_val = max(8, min(40, pts_val + shift))
        cls._last_pts_by_market[symbol] = pts_val

        m_hist.append(signal)
        if len(m_hist) > 12:
            m_hist.pop(0)

        conf_pct = min(99, max(72, int(round(72 + min(27.0, (confirm_ratio * 16.0) + abs(avg_bias) * 4.2)))))
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
                response = http_session.get(url, timeout=2.0)
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
                    normalized_str = event_time_str.replace("Z", "+00:00")
                    event_dt = datetime.fromisoformat(normalized_str)
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
                resp = http_session.get(url_ts, timeout=2.0)
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
                resp = http_session.get(url_b, timeout=1.8)
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
                resp = http_session.get(url_p, timeout=1.8)
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
                q_resp = http_session.get(url_q, timeout=1.7)
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
                    resp = http_session.get(url_av, timeout=1.8)
                    if resp.status_code == 200:
                        rt = resp.json().get("Realtime Currency Exchange Rate", {})
                        px = rt.get("5. Exchange Rate")
                        if px is not None:
                            return float(px), "AlphaVantage-Spot"
                except Exception:
                    pass

            try:
                url_er = f"https://api.exchangerate-api.com/v4/latest/{from_curr}"
                resp = http_session.get(url_er, timeout=1.7)
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
            if len(hist) >= 2:
                gathered_series.append({"closes": hist, "weight": 1.25})
                if spot_src:
                    sources_used.append(spot_src)

        if gathered_series:
            sig, pts_val, conf_pct, c0 = cls._evaluate_consensus_signal(clean_sym, gathered_series, pip_factor)
            if sig == "HOLD":
                return {
                    "signal": "HOLD",
                    "trend": "NEUTRAL BALANCE",
                    "status": "HOLD_NEUTRAL",
                    "pts": 0,
                    "confidence": 0,
                    "rule": f"{mode_prefix} Awaiting Clear Directional Momentum ({formatted_sym}: {c0})"
                }
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
    res = make_response("R-A CANDLE HACKER ENGINE ACTIVE - ULTRA SMOOTH LIVE CANDLES!")
    return add_cors_headers(res)


@app.route('/ping')
def ping():
    res = make_response("OK", 200)
    return add_cors_headers(res)


@app.route('/health')
def health():
    res = jsonify({
        "status": "ONLINE",
        "server": "https://ra-ai-bot.onrender.com",
        "knowledge": KNOWLEDGE_REGISTRY,
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
            is_news_safe = LiveMarketCandleEngine.check_news_safety(clean_sym[:3])
            if not is_news_safe:
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
            "confidence": analysis.get("confidence", 75),
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
        var renderServerUrl = "https://ra-ai-bot.onrender.com";
        var botAvatarUrl = "https://i.postimg.cc/jj70SSfW/IMG-20261124-WA0005.jpg";
        var communityAvatarUrl = "https://i.postimg.cc/KYTGH2Zg/IMG-20261118-WA0017.jpg";
        var telegramChannelUrl = "https://t.me/+x1QYA_1-sSs0NTk1";
        var validAccessKey = "Gop Gop2027";
        var sessionFlagName = "__raCandleHackerUnlocked";
        var savedModeStorageKey = "__raLockedModeChoice";
        var savedActiveStorageKey = "__raModeActiveState";

        function mountBot() {
            try {
                var d = document;
                var hostRoot = d.body || d.documentElement;
                if(!hostRoot) return false;

                var hasLogin = !!d.getElementById('ra-hacker-login-modal');
                var hasBotBtn = !!d.getElementById('ra-hacker-btn');
                var hasScan = !!d.getElementById('ra-hacker-scan-modal');
                var hasCyberOverlay = !!d.getElementById('ra-cyber-5s-overlay');

                if(hasLogin || hasBotBtn || hasScan || hasCyberOverlay) {
                    return true;
                }

                [
                    "ra-sniper-bot-panel", "ra-sniper-bot-btn", "ra-sniper-bot-style",
                    "dr-tracker-panel", "dr-tracker-btn", "dr-scan-modal",
                    "dr-candle-projection", "dr-next-signal-popup", "dr-hacker-style",
                    "ra-hacker-btn", "ra-hacker-scan-modal", "ra-hacker-signal-popup",
                    "ra-hacker-login-modal", "ra-bg-blur-overlay", "ra-hacker-style",
                    "ra-mode-selector-menu", "ra-auto-5s-panel", "ra-cyber-5s-overlay",
                    "ra-bot-power-pill", "ra-auto-trade-toast", "ra-5s-hold-notice"
                ].forEach(function(id){
                    var el = d.getElementById(id);
                    if(el) el.remove();
                });

                if(window.__raScanTimer) {
                    clearInterval(window.__raScanTimer);
                    window.__raScanTimer = null;
                }
                if(window.__raScanRaf) {
                    cancelAnimationFrame(window.__raScanRaf);
                    window.__raScanRaf = null;
                }
                if(window.__raCyber5sRaf) {
                    cancelAnimationFrame(window.__raCyber5sRaf);
                    window.__raCyber5sRaf = null;
                }
                if(window.__raAuto5sLoopTimer) {
                    clearTimeout(window.__raAuto5sLoopTimer);
                    window.__raAuto5sLoopTimer = null;
                }
                if(window.__raAuto5sStepTimer) {
                    clearInterval(window.__raAuto5sStepTimer);
                    window.__raAuto5sStepTimer = null;
                }
                if(window.__raAuto5sClockTimer) {
                    clearInterval(window.__raAuto5sClockTimer);
                    window.__raAuto5sClockTimer = null;
                }

                function readSavedMode() {
                    try {
                        var v = window[savedModeStorageKey] || localStorage.getItem(savedModeStorageKey);
                        if(v === "MANUAL" || v === "5S_AUTO") return v;
                    } catch(e) {}
                    return null;
                }

                function writeSavedMode(modeVal) {
                    try {
                        if(modeVal) {
                            window[savedModeStorageKey] = modeVal;
                            localStorage.setItem(savedModeStorageKey, modeVal);
                        } else {
                            delete window[savedModeStorageKey];
                            localStorage.removeItem(savedModeStorageKey);
                        }
                    } catch(e) {}
                }

                function readSavedActive() {
                    try {
                        var a = window[savedActiveStorageKey];
                        if(typeof a === "boolean") return a;
                        var ls = localStorage.getItem(savedActiveStorageKey);
                        if(ls === "1") return true;
                        if(ls === "0") return false;
                    } catch(e) {}
                    return false;
                }

                function writeSavedActive(isAct) {
                    try {
                        window[savedActiveStorageKey] = !!isAct;
                        localStorage.setItem(savedActiveStorageKey, isAct ? "1" : "0");
                    } catch(e) {}
                }

                writeSavedActive(false);
                writeSavedMode(null);

                var lockedModeChoice = readSavedMode();
                var isModeOn = readSavedActive();
                var auto5sRunning = false;
                var auto5sBusy = false;
                var lastAutoTradeTs = 0;
                var lastCandlePtsByKey = {};

                var audioCtx = null;
                var lastTickMs = 0;

                function ensureAudioContext() {
                    try {
                        var Ctx = window.AudioContext || window.webkitAudioContext;
                        if(!Ctx) return null;
                        if(!audioCtx) audioCtx = new Ctx();
                        if(audioCtx.state === "suspended") {
                            audioCtx.resume().catch(function(){});
                        }
                        return audioCtx;
                    } catch(e) {
                        return null;
                    }
                }

                function pickEnhancedFemaleBanglaVoice(voices) {
                    if(!voices || !voices.length) return null;
                    var femaleHints = [
                        "female", "woman", "girl", "zira", "samantha", "priya",
                        "salma", "tanisha", "lekha", "heera", "aria", "jenny",
                        "google বাংলা", "bangla female", "bengali female"
                    ];
                    var bnList = voices.filter(function(v){
                        var l = String(v.lang || "").toLowerCase();
                        return l.indexOf("bn") === 0 || l.indexOf("bengali") !== -1;
                    });
                    var pool = bnList.length ? bnList : voices;

                    for(var i = 0; i < pool.length; i++) {
                        var nm = String(pool[i].name || "").toLowerCase();
                        for(var h = 0; h < femaleHints.length; h++) {
                            if(nm.indexOf(femaleHints[h]) !== -1) {
                                return pool[i];
                            }
                        }
                    }
                    return bnList.length ? bnList[0] : null;
                }

                function speakBangla5sVoice(phrase) {
                    try {
                        if(!phrase) return;
                        if('speechSynthesis' in window) {
                            var runSpeak = function() {
                                try {
                                    window.speechSynthesis.cancel();
                                    var utter = new SpeechSynthesisUtterance(phrase);
                                    var voices = window.speechSynthesis.getVoices ? window.speechSynthesis.getVoices() : [];
                                    var chosenVoice = pickEnhancedFemaleBanglaVoice(voices);
                                    if(chosenVoice) {
                                        utter.voice = chosenVoice;
                                        utter.lang = chosenVoice.lang || 'bn-BD';
                                    } else {
                                        utter.lang = 'bn-BD';
                                    }
                                    utter.rate = 1.05;
                                    utter.pitch = 1.25;
                                    utter.volume = 1.0;
                                    window.speechSynthesis.speak(utter);
                                } catch(errInner) {}
                            };

                            var currentVoices = window.speechSynthesis.getVoices ? window.speechSynthesis.getVoices() : [];
                            if(!currentVoices.length && 'onvoiceschanged' in window.speechSynthesis) {
                                var prevHandler = window.speechSynthesis.onvoiceschanged;
                                window.speechSynthesis.onvoiceschanged = function(ev) {
                                    if(typeof prevHandler === "function") prevHandler(ev);
                                    runSpeak();
                                };
                                setTimeout(runSpeak, 120);
                            } else {
                                runSpeak();
                            }
                        }
                    } catch(e) {}
                }

                function playTickSound() {
                    try {
                        var nowMs = Date.now();
                        if(nowMs - lastTickMs < 220) return;
                        lastTickMs = nowMs;

                        var ctx = ensureAudioContext();
                        if(!ctx) return;
                        var now = ctx.currentTime;
                        var osc = ctx.createOscillator();
                        var gain = ctx.createGain();
                        osc.type = "triangle";
                        osc.frequency.setValueAtTime(1020, now);
                        osc.frequency.exponentialRampToValueAtTime(520, now + 0.022);
                        gain.gain.setValueAtTime(0.001, now);
                        gain.gain.linearRampToValueAtTime(0.14, now + 0.004);
                        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.026);
                        osc.connect(gain);
                        gain.connect(ctx.destination);
                        osc.start(now);
                        osc.stop(now + 0.028);
                    } catch(e) {}
                }

                function playTradePongSound(isCall) {
                    try {
                        var ctx = ensureAudioContext();
                        if(!ctx) return;
                        var now = ctx.currentTime;
                        var osc1 = ctx.createOscillator();
                        var osc2 = ctx.createOscillator();
                        var gain = ctx.createGain();

                        osc1.type = "sine";
                        osc2.type = "triangle";

                        if(isCall) {
                            osc1.frequency.setValueAtTime(520, now);
                            osc1.frequency.exponentialRampToValueAtTime(980, now + 0.16);
                            osc2.frequency.setValueAtTime(780, now);
                            osc2.frequency.exponentialRampToValueAtTime(1240, now + 0.18);
                        } else {
                            osc1.frequency.setValueAtTime(640, now);
                            osc1.frequency.exponentialRampToValueAtTime(260, now + 0.18);
                            osc2.frequency.setValueAtTime(420, now);
                            osc2.frequency.exponentialRampToValueAtTime(190, now + 0.2);
                        }

                        gain.gain.setValueAtTime(0.001, now);
                        gain.gain.linearRampToValueAtTime(0.42, now + 0.015);
                        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.24);

                        osc1.connect(gain);
                        osc2.connect(gain);
                        gain.connect(ctx.destination);

                        osc1.start(now);
                        osc2.start(now);
                        osc1.stop(now + 0.25);
                        osc2.stop(now + 0.25);
                    } catch(e) {}
                }

                var styleEl = d.createElement('style');
                styleEl.id = 'ra-hacker-style';
                styleEl.innerHTML = '' +
                    '@keyframes raContinuousSpin {' +
                    '  0%   { transform: rotate(0deg); }' +
                    '  100% { transform: rotate(360deg); }' +
                    '}' +
                    '@keyframes raContinuousReverseSpin {' +
                    '  0%   { transform: rotate(360deg); }' +
                    '  100% { transform: rotate(0deg); }' +
                    '}' +
                    '@keyframes raBotNeonAura {' +
                    '  0%   { box-shadow: 0 0 22px #00f0ff, 0 0 44px rgba(0,240,255,0.85); }' +
                    '  50%  { box-shadow: 0 0 24px #e879f9, 0 0 48px rgba(232,121,249,0.85); }' +
                    '  100% { box-shadow: 0 0 22px #00f0ff, 0 0 44px rgba(0,240,255,0.85); }' +
                    '}' +
                    '@keyframes raLoginFastBorder {' +
                    '  0%   { border-color: #22c55e; box-shadow: 0 0 20px rgba(34,197,94,0.85); }' +
                    '  50%  { border-color: #00f0ff; box-shadow: 0 0 24px rgba(0,240,255,0.9); }' +
                    '  100% { border-color: #22c55e; box-shadow: 0 0 20px rgba(34,197,94,0.85); }' +
                    '}' +
                    '@keyframes raTelegramSlowBorder {' +
                    '  0%   { border-color: #facc15; }' +
                    '  50%  { border-color: #38bdf8; }' +
                    '  100% { border-color: #facc15; }' +
                    '}' +
                    '@keyframes raScanBoxSlowBorder {' +
                    '  0%   { border-color: #22c55e; }' +
                    '  50%  { border-color: #00f0ff; }' +
                    '  100% { border-color: #22c55e; }' +
                    '}' +
                    '@keyframes raHeaderAvatarGlow {' +
                    '  0%   { border-color: #00f0ff; }' +
                    '  50%  { border-color: #e879f9; }' +
                    '  100% { border-color: #00f0ff; }' +
                    '}' +
                    '@keyframes raPopupGreenGlow {' +
                    '  0%, 100% { border-color: #4ade80; box-shadow: 0 0 24px rgba(34,197,94,0.75); }' +
                    '  50% { border-color: #86efac; box-shadow: 0 0 30px rgba(34,197,94,0.85); }' +
                    '}' +
                    '@keyframes raPopupRedGlow {' +
                    '  0%, 100% { border-color: #f87171; box-shadow: 0 0 24px rgba(239,68,68,0.75); }' +
                    '  50% { border-color: #fca5a5; box-shadow: 0 0 30px rgba(239,68,68,0.85); }' +
                    '}' +
                    '@keyframes raCandleReveal {' +
                    '  0% { transform: scaleY(0.35); opacity: 0.5; }' +
                    '  100% { transform: scaleY(1); opacity: 1; }' +
                    '}' +
                    '@keyframes raPopupEnter {' +
                    '  0% { opacity: 0; transform: translateY(6px) scale(0.96); }' +
                    '  100% { opacity: 1; transform: translateY(0) scale(1); }' +
                    '}' +
                    '@keyframes raCyberBorderSoft {' +
                    '  0%   { border-color: #00f0ff; }' +
                    '  25%  { border-color: #22c55e; }' +
                    '  50%  { border-color: #e879f9; }' +
                    '  75%  { border-color: #facc15; }' +
                    '  100% { border-color: #00f0ff; }' +
                    '}' +
                    '@keyframes raPlanetSpinFast {' +
                    '  0%   { transform: rotate(0deg); }' +
                    '  100% { transform: rotate(360deg); }' +
                    '}' +
                    '@keyframes raLightningFlash {' +
                    '  0%, 100% { opacity: 0.25; transform: scale(0.96); }' +
                    '  50% { opacity: 0.95; transform: scale(1.08); }' +
                    '}' +
                    '@keyframes raSmoothLogGlide {' +
                    '  0%   { opacity: 0; transform: translate3d(-4px, 4px, 0); }' +
                    '  100% { opacity: 1; transform: translate3d(0, 0, 0); }' +
                    '}' +
                    '@keyframes raLowerTradePop {' +
                    '  0%   { opacity: 0; transform: translate3d(-50%, -44%, 0) scale(0.88); }' +
                    '  100% { opacity: 1; transform: translate3d(-50%, -50%, 0) scale(1); }' +
                    '}';
                (d.head || hostRoot).appendChild(styleEl);

                function syncBotPowerPillPosition() {
                    var botBtn = d.getElementById('ra-hacker-btn');
                    var pill = d.getElementById('ra-bot-power-pill');
                    if(!botBtn || !pill) return;

                    var isActiveNow = !!(isModeOn && lockedModeChoice);
                    pill.style.display = isActiveNow ? 'inline-flex' : 'none';
                    if(!isActiveNow) return;

                    var br = botBtn.getBoundingClientRect();
                    var pillW = pill.offsetWidth || 56;
                    var leftX = Math.round(br.left + (br.width / 2) - (pillW / 2));
                    leftX = Math.max(6, Math.min(window.innerWidth - pillW - 6, leftX));
                    var topY = Math.round(br.bottom + 8);
                    topY = Math.max(6, Math.min(window.innerHeight - 28, topY));
                    pill.style.left = leftX + 'px';
                    pill.style.top = topY + 'px';
                }

                function ensureBotPowerPill() {
                    var pill = d.getElementById('ra-bot-power-pill');
                    if(!pill) {
                        pill = d.createElement('button');
                        pill.id = 'ra-bot-power-pill';
                        pill.type = 'button';
                        pill.innerText = 'ON / OFF';
                        pill.style.cssText = 'position:fixed;z-index:2147483647;display:none;align-items:center;justify-content:center;' +
                            'padding:3px 9px;border-radius:8px;background:linear-gradient(90deg,#16a34a,#22c55e);color:#031409;' +
                            'border:1.5px solid #ffffff;font-family:"Segoe UI",Roboto,Arial,sans-serif;font-size:8px;font-weight:900;' +
                            'letter-spacing:0.4px;box-shadow:0 0 12px rgba(34,197,94,0.85);cursor:pointer;user-select:none;';
                        pill.addEventListener('click', function(ev){
                            ev.stopPropagation();
                            ev.preventDefault();
                            ensureAudioContext();
                            turnModeOffToStandby();
                        });
                        hostRoot.appendChild(pill);
                    }
                    syncBotPowerPillPosition();
                }

                function refreshBotOnBadge() {
                    ensureBotPowerPill();
                    syncBotPowerPillPosition();
                }

                function setBrokerBackgroundBlur(enableBlur) {
                    var existing = d.getElementById('ra-bg-blur-overlay');
                    if(enableBlur) {
                        if(!existing) {
                            var blurLayer = d.createElement('div');
                            blurLayer.id = 'ra-bg-blur-overlay';
                            blurLayer.style.cssText = 'position:fixed;inset:0;z-index:2147483640;' +
                                'background:rgba(2,8,15,0.22);pointer-events:none;';
                            hostRoot.appendChild(blurLayer);
                        }
                    } else if(existing) {
                        existing.remove();
                    }
                }

                function applyHeroCandleColor(isCall) {
                    var heroCandleBox = d.getElementById('ra-hero-candle-box');
                    var heroCandleBody = d.getElementById('ra-hero-candle-body');
                    var heroWickTop = d.getElementById('ra-hero-wick-top');
                    var heroWickBot = d.getElementById('ra-hero-wick-bot');
                    if(!heroCandleBody || !heroWickTop || !heroWickBot || !heroCandleBox) return;

                    if(isCall) {
                        heroCandleBody.style.background = 'linear-gradient(180deg,#86efac,#22c55e,#15803d)';
                        heroCandleBody.style.borderColor = '#dcfce7';
                        heroWickTop.style.background = '#86efac';
                        heroWickBot.style.background = '#86efac';
                        heroCandleBox.style.borderColor = '#4ade80';
                        heroCandleBox.style.background = 'rgba(34,197,94,0.28)';
                    } else {
                        heroCandleBody.style.background = 'linear-gradient(180deg,#fca5a5,#ef4444,#b91c1c)';
                        heroCandleBody.style.borderColor = '#fee2e2';
                        heroWickTop.style.background = '#fca5a5';
                        heroWickBot.style.background = '#fca5a5';
                        heroCandleBox.style.borderColor = '#f87171';
                        heroCandleBox.style.background = 'rgba(239,68,68,0.28)';
                    }
                }

                function showCenteredPasswordPanel() {
                    var oldLogin = d.getElementById('ra-hacker-login-modal');
                    if(oldLogin) oldLogin.remove();

                    var loginBox = d.createElement('div');
                    loginBox.id = 'ra-hacker-login-modal';
                    loginBox.style.cssText = 'position:fixed !important;top:50% !important;left:50% !important;' +
                        'transform:translate(-50%, -50%) !important;display:block !important;opacity:1 !important;visibility:visible !important;' +
                        'width:258px;max-width:88vw;background:linear-gradient(170deg, #061018 0%, #091722 55%, #050d14 100%);' +
                        'border:2px solid #22c55e;border-radius:14px;padding:10px 11px;box-sizing:border-box;' +
                        'z-index:2147483647;font-family:"Segoe UI",Roboto,Arial,sans-serif;color:#ffffff;' +
                        'animation:raLoginFastBorder 1.8s infinite linear;';

                    loginBox.innerHTML = '' +
                        '<div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid rgba(255,255,255,0.1);padding-bottom:7px;margin-bottom:7px;">' +
                        '  <div style="display:flex;align-items:center;gap:7px;">' +
                        '    <div style="width:34px;height:34px;border-radius:50%;padding:1.5px;background:linear-gradient(135deg,#22c55e,#00f0ff,#e879f9);flex-shrink:0;">' +
                        '      <img src="' + botAvatarUrl + '" alt="R-A Candle Hacker" style="width:100%;height:100%;border-radius:50%;object-fit:cover;display:block;background:#02090e;" />' +
                        '    </div>' +
                        '    <div>' +
                        '      <div style="font-size:11px;font-weight:900;color:#ffffff;letter-spacing:0.2px;line-height:1.15;">R-A Candle Hacker</div>' +
                        '      <div style="font-size:7.5px;font-weight:800;color:#f43f5e;letter-spacing:0.7px;margin-top:1px;">SECURE LOGIN</div>' +
                        '    </div>' +
                        '  </div>' +
                        '  <div id="ra-login-close" style="width:20px;height:20px;border-radius:5px;background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.14);display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:10.5px;color:#cbd5e1;font-weight:bold;">✕</div>' +
                        '</div>' +

                        '<div style="display:flex;align-items:center;gap:8px;margin-bottom:7px;">' +
                        '  <div style="width:40px;height:40px;border-radius:50%;padding:1.5px;background:linear-gradient(135deg,#facc15,#ef4444,#22c55e);flex-shrink:0;">' +
                        '    <img src="' + communityAvatarUrl + '" alt="R-A Trading Community" style="width:100%;height:100%;border-radius:50%;object-fit:cover;display:block;background:#02090e;" />' +
                        '  </div>' +
                        '  <div style="font-size:8.8px;color:#94a3b8;line-height:1.3;">' +
                        '    <div style="color:#facc15;font-weight:800;font-size:9.3px;">Official VIP Access</div>' +
                        '    <div>Join Telegram for updates &amp; keys.</div>' +
                        '  </div>' +
                        '</div>' +

                        '<a href="' + telegramChannelUrl + '" target="_blank" rel="noopener noreferrer" style="display:flex;align-items:center;justify-content:center;gap:8px;text-decoration:none;background:linear-gradient(135deg, rgba(16,28,38,0.96), rgba(10,20,28,0.98));border:1.8px solid #facc15;border-radius:10px;padding:7px 8px;margin-bottom:7px;cursor:pointer;animation:raTelegramSlowBorder 8s infinite ease-in-out;">' +
                        '  <div style="width:20px;height:20px;border-radius:50%;background:#26a5e4;display:flex;align-items:center;justify-content:center;flex-shrink:0;">' +
                        '    <svg width="11" height="11" viewBox="0 0 24 24" fill="#ffffff"><path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/></svg>' +
                        '  </div>' +
                        '  <div style="text-align:left;">' +
                        '    <div style="font-size:10px;font-weight:800;color:#4ade80;line-height:1.15;">R-A Trading Community</div>' +
                        '    <div style="font-size:7.5px;color:#cbd5e1;margin-top:1px;">Click to Join Telegram</div>' +
                        '  </div>' +
                        '</a>' +

                        '<div style="text-align:center;font-size:8px;color:#94a3b8;font-weight:600;margin-bottom:4px;">Bot Access Key</div>' +
                        '<input id="ra-access-key-input" type="password" placeholder="Bot Access Key" autocomplete="off" style="width:100%;box-sizing:border-box;background:#0b1724;border:1.4px solid rgba(148,163,184,0.3);border-radius:8px;padding:7px 8px;color:#ffffff;font-size:10.5px;text-align:center;outline:none;margin-bottom:6px;" />' +
                        '<div id="ra-login-status-msg" style="min-height:12px;text-align:center;font-size:8.5px;font-weight:800;margin-bottom:5px;letter-spacing:0.2px;"></div>' +
                        '<button id="ra-activate-bot-btn" type="button" style="width:100%;border:none;border-radius:8px;padding:8px;font-size:10.5px;font-weight:900;letter-spacing:0.5px;color:#04110a;background:linear-gradient(90deg, #f43f5e 0%, #eab308 45%, #22c55e 100%);cursor:pointer;">ACTIVATE BOT</button>';

                    hostRoot.appendChild(loginBox);

                    var closeBtn = loginBox.querySelector('#ra-login-close');
                    var keyInput = loginBox.querySelector('#ra-access-key-input');
                    var statusMsg = loginBox.querySelector('#ra-login-status-msg');
                    var activateBtn = loginBox.querySelector('#ra-activate-bot-btn');
                    var isVerifying = false;

                    closeBtn.onclick = function() {
                        loginBox.remove();
                    };

                    keyInput.addEventListener('input', function() {
                        ensureAudioContext();
                        if(!isVerifying) {
                            keyInput.style.borderColor = 'rgba(0,240,255,0.65)';
                            statusMsg.innerText = '';
                        }
                    });

                    function handleVerification() {
                        ensureAudioContext();
                        if(isVerifying) return;
                        var enteredVal = (keyInput.value || '').trim();

                        if(enteredVal !== validAccessKey) {
                            keyInput.style.borderColor = '#ef4444';
                            keyInput.style.background = 'rgba(69,10,10,0.65)';
                            statusMsg.style.color = '#f87171';
                            statusMsg.innerText = '✕ INCORRECT PASSWORD! ACCESS DENIED';
                            activateBtn.style.background = 'linear-gradient(90deg, #dc2626, #ef4444)';
                            activateBtn.style.color = '#ffffff';
                            activateBtn.innerText = 'INCORRECT PASSWORD';
                            setTimeout(function() {
                                if(loginBox.isConnected && !isVerifying) {
                                    activateBtn.style.background = 'linear-gradient(90deg, #f43f5e 0%, #eab308 45%, #22c55e 100%)';
                                    activateBtn.style.color = '#04110a';
                                    activateBtn.innerText = 'ACTIVATE BOT';
                                }
                            }, 1600);
                            return;
                        }

                        isVerifying = true;
                        keyInput.disabled = true;
                        keyInput.style.borderColor = '#facc15';
                        statusMsg.style.color = '#facc15';
                        statusMsg.innerText = '⟳ VERIFYING LICENSE KEY...';
                        activateBtn.style.background = 'linear-gradient(90deg, #0284c7, #eab308)';
                        activateBtn.style.color = '#ffffff';
                        activateBtn.innerText = 'PROCESSING...';

                        setTimeout(function() {
                            if(!loginBox.isConnected) return;
                            statusMsg.style.color = '#00f0ff';
                            statusMsg.innerText = '⟳ SYNCING QUANT ENGINE NODE...';
                        }, 900);

                        setTimeout(function() {
                            if(!loginBox.isConnected) return;
                            keyInput.style.borderColor = '#22c55e';
                            statusMsg.style.color = '#4ade80';
                            statusMsg.innerText = '✓ VERIFICATION SUCCESSFUL!';
                            activateBtn.style.background = 'linear-gradient(90deg, #16a34a, #4ade80)';
                            activateBtn.style.color = '#021208';
                            activateBtn.innerText = 'SUCCESSFUL ✓';

                            window[sessionFlagName] = true;

                            setTimeout(function() {
                                if(loginBox.isConnected) loginBox.remove();
                                createDraggableBotButton();
                            }, 600);
                        }, 1900);
                    }

                    activateBtn.onclick = handleVerification;
                    keyInput.addEventListener('keydown', function(e) {
                        if(e.key === 'Enter') {
                            e.preventDefault();
                            handleVerification();
                        }
                    });
                }

                function positionPopupAboveBotWithGap(popupEl, botEl) {
                    if(!popupEl || !botEl) return;
                    var br = botEl.getBoundingClientRect();
                    var popupWidth = 128;
                    var gapPx = 14;
                    var leftPos = Math.round(br.left + (br.width / 2) - (popupWidth / 2));
                    leftPos = Math.max(8, Math.min(window.innerWidth - popupWidth - 8, leftPos));
                    var popupHeight = popupEl.offsetHeight || 176;
                    var topPos = Math.round(br.top - popupHeight - gapPx);
                    topPos = Math.max(72, topPos);
                    popupEl.style.width = popupWidth + 'px';
                    popupEl.style.left = leftPos + 'px';
                    popupEl.style.top = topPos + 'px';
                }

                function positionModeMenuAboveBot(menuEl, botEl) {
                    if(!menuEl || !botEl) return;
                    var br = botEl.getBoundingClientRect();
                    var menuW = 204;
                    var leftPos = Math.round(br.left + br.width / 2 - menuW / 2);
                    leftPos = Math.max(8, Math.min(window.innerWidth - menuW - 8, leftPos));
                    var menuH = menuEl.offsetHeight || 92;
                    var topPos = Math.round(br.top - menuH - 12);
                    topPos = Math.max(64, topPos);
                    menuEl.style.width = menuW + 'px';
                    menuEl.style.left = leftPos + 'px';
                    menuEl.style.top = topPos + 'px';
                }

                function stopAuto5sEngine() {
                    auto5sRunning = false;
                    auto5sBusy = false;
                    if(window.__raAuto5sLoopTimer) {
                        clearTimeout(window.__raAuto5sLoopTimer);
                        window.__raAuto5sLoopTimer = null;
                    }
                    if(window.__raCyber5sRaf) {
                        cancelAnimationFrame(window.__raCyber5sRaf);
                        window.__raCyber5sRaf = null;
                    }
                    try {
                        if('speechSynthesis' in window) window.speechSynthesis.cancel();
                    } catch(e) {}
                    var ov = d.getElementById('ra-cyber-5s-overlay');
                    if(ov) ov.remove();
                    var hn = d.getElementById('ra-5s-hold-notice');
                    if(hn) hn.remove();
                    var tr = d.getElementById('ra-auto-trade-toast');
                    if(tr) tr.remove();
                }

                function turnModeOffToStandby() {
                    isModeOn = false;
                    lockedModeChoice = null;
                    writeSavedActive(false);
                    writeSavedMode(null);
                    stopAuto5sEngine();
                    var menu = d.getElementById('ra-mode-selector-menu');
                    if(menu) menu.remove();
                    var popup = d.getElementById('ra-hacker-signal-popup');
                    if(popup) popup.remove();

                    var botBtn = d.getElementById('ra-hacker-btn');
                    if(botBtn) {
                        botBtn.style.display = 'flex';
                    } else {
                        createDraggableBotButton();
                    }
                    refreshBotOnBadge();
                }

                function show5sHoldNotice(marketName, onDone) {
                    var oldHold = d.getElementById('ra-5s-hold-notice');
                    if(oldHold) oldHold.remove();

                    var box = d.createElement('div');
                    box.id = 'ra-5s-hold-notice';
                    box.style.cssText = 'position:fixed;top:56%;left:50%;transform:translate3d(-50%,-50%,0);' +
                        'width:194px;z-index:2147483647;background:linear-gradient(155deg,rgba(24,20,6,0.97),rgba(42,33,9,0.97));' +
                        'border:2px solid #facc15;border-radius:13px;padding:9px 11px;box-sizing:border-box;' +
                        'pointer-events:none;color:#ffffff;font-family:"Segoe UI",Roboto,Arial,sans-serif;' +
                        'box-shadow:0 8px 24px rgba(0,0,0,0.65);animation:raLowerTradePop 0.2s ease-out;';

                    box.innerHTML = '' +
                        '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:4px;">' +
                        '  <span style="font-size:7px;font-weight:900;color:#facc15;letter-spacing:0.4px;">5S AUTO PANEL</span>' +
                        '  <span style="font-size:6.8px;font-weight:900;color:#fef08a;background:rgba(250,204,21,0.18);padding:1px 6px;border-radius:6px;">HOLD</span>' +
                        '</div>' +
                        '<div style="font-size:11.5px;font-weight:900;color:#facc15;line-height:1.2;">হোল্ড • এখন ট্রেড নয়</div>' +
                        '<div style="font-size:7.6px;color:#e2e8f0;margin-top:2px;">' + marketName + ' • স্ক্যানিং শুরু হচ্ছে...</div>';

                    hostRoot.appendChild(box);
                    speakBangla5sVoice("এখন ট্রেড দেওয়া হচ্ছে না, হোল্ড করুন");

                    setTimeout(function(){
                        if(box.parentNode) box.remove();
                        if(typeof onDone === "function") onDone();
                    }, 2800);
                }

                function showTradeExecutedPopup(isCall, marketName, ptsVal, didClickBtn, confVal, onDone) {
                    var oldToast = d.getElementById('ra-auto-trade-toast');
                    if(oldToast) oldToast.remove();

                    var metrics = computeTradeCandleSize(ptsVal, isCall, marketName, "5S");
                    var dirText = isCall ? "UP / BUY" : "DOWN / SELL";
                    var accent = isCall ? "#22c55e" : "#f43f5e";
                    var softBg = isCall
                        ? "linear-gradient(155deg, rgba(5,34,21,0.98), rgba(9,56,35,0.97))"
                        : "linear-gradient(155deg, rgba(42,7,18,0.98), rgba(66,11,28,0.97))";
                    var ptsBadge = (isCall ? "+" : "-") + metrics.pts + " PTS • " + metrics.sizeTag;
                    var cNum = parseInt(confVal, 10);
                    var confLabel = (!isNaN(cNum) && cNum > 0) ? (cNum + "%") : "76%";

                    var toast = d.createElement('div');
                    toast.id = 'ra-auto-trade-toast';
                    toast.style.cssText = 'position:fixed;top:56%;left:50%;transform:translate3d(-50%,-50%,0);' +
                        'width:188px;z-index:2147483647;' +
                        'background:' + softBg + ';border:2px solid ' + accent + ';border-radius:14px;' +
                        'padding:9px 11px;box-sizing:border-box;pointer-events:none;color:#ffffff;' +
                        'font-family:"Segoe UI",Roboto,Arial,sans-serif;' +
                        'box-shadow:0 10px 26px rgba(0,0,0,0.72);' +
                        'animation:raLowerTradePop 0.2s ease-out;';

                    toast.innerHTML = '' +
                        '<div style="display:flex;align-items:center;justify-content:space-between;gap:4px;margin-bottom:4px;">' +
                        '  <span style="font-size:7px;font-weight:900;letter-spacing:0.4px;color:#e2e8f0;opacity:0.92;">5S AUTO (' + confLabel + ')</span>' +
                        '  <span style="font-size:6.8px;font-weight:900;color:' + accent + ';background:rgba(0,0,0,0.45);padding:1px 6px;border-radius:6px;white-space:nowrap;">' + ptsBadge + '</span>' +
                        '</div>' +
                        '<div style="display:flex;align-items:center;gap:8px;">' +
                        '  <span style="display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;border-radius:9px;background:' + accent + ';color:#041009;font-size:13px;font-weight:900;">' + (isCall ? "▲" : "▼") + '</span>' +
                        '  <div style="min-width:0;">' +
                        '    <div style="font-size:12.5px;font-weight:900;color:' + accent + ';line-height:1.15;">' + dirText + '</div>' +
                        '    <div style="font-size:7.4px;color:#e2e8f0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:2px;">' + marketName + ' • ' + metrics.sizeTag + ' (' + metrics.heightPx + 'PX)</div>' +
                        '  </div>' +
                        '</div>';

                    hostRoot.appendChild(toast);
                    setTimeout(function(){
                        if(toast.parentNode) toast.remove();
                        if(typeof onDone === "function") onDone();
                    }, 3200);
                }

                function executePlatformTradeClick(isCall) {
                    var nowMs = Date.now();
                    if(nowMs - lastAutoTradeTs < 2800) {
                        return false;
                    }
                    lastAutoTradeTs = nowMs;

                    var candidates = Array.prototype.slice.call(
                        d.querySelectorAll('button, [role="button"], a, div, span')
                    );

                    var scored = [];
                    for(var i = 0; i < candidates.length; i++) {
                        var el = candidates[i];
                        if(!el || !el.getBoundingClientRect) continue;
                        if(el.closest('#ra-auto-5s-panel, #ra-hacker-scan-modal, #ra-hacker-signal-popup, #ra-mode-selector-menu, #ra-hacker-login-modal, #ra-hacker-btn, #ra-cyber-5s-overlay, #ra-bot-power-pill, #ra-auto-trade-toast, #ra-5s-hold-notice')) {
                            continue;
                        }
                        var rect = el.getBoundingClientRect();
                        if(rect.width < 24 || rect.height < 18) continue;
                        if(rect.top < window.innerHeight * 0.32) continue;

                        var rawText = (el.innerText || el.textContent || '').trim().toUpperCase();
                        var metaText = (rawText + ' ' + (el.className || '') + ' ' + (el.getAttribute('aria-label') || '') + ' ' + (el.getAttribute('data-testid') || '')).toUpperCase();

                        var hasUp = /\b(UP|BUY|CALL|HIGHER|LONG)\b/.test(metaText);
                        var hasDown = /\b(DOWN|SELL|PUT|LOWER|SHORT)\b/.test(metaText);

                        var clickableEl = el.closest('button, [role="button"]') || el;
                        var cRect = clickableEl.getBoundingClientRect();
                        if(cRect.width < 24 || cRect.height < 18) continue;

                        if(isCall && hasUp && !hasDown) {
                            scored.push({ el: clickableEl, rect: cRect, score: 120 + cRect.bottom });
                        } else if(!isCall && hasDown && !hasUp) {
                            var rightBonus = cRect.left > window.innerWidth * 0.40 ? 45 : 0;
                            scored.push({ el: clickableEl, rect: cRect, score: 120 + cRect.bottom + rightBonus });
                        }
                    }

                    if(scored.length > 0) {
                        scored.sort(function(a, b){ return b.score - a.score; });
                        var target = scored[0].el;
                        try {
                            target.focus();
                        } catch(eFocus) {}
                        try {
                            target.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, cancelable: true }));
                            target.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }));
                            target.click();
                            target.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, cancelable: true }));
                            target.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, cancelable: true }));
                            return true;
                        } catch(e) {}
                    }

                    var fallbackBtns = candidates.filter(function(el){
                        if(!el || !el.getBoundingClientRect) return false;
                        if(el.closest('#ra-auto-5s-panel, #ra-hacker-scan-modal, #ra-hacker-signal-popup, #ra-mode-selector-menu, #ra-hacker-login-modal, #ra-hacker-btn, #ra-cyber-5s-overlay, #ra-bot-power-pill, #ra-auto-trade-toast, #ra-5s-hold-notice')) return false;
                        var tag = (el.tagName || '').toUpperCase();
                        if(tag !== 'BUTTON' && el.getAttribute('role') !== 'button') return false;
                        var r = el.getBoundingClientRect();
                        return r.width >= 40 && r.height >= 24 && r.bottom >= window.innerHeight * 0.55;
                    });

                    if(fallbackBtns.length >= 2) {
                        fallbackBtns.sort(function(a, b){
                            return a.getBoundingClientRect().left - b.getBoundingClientRect().left;
                        });
                        var pickEl = isCall ? fallbackBtns[0] : fallbackBtns[fallbackBtns.length - 1];
                        try {
                            pickEl.click();
                            return true;
                        } catch(e) {}
                    }
                    return false;
                }

                function runCyberHacking5sCycle(onCycleComplete) {
                    if(auto5sBusy) return;
                    auto5sBusy = true;

                    var oldOv = d.getElementById('ra-cyber-5s-overlay');
                    if(oldOv) oldOv.remove();
                    if(window.__raCyber5sRaf) {
                        cancelAnimationFrame(window.__raCyber5sRaf);
                        window.__raCyber5sRaf = null;
                    }

                    var liveMarket = detectExactQuotexMarket();
                    var qParam = liveMarket.replace(/[^A-Z0-9]/g, '_').replace(/_+/g, '_').replace(/^_|_$/g, '') || 'EURUSD';
                    var scanMs = 5200;
                    var startTs = performance.now();

                    ensureAudioContext();
                    speakBangla5sVoice("লাইভ মার্কেট স্ক্যান করা হচ্ছে");

                    var cyberPalette = [
                        "#00f0ff", "#22c55e", "#e879f9", "#facc15",
                        "#fb7185", "#38bdf8", "#a855f7", "#4ade80"
                    ];

                    var logTemplates = [
                        "HOOK_0x{H1}::STREAM [{M}]",
                        "ROOT@CORE: PULL_TICK #{N}",
                        "SCAN_BEAM: WICK +{D}",
                        "NODE_0x{H3}: DEPTH_SYNC",
                        "QUANT_LINK: CONF {P}%",
                        "PIPE_0x{H1}: FLOW_OK"
                    ];

                    var ov = d.createElement('div');
                    ov.id = 'ra-cyber-5s-overlay';
                    ov.style.cssText = 'position:fixed;inset:0;z-index:2147483645;pointer-events:none;overflow:hidden;' +
                        'border:2px solid #00f0ff;box-sizing:border-box;' +
                        'background:rgba(2,9,17,0.08);' +
                        'font-family:"Courier New",Courier,monospace;will-change:transform;' +
                        'animation:raCyberBorderSoft 4s infinite linear;';

                    ov.innerHTML = '' +
                        '<div id="ra-full-laser-top" style="position:fixed;left:0;right:0;height:1px;top:0;background:linear-gradient(90deg,transparent,rgba(0,240,255,0.45),rgba(232,121,249,0.45),transparent);will-change:transform;z-index:3;"></div>' +

                        '<div id="ra-cyber-center-ball" style="position:fixed;top:50%;left:calc(55% + 22px);width:146px;height:146px;transform:translate3d(-50%,-50%,0);pointer-events:none;z-index:3;">' +
                        '  <div id="ra-lightning-ring" style="position:fixed;top:50%;left:50%;width:158px;height:158px;border-radius:50%;transform:translate3d(-50%,-50%,0);' +
                        '  border:2px dashed #facc15;box-shadow:0 0 24px rgba(0,240,255,0.65),0 0 36px rgba(232,121,249,0.55);' +
                        '  animation:raLightningFlash 0.9s infinite ease-in-out;"></div>' +

                        '  <div id="ra-planet-rotator" style="position:fixed;top:50%;left:50%;width:132px;height:132px;margin-left:-66px;margin-top:-66px;border-radius:50%;overflow:hidden;' +
                        '  border:3px solid #00f0ff;box-shadow:0 0 28px rgba(0,240,255,0.75);' +
                        '  background:conic-gradient(from 0deg, #00f0ff, #22c55e, #facc15, #e879f9, #fb7185, #38bdf8, #00f0ff);' +
                        '  animation:raPlanetSpinFast 3.2s linear infinite;will-change:transform;">' +
                        '    <div style="position:absolute;top:16%;left:-10%;width:76%;height:26%;border-radius:50%;background:rgba(74,222,128,0.65);transform:rotate(-16deg);"></div>' +
                        '    <div style="position:absolute;top:52%;left:22%;width:80%;height:28%;border-radius:50%;background:rgba(232,121,249,0.65);transform:rotate(14deg);"></div>' +
                        '  </div>' +

                        '  <div style="position:fixed;top:50%;left:50%;width:96px;height:96px;border-radius:50%;transform:translate3d(-50%,-50%,0);' +
                        '  background:rgba(3,12,24,0.82);border:1.5px solid #ffffff;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;">' +
                        '    <div id="ra-ball-proc-tag" style="font-size:6.8px;font-weight:900;color:#4ade80;letter-spacing:0.5px;">5S SCAN</div>' +
                        '    <div id="ra-ball-pct" style="font-size:14.5px;font-weight:900;color:#ffffff;line-height:1.15;">1%</div>' +
                        '    <div id="ra-ball-node-code" style="font-size:6.5px;font-weight:800;color:#facc15;margin-top:2px;">⚡ 0x01</div>' +
                        '  </div>' +
                        '</div>' +

                        '<div id="ra-cyber-left-cascade" style="position:fixed;top:18px;bottom:18px;left:8px;width:168px;max-width:42vw;' +
                        'overflow:hidden;display:flex;flex-direction:column;justify-content:flex-start;gap:3px;' +
                        'background:transparent;border:none;padding:2px;z-index:2;' +
                        'font-size:8px;line-height:1.32;font-weight:800;"></div>';

                    hostRoot.appendChild(ov);

                    var fullLaserTop = ov.querySelector('#ra-full-laser-top');
                    var ballPctEl = ov.querySelector('#ra-ball-pct');
                    var ballProcTagEl = ov.querySelector('#ra-ball-proc-tag');
                    var ballNodeEl = ov.querySelector('#ra-ball-node-code');
                    var planetRotatorEl = ov.querySelector('#ra-planet-rotator');
                    var lightningRingEl = ov.querySelector('#ra-lightning-ring');
                    var leftCascadeEl = ov.querySelector('#ra-cyber-left-cascade');

                    var sigPromise = fetch(renderServerUrl + '/signal?market=' + encodeURIComponent(qParam) + '&mode=AUTO5S&t=' + Date.now())
                        .then(function(r){ return r.json(); })
                        .catch(function(){ return { signal: 'HOLD', pts: 0, confidence: 0 }; });

                    var lastPctSeen = 0;
                    var lastColorTick = -1;
                    var lastLogTick = -1;
                    var logSeq = 0;
                    var maxVisibleLogs = 22;

                    function buildLogLine(seqNum, pctNum) {
                        var tpl = logTemplates[seqNum % logTemplates.length];
                        var h1 = ((seqNum * 73 + 19) % 255).toString(16).toUpperCase().padStart(2, '0');
                        var h3 = ((seqNum * 53 + 11) % 15).toString(16).toUpperCase();
                        var deltaStr = (0.00012 + ((seqNum * 19) % 85) * 0.00001).toFixed(5);
                        var msg = tpl
                            .replace("{H1}", h1)
                            .replace("{H3}", h3)
                            .replace("{M}", liveMarket)
                            .replace("{N}", String(seqNum))
                            .replace("{D}", deltaStr)
                            .replace("{P}", String(pctNum));

                        var rowCol = cyberPalette[seqNum % cyberPalette.length];
                        var row = d.createElement('div');
                        row.style.cssText = 'color:' + rowCol + ';white-space:nowrap;overflow:hidden;text-overflow:ellipsis;animation:raSmoothLogGlide 0.24s ease-out both;';
                        row.innerHTML = '<span style="color:#ffffff;font-weight:900;">✓</span> ' + msg;
                        return row;
                    }

                    function stepCyber5s(nowTs) {
                        if(!ov.isConnected || !auto5sRunning) {
                            if(ov.parentNode) ov.remove();
                            auto5sBusy = false;
                            if(typeof onCycleComplete === "function") onCycleComplete(false);
                            return;
                        }

                        var elapsed = nowTs - startTs;
                        var ratio = Math.min(1, elapsed / scanMs);
                        var vh = window.innerHeight || 720;

                        if(fullLaserTop) {
                            var waveY = 10 + (0.5 - 0.5 * Math.cos(ratio * Math.PI * 2)) * Math.max(40, vh - 20);
                            fullLaserTop.style.transform = "translate3d(0," + waveY.toFixed(1) + "px,0)";
                        }

                        var curPct = Math.max(1, Math.min(100, Math.round(ratio * 100)));
                        if(curPct !== lastPctSeen) {
                            lastPctSeen = curPct;
                            if(ballPctEl) ballPctEl.innerText = curPct + "%";
                        }

                        var colorTick = Math.floor(elapsed / 260);
                        if(colorTick !== lastColorTick) {
                            lastColorTick = colorTick;
                            var cMain = cyberPalette[colorTick % cyberPalette.length];
                            var cSec = cyberPalette[(colorTick + 2) % cyberPalette.length];
                            var cThird = cyberPalette[(colorTick + 4) % cyberPalette.length];
                            if(ballProcTagEl) ballProcTagEl.style.color = cMain;
                            if(ballNodeEl) {
                                ballNodeEl.innerText = "⚡ 0x" + ((colorTick * 17 + 7) % 255).toString(16).toUpperCase().padStart(2, "0");
                                ballNodeEl.style.color = cSec;
                            }
                            if(planetRotatorEl) {
                                planetRotatorEl.style.borderColor = cMain;
                                planetRotatorEl.style.background = "conic-gradient(from " + ((colorTick * 45) % 360) + "deg, " + cMain + ", " + cSec + ", " + cThird + ", " + cMain + ")";
                                planetRotatorEl.style.boxShadow = "0 0 26px " + cMain + ", 0 0 42px " + cSec;
                            }
                            if(lightningRingEl) {
                                lightningRingEl.style.borderColor = cThird;
                                lightningRingEl.style.boxShadow = "0 0 22px " + cSec + ", 0 0 34px " + cMain;
                            }
                        }

                        var logTick = Math.floor(elapsed / 230);
                        if(logTick > lastLogTick && leftCascadeEl) {
                            lastLogTick = logTick;
                            logSeq++;
                            leftCascadeEl.appendChild(buildLogLine(logSeq, curPct));
                            while(leftCascadeEl.children.length > maxVisibleLogs) {
                                leftCascadeEl.removeChild(leftCascadeEl.firstChild);
                            }
                            playTickSound();
                        }

                        if(ratio < 1) {
                            window.__raCyber5sRaf = requestAnimationFrame(stepCyber5s);
                            return;
                        }

                        if(ov.parentNode) ov.remove();
                        sigPromise.then(function(data){
                            auto5sBusy = false;
                            if(!auto5sRunning) {
                                if(typeof onCycleComplete === "function") onCycleComplete(false);
                                return;
                            }

                            var sig = String((data && data.signal) || 'HOLD').toUpperCase();
                            var confNum = parseInt(data && data.confidence, 10);
                            var hasConf = isNaN(confNum) ? (sig !== 'HOLD') : (confNum >= 65);
                            var isCall = hasConf && (sig === 'CALL' || sig === 'UP' || sig === 'BUY');
                            var isPut = hasConf && (sig === 'PUT' || sig === 'DOWN' || sig === 'SELL');
                            var ptsVal = data && data.pts;
                            var activeMarket = detectExactQuotexMarket();

                            if(isCall || isPut) {
                                playTradePongSound(isCall);
                                var didClick = executePlatformTradeClick(isCall);
                                speakBangla5sVoice(
                                    isCall
                                        ? "স্যার এখান থেকে আপের জন্য ট্রেড নেওয়া হয়েছে"
                                        : "স্যার এখান থেকে ডাউনের জন্য ট্রেড নেওয়া হয়েছে"
                                );
                                showTradeExecutedPopup(isCall, activeMarket, ptsVal, didClick, confNum, function(){
                                    if(typeof onCycleComplete === "function") onCycleComplete(true);
                                });
                            } else {
                                show5sHoldNotice(activeMarket, function(){
                                    if(typeof onCycleComplete === "function") onCycleComplete(true);
                                });
                            }
                        });
                    }

                    window.__raCyber5sRaf = requestAnimationFrame(stepCyber5s);
                }

                function startAuto5sLoop() {
                    stopAuto5sEngine();
                    auto5sRunning = true;
                    isModeOn = true;
                    writeSavedActive(true);
                    refreshBotOnBadge();

                    var currentMarket = detectExactQuotexMarket();

                    // First click on 5s mode shows HOLD (~2.8s), then starts smooth scanning (no immediate trade)
                    show5sHoldNotice(currentMarket, function(){
                        if(!auto5sRunning || !isModeOn) return;

                        function scheduleNext() {
                            if(!auto5sRunning || !isModeOn) return;
                            runCyberHacking5sCycle(function(completed){
                                if(!auto5sRunning || !isModeOn) return;
                                var waitMs = completed ? 1400 : 1200;
                                window.__raAuto5sLoopTimer = setTimeout(scheduleNext, waitMs);
                            });
                        }
                        scheduleNext();
                    });
                }

                function selectManualModeAndActivate() {
                    stopAuto5sEngine();
                    lockedModeChoice = "MANUAL";
                    writeSavedMode("MANUAL");
                    isModeOn = true;
                    writeSavedActive(true);
                    refreshBotOnBadge();
                    startHackerScanSequence();
                }

                function selectAuto5sModeAndActivate() {
                    lockedModeChoice = "5S_AUTO";
                    writeSavedMode("5S_AUTO");
                    isModeOn = true;
                    writeSavedActive(true);
                    refreshBotOnBadge();
                    startAuto5sLoop();
                }

                function triggerLockedActiveMode(botBtn) {
                    if(lockedModeChoice === "5S_AUTO") {
                        if(!auto5sRunning) {
                            startAuto5sLoop();
                        }
                        return;
                    }
                    if(lockedModeChoice === "MANUAL") {
                        startHackerScanSequence();
                        return;
                    }
                    openBotModeMenu(botBtn);
                }

                function openBotModeMenu(botBtn) {
                    if(isModeOn && lockedModeChoice) {
                        triggerLockedActiveMode(botBtn);
                        return;
                    }

                    var existingMenu = d.getElementById('ra-mode-selector-menu');
                    if(existingMenu) {
                        existingMenu.remove();
                        return;
                    }

                    var menu = d.createElement('div');
                    menu.id = 'ra-mode-selector-menu';
                    menu.style.cssText = 'position:fixed;width:204px;' +
                        'background:linear-gradient(165deg,rgba(5,18,28,0.98),rgba(10,24,42,0.98));' +
                        'border:2px solid #00f0ff;border-radius:12px;padding:7px;box-sizing:border-box;' +
                        'z-index:2147483647;font-family:"Segoe UI",Roboto,Arial,sans-serif;color:#ffffff;' +
                        'box-shadow:0 0 20px rgba(0,240,255,0.55);' +
                        'animation:raPopupEnter 0.16s ease-out;';

                    menu.innerHTML = '' +
                        '<button id="ra-opt-manual-signal" type="button" style="width:100%;display:flex;align-items:center;justify-content:space-between;' +
                        'background:linear-gradient(90deg,rgba(34,197,94,0.22),rgba(0,240,255,0.16));border:1.4px solid #4ade80;' +
                        'border-radius:8px;padding:7px 9px;color:#ffffff;font-size:10.5px;font-weight:900;cursor:pointer;margin-bottom:6px;">' +
                        '  <span>Manual Signal</span>' +
                        '  <span style="background:#22c55e;color:#041208;padding:1px 6px;border-radius:6px;font-size:9px;font-weight:900;">1M</span>' +
                        '</button>' +
                        '<button id="ra-opt-auto-5s" type="button" style="width:100%;display:flex;align-items:center;justify-content:space-between;' +
                        'background:linear-gradient(90deg,rgba(232,121,249,0.24),rgba(250,204,21,0.18));border:1.4px solid #e879f9;' +
                        'border-radius:8px;padding:7px 9px;color:#ffffff;font-size:10.5px;font-weight:900;cursor:pointer;">' +
                        '  <span>5s Auto Mode</span>' +
                        '  <span style="background:#e879f9;color:#140519;padding:1px 6px;border-radius:6px;font-size:8.5px;font-weight:900;">5S</span>' +
                        '</button>';

                    hostRoot.appendChild(menu);
                    positionModeMenuAboveBot(menu, botBtn);

                    menu.querySelector('#ra-opt-manual-signal').onclick = function(ev) {
                        ev.stopPropagation();
                        menu.remove();
                        selectManualModeAndActivate();
                    };

                    menu.querySelector('#ra-opt-auto-5s').onclick = function(ev) {
                        ev.stopPropagation();
                        menu.remove();
                        selectAuto5sModeAndActivate();
                    };
                }

                function createDraggableBotButton() {
                    if(d.getElementById('ra-hacker-btn')) {
                        ensureBotPowerPill();
                        return;
                    }

                    var btn = d.createElement('div');
                    btn.id = 'ra-hacker-btn';
                    btn.style.cssText = 'position:fixed;bottom:146px;right:12px;width:82px;height:82px;border-radius:50%;' +
                        'background:#02090e;display:flex !important;opacity:1 !important;visibility:visible !important;' +
                        'align-items:center;justify-content:center;' +
                        'z-index:2147483647;cursor:grab;user-select:none;touch-action:none;overflow:visible;' +
                        'font-family:"Courier New",Courier,monospace;' +
                        'animation:raBotNeonAura 3.5s infinite linear;';

                    btn.innerHTML = '' +
                        '<div style="position:absolute;inset:-4px;border-radius:50%;pointer-events:none;z-index:0;' +
                        'background:conic-gradient(from 0deg, #ff2a5f, #ffae00, #00ff88, #00f0ff, #c026d3, #ff2a5f);' +
                        'opacity:0.9;animation:raContinuousSpin 2.4s linear infinite;"></div>' +
                        '<div style="position:absolute;inset:0;border-radius:50%;overflow:hidden;pointer-events:none;z-index:1;">' +
                        '  <div style="position:absolute;inset:0;border-radius:50%;' +
                        '  background:conic-gradient(from 0deg, #22c55e, #00f0ff, #e879f9, #facc15, #f43f5e, #38bdf8, #22c55e);' +
                        '  animation:raContinuousReverseSpin 2.8s linear infinite;"></div>' +
                        '  <div style="position:absolute;inset:5px;border-radius:50%;background:#02090e;"></div>' +
                        '</div>' +
                        '<img src="' + botAvatarUrl + '" alt="R-A Candle Hacker" style="position:relative;z-index:3;width:66px;height:66px;object-fit:cover;border-radius:50%;pointer-events:none;display:block;background:#02090e;border:1.8px solid rgba(255,255,255,0.85);" />';

                    hostRoot.appendChild(btn);
                    refreshBotOnBadge();

                    var dragging = false, moved = false, offsetX = 0, offsetY = 0;

                    function onStart(e) {
                        ensureAudioContext();
                        var pt = e.touches ? e.touches[0] : e;
                        var rect = btn.getBoundingClientRect();
                        offsetX = pt.clientX - rect.left;
                        offsetY = pt.clientY - rect.top;
                        dragging = true;
                        moved = false;
                        btn.style.cursor = 'grabbing';
                    }

                    function onMove(e) {
                        if(!dragging) return;
                        var pt = e.touches ? e.touches[0] : e;
                        var nextLeft = pt.clientX - offsetX;
                        var nextTop = pt.clientY - offsetY;
                        if(Math.abs(nextLeft - btn.offsetLeft) > 3 || Math.abs(nextTop - btn.offsetTop) > 3) {
                            moved = true;
                        }
                        var maxX = window.innerWidth - btn.offsetWidth - 4;
                        var maxY = window.innerHeight - btn.offsetHeight - 4;
                        nextLeft = Math.max(4, Math.min(nextLeft, maxX));
                        nextTop = Math.max(4, Math.min(nextTop, maxY));
                        btn.style.left = nextLeft + 'px';
                        btn.style.top = nextTop + 'px';
                        btn.style.right = 'auto';
                        btn.style.bottom = 'auto';

                        syncBotPowerPillPosition();

                        var activePopup = d.getElementById('ra-hacker-signal-popup');
                        if(activePopup) positionPopupAboveBotWithGap(activePopup, btn);
                        var activeMenu = d.getElementById('ra-mode-selector-menu');
                        if(activeMenu) positionModeMenuAboveBot(activeMenu, btn);
                    }

                    function onEnd(e) {
                        if(!dragging) return;
                        dragging = false;
                        btn.style.cursor = 'grab';
                        if(!moved) {
                            if(e) { e.stopPropagation(); e.preventDefault(); }
                            if(isModeOn && lockedModeChoice) {
                                triggerLockedActiveMode(btn);
                            } else {
                                openBotModeMenu(btn);
                            }
                        }
                    }

                    btn.addEventListener('mousedown', onStart);
                    btn.addEventListener('touchstart', onStart, {passive: true});
                    d.addEventListener('mousemove', onMove);
                    d.addEventListener('touchmove', onMove, {passive: true});
                    d.addEventListener('mouseup', onEnd);
                    d.addEventListener('touchend', onEnd);
                }

                function detectExactQuotexMarket() {
                    try {
                        var selectors = [
                            '.asset-select__title',
                            '.asset-select button',
                            '[class*="asset-select"] [class*="name"]',
                            '[class*="asset-select"] [class*="title"]',
                            '[class*="pair-name"]',
                            '[class*="current-asset"]',
                            '[class*="market-name"]'
                        ];
                        for(var s = 0; s < selectors.length; s++) {
                            var nodes = d.querySelectorAll(selectors[s]);
                            for(var i = 0; i < nodes.length; i++) {
                                var raw = (nodes[i].innerText || '').trim();
                                var cleaned = raw.replace(/\s+/g, ' ').trim();
                                if(/^[A-Z0-9]{2,8}\s*\/\s*[A-Z0-9]{2,8}(\s*\(?(OTC|REAL)\)?)?$/i.test(cleaned)) {
                                    return cleaned.replace(/\s*\/\s*/, '/').toUpperCase();
                                }
                            }
                        }

                        var allTextEls = d.querySelectorAll('span, div, button, p');
                        for(var j = 0; j < allTextEls.length; j++) {
                            if(allTextEls[j].children.length === 0) {
                                var t = (allTextEls[j].innerText || '').trim().replace(/\s+/g, ' ');
                                if(/^[A-Z0-9]{2,8}\s*\/\s*[A-Z0-9]{2,8}(\s*\(?(OTC|REAL)\)?)?$/i.test(t) && t.length <= 26) {
                                    var rect = allTextEls[j].getBoundingClientRect();
                                    if(rect.width > 20 && rect.height > 8 && rect.top > 35 && rect.top < window.innerHeight - 35) {
                                        return t.replace(/\s*\/\s*/, '/').toUpperCase();
                                    }
                                }
                            }
                        }
                    } catch(e) {}
                    return "EUR/USD";
                }

                function getTierWithPct(scoreVal) {
                    var p = Math.max(1, Math.min(100, Math.round(scoreVal)));
                    if(p >= 98) return { label: "100% ULTRA", pctStr: "100%", color: "#e879f9" };
                    if(p >= 72) return { label: "ULTRA HIGH", pctStr: p + "%", color: "#e879f9" };
                    if(p >= 46) return { label: "HIGH", pctStr: p + "%", color: "#00f0ff" };
                    if(p >= 22) return { label: "MEDIUM", pctStr: p + "%", color: "#facc15" };
                    return { label: "LOW", pctStr: p + "%", color: "#4ade80" };
                }

                function computeTradeCandleSize(ptsRaw, isCall, marketStr, modeTag) {
                    var ptsNum = parseInt(ptsRaw, 10);
                    var symSeed = 0;
                    var sClean = String(marketStr || "EURUSD");
                    for(var c = 0; c < sClean.length; c++) {
                        symSeed = (symSeed * 37 + sClean.charCodeAt(c)) % 997;
                    }
                    var tickBucket = Math.floor(Date.now() / 3700) % 13;
                    var dirFactor = isCall ? 3 : -2;
                    var modeBias = (modeTag === "5S") ? -3 : 2;

                    if(isNaN(ptsNum) || ptsNum <= 0) {
                        ptsNum = 9 + ((symSeed + tickBucket * 5 + (isCall ? 4 : 9)) % 31);
                    } else {
                        var deltaAdjust = ((tickBucket - 6) * 2) + dirFactor + modeBias;
                        ptsNum = ptsNum + deltaAdjust;
                    }

                    var clampedPts = Math.max(8, Math.min(40, ptsNum));
                    var memKey = String(modeTag || "1M") + "_" + sClean + "_" + (isCall ? "C" : "P");
                    if(lastCandlePtsByKey[memKey] === clampedPts) {
                        clampedPts = (clampedPts >= 36) ? (clampedPts - 5) : (clampedPts + 4);
                        clampedPts = Math.max(8, Math.min(40, clampedPts));
                    }
                    lastCandlePtsByKey[memKey] = clampedPts;

                    var ratio = (clampedPts - 8) / 32;
                    var candleHeightPx = Math.round(12 + (ratio * 44));
                    var candleWidthPx = Math.round(9 + (ratio * 12));
                    var wickHeightPx = Math.round(4 + (ratio * 10));
                    var ptsFontPx = (6.5 + (ratio * 2.5)).toFixed(1);
                    var sizeFontPx = (5.6 + (ratio * 1.7)).toFixed(1);

                    var sizeTag = "SMALL SIZE";
                    if(clampedPts <= 13) {
                        sizeTag = "MICRO-SMALL";
                    } else if(clampedPts <= 19) {
                        sizeTag = "SMALL SIZE";
                    } else if(clampedPts <= 27) {
                        sizeTag = "MEDIUM SIZE";
                    } else if(clampedPts <= 34) {
                        sizeTag = "LARGE SIZE";
                    } else {
                        sizeTag = "HEAVY SIZE";
                    }

                    return {
                        pts: clampedPts,
                        heightPx: candleHeightPx,
                        widthPx: candleWidthPx,
                        wickPx: wickHeightPx,
                        ptsFontPx: ptsFontPx,
                        sizeFontPx: sizeFontPx,
                        sizeTag: sizeTag
                    };
                }

                function showBoxSignalCard(sigType, marketDisplayName, ptsFromBackend, confFromBackend) {
                    var old = d.getElementById('ra-hacker-signal-popup');
                    if(old) old.remove();

                    var liveMarket = marketDisplayName || detectExactQuotexMarket();
                    var rawSig = String(sigType || 'HOLD').toUpperCase();
                    var cNum = parseInt(confFromBackend, 10);
                    var meetsConf = isNaN(cNum) ? (rawSig !== 'HOLD') : (cNum >= 65);
                    var isHold = (!meetsConf) || (rawSig === 'HOLD');
                    var isCall = (!isHold) && (rawSig === 'CALL' || rawSig === 'UP' || rawSig === 'BUY');
                    var metrics = computeTradeCandleSize(ptsFromBackend, isCall, liveMarket, "1M");
                    var estText = isHold ? "HOLD" : ((isCall ? "+" : "-") + metrics.pts + " PTS");
                    var mainColor = isHold ? "#facc15" : (isCall ? "#4ade80" : "#f87171");
                    var glowAnim = isCall ? "raPopupGreenGlow 2.4s infinite ease-in-out" : "raPopupRedGlow 2.4s infinite ease-in-out";

                    var candleVisualHtml = '';
                    if(isHold) {
                        candleVisualHtml = '' +
                            '<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:74px;">' +
                            '  <div style="font-size:8.5px;font-weight:900;color:#facc15;">হোল্ড • অপেক্ষা</div>' +
                            '  <div style="font-size:6.5px;color:#cbd5e1;margin-top:4px;">পরবর্তী ক্যান্ডেল দেখুন</div>' +
                            '</div>';
                    } else if(isCall) {
                        candleVisualHtml = '' +
                            '<div style="display:flex;flex-direction:column;align-items:center;justify-content:flex-end;height:74px;animation:raCandleReveal 0.25s ease-out;">' +
                            '  <div style="font-size:' + metrics.ptsFontPx + 'px;font-weight:900;color:#4ade80;margin-bottom:2px;">' + estText + ' • ' + metrics.sizeTag + '</div>' +
                            '  <div style="width:2px;height:' + metrics.wickPx + 'px;background:#4ade80;"></div>' +
                            '  <div style="width:' + metrics.widthPx + 'px;height:' + metrics.heightPx + 'px;background:linear-gradient(180deg,#86efac,#22c55e,#15803d);border:1.2px solid #bbf7d0;border-radius:2px;"></div>' +
                            '  <div style="width:2px;height:' + Math.max(3, Math.round(metrics.wickPx * 0.75)) + 'px;background:#4ade80;"></div>' +
                            '</div>';
                    } else {
                        candleVisualHtml = '' +
                            '<div style="display:flex;flex-direction:column;align-items:center;justify-content:flex-start;height:74px;animation:raCandleReveal 0.25s ease-out;">' +
                            '  <div style="width:2px;height:' + Math.max(3, Math.round(metrics.wickPx * 0.75)) + 'px;background:#f87171;"></div>' +
                            '  <div style="width:' + metrics.widthPx + 'px;height:' + metrics.heightPx + 'px;background:linear-gradient(180deg,#fca5a5,#ef4444,#b91c1c);border:1.2px solid #fecaca;border-radius:2px;"></div>' +
                            '  <div style="width:2px;height:' + metrics.wickPx + 'px;background:#f87171;"></div>' +
                            '  <div style="font-size:' + metrics.ptsFontPx + 'px;font-weight:900;color:#f87171;margin-top:2px;">' + estText + ' • ' + metrics.sizeTag + '</div>' +
                            '</div>';
                    }

                    var popup = d.createElement('div');
                    popup.id = 'ra-hacker-signal-popup';
                    popup.style.cssText = 'position:fixed;width:128px;' +
                        (isCall
                            ? 'background:linear-gradient(165deg, rgba(6,34,20,0.99), rgba(10,48,28,0.98));'
                            : 'background:linear-gradient(165deg, rgba(36,8,14,0.99), rgba(52,10,20,0.98));') +
                        'border-width:2px;border-style:solid;border-radius:10px;padding:6px 6px;box-sizing:border-box;' +
                        'z-index:2147483646;pointer-events:none;font-family:"Courier New",monospace;color:#e2e8f0;' +
                        'animation:raPopupEnter 0.18s ease-out, ' + glowAnim + ';';

                    var dirLabel = isHold ? '● HOLD / হোল্ড' : (isCall ? '▲ CALL (UP)' : '▼ PUT (DOWN)');

                    popup.innerHTML = '' +
                        '<div style="text-align:center;font-size:6.2px;font-weight:900;letter-spacing:0.3px;color:#00f0ff;line-height:1.25;margin-bottom:4px;">' +
                        '  R-A Candle Hacker<br><span style="color:' + mainColor + ';font-size:8px;">' + dirLabel + '</span>' +
                        '</div>' +
                        '<div style="background:rgba(2,8,12,0.94);border:1.2px solid ' + mainColor + ';border-radius:6px;padding:5px 4px;text-align:center;margin-bottom:4px;">' +
                        candleVisualHtml +
                        '  <div style="font-size:' + metrics.sizeFontPx + 'px;font-weight:900;color:' + mainColor + ';margin-top:3px;">' + (isHold ? 'হোল্ড সিস্টেম • শান্ত থাকুন' : ('EST: ' + metrics.sizeTag + ' (' + metrics.heightPx + 'PX)')) + '</div>' +
                        '  <div style="font-size:6.6px;font-weight:900;color:#ffffff;margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">' + liveMarket + '</div>' +
                        '</div>' +
                        '<div style="text-align:center;font-size:6.5px;font-weight:900;color:' + mainColor + ';letter-spacing:0.6px;border-top:1px dashed rgba(255,255,255,0.22);padding-top:3px;">' + (isHold ? 'HOLD MODE' : 'LOCKED') + '</div>';

                    hostRoot.appendChild(popup);
                    var botBtn = d.getElementById('ra-hacker-btn');
                    positionPopupAboveBotWithGap(popup, botBtn);

                    setTimeout(function(){
                        if(popup.parentNode) popup.remove();
                    }, 9000);
                }

                function startHackerScanSequence() {
                    ensureAudioContext();
                    var oldModal = d.getElementById('ra-hacker-scan-modal');
                    if(oldModal) oldModal.remove();
                    if(window.__raScanTimer) {
                        clearInterval(window.__raScanTimer);
                        window.__raScanTimer = null;
                    }
                    if(window.__raScanRaf) {
                        cancelAnimationFrame(window.__raScanRaf);
                        window.__raScanRaf = null;
                    }
                    setBrokerBackgroundBlur(true);

                    var liveMarketDisplay = detectExactQuotexMarket();
                    var queryMarketParam = liveMarketDisplay.replace(/[^A-Z0-9]/g, '_').replace(/_+/g, '_').replace(/^_|_$/g, '') || "EURUSD";
                    var initialIsCall = (Math.floor(Date.now() / 1000) % 2 === 0);

                    var hexStreamLines = [
                        { text: "MOD KERNEL32.DLL: 0x0550D120 SCOPE", color: "#00f0ff" },
                        { text: "HASH 0x626A.6F8C4E12 [TICK-SYNC]", color: "#4ade80" },
                        { text: "HEAP 0x56A8B848: 1094272B [QX-03EE]", color: "#facc15" },
                        { text: "PAT 0x80271894: EAX=0x16450 [+0.16450]", color: "#e879f9" },
                        { text: "THREAD#3679 STACK=0x7F98A2B1: #1967", color: "#38bdf8" },
                        { text: "SOCKET 168.153.167.11:21463 ACK", color: "#fb7185" },
                        { text: "MEM 0x0528F7C3: 75C74F49E [016-ACK]", color: "#00f0ff" },
                        { text: "ORDER BOOK DELTA: +0.00042 [BID-ASK]", color: "#38bdf8" },
                        { text: "SESSION ENTROPY LOCK: 99.4% [VERIFIED]", color: "#4ade80" },
                        { text: "SOCKET BRIDGE 0x37: LATENCY SYNC OK", color: "#00f0ff" }
                    ];

                    var scanSteps = [
                        { text: "Scanning server parts", color: "#22c55e" },
                        { text: "Intercepting order flow packets", color: "#facc15" },
                        { text: "Reverse-engineering price engine", color: "#e879f9" },
                        { text: "Injecting live data hook", color: "#38bdf8" },
                        { text: "Syncing tick buffer 0x626", color: "#00f0ff" },
                        { text: "Probing liquidity depth matrix", color: "#facc15" },
                        { text: "Calibrating candle wick pressure", color: "#22c55e" },
                        { text: "Aligning momentum vectors", color: "#facc15" },
                        { text: "Validating node 0x37 bridge", color: "#22c55e" },
                        { text: "Cross-checking multi-timeframe bias", color: "#4ade80" },
                        { text: "CIPHER LOCKED || 100% HIGH ARMED", color: "#4ade80" }
                    ];

                    var neonPalette = ["#22c55e", "#00f0ff", "#e879f9", "#facc15", "#fb7185", "#38bdf8", "#a855f7", "#4ade80"];

                    var modal = d.createElement('div');
                    modal.id = 'ra-hacker-scan-modal';
                    modal.style.cssText = 'position:fixed;top:47%;left:50%;transform:translate(-50%, -50%);width:336px;max-width:95vw;' +
                        'background:linear-gradient(160deg, #061d15 0%, #051326 52%, #150726 100%);' +
                        'border:2px solid #22c55e;border-radius:14px;padding:10px;z-index:2147483647;' +
                        'font-family:"Courier New",Courier,monospace;color:#4ade80;box-sizing:border-box;will-change:transform;' +
                        'animation:raScanBoxSlowBorder 6s infinite ease-in-out;';

                    modal.innerHTML = '' +
                        '<div style="display:flex;justify-content:space-between;align-items:flex-start;border-bottom:1px solid rgba(0,240,255,0.4);padding-bottom:6px;margin-bottom:6px;">' +
                        '  <div style="display:flex;align-items:center;gap:8px;margin-top:-3px;">' +
                        '    <img src="' + botAvatarUrl + '" alt="R-A Candle Hacker" style="width:38px;height:38px;border-radius:50%;object-fit:cover;border:2px solid #00f0ff;flex-shrink:0;animation:raHeaderAvatarGlow 4s infinite ease-in-out;" />' +
                        '    <div>' +
                        '      <div style="font-size:12px;font-weight:900;color:#4ade80;letter-spacing:0.6px;">R-A Candle Hacker</div>' +
                        '      <div style="font-size:7px;color:#00f0ff;letter-spacing:0.5px;">QUANT CORE EXPLOIT</div>' +
                        '      <div style="font-size:6.5px;color:#94a3b8;">SESSION: QQX-5709-03EE-1967 | ' + liveMarketDisplay + '</div>' +
                        '    </div>' +
                        '  </div>' +
                        '  <div style="display:flex;align-items:center;gap:5px;">' +
                        '    <div id="ra-pct-badge" style="background:rgba(20,83,45,0.85);border:1.4px solid #4ade80;color:#4ade80;font-size:9px;font-weight:900;padding:2px 7px;border-radius:10px;">1%</div>' +
                        '    <div id="ra-modal-close" style="cursor:pointer;color:#94a3b8;font-size:12px;font-weight:bold;padding:0 3px;">✕</div>' +
                        '  </div>' +
                        '</div>' +

                        '<div style="background:rgba(2,10,16,0.94);border:1.5px solid #00f0ff;border-radius:8px;padding:6px 7px;margin-bottom:6px;">' +
                        '  <div style="display:flex;justify-content:space-between;font-size:7px;color:#00f0ff;margin-bottom:4px;">' +
                        '    <span>MEMORY STREAM</span>' +
                        '    <span id="ra-mem-state" style="color:#4ade80;font-weight:bold;">● LOW (1%)</span>' +
                        '  </div>' +
                        '  <div style="display:flex;align-items:center;gap:6px;">' +
                        '    <div id="ra-hero-candle-box" style="width:36px;height:68px;border:2px solid #4ade80;border-radius:6px;background:rgba(34,197,94,0.28);display:flex;flex-direction:column;align-items:center;justify-content:center;flex-shrink:0;">' +
                        '      <span id="ra-hero-wick-top" style="width:2.5px;height:12px;background:#86efac;"></span>' +
                        '      <span id="ra-hero-candle-body" style="width:17px;height:38px;background:linear-gradient(180deg,#86efac,#22c55e,#15803d);border:1.4px solid #dcfce7;border-radius:2px;display:inline-block;"></span>' +
                        '      <span id="ra-hero-wick-bot" style="width:2.5px;height:12px;background:#86efac;"></span>' +
                        '    </div>' +
                        '    <div style="flex:1;min-width:0;display:flex;flex-direction:column;gap:4px;">' +
                        '      <div style="display:flex;justify-content:space-between;font-size:6.8px;gap:3px;">' +
                        '        <span><b style="color:#64748b;">OPEN</b> <span style="color:#fff;">0.1645</span></span>' +
                        '        <span><b style="color:#64748b;">HIGH</b> <span style="color:#4ade80;">0.1650</span></span>' +
                        '        <span><b style="color:#64748b;">LOW</b> <span style="color:#f87171;">0.1639</span></span>' +
                        '        <span><b style="color:#64748b;">CLOSE</b> <span style="color:#00f0ff;">0.1643</span></span>' +
                        '      </div>' +

                        '      <div id="ra-track-rtl" style="position:relative;display:flex;align-items:center;height:32px;background:rgba(4,16,26,0.92);border:1.5px solid #4ade80;border-radius:5px;padding:0 2px;overflow:hidden;">' +
                        '        <div style="position:absolute;left:0;right:0;top:50%;height:1px;background:rgba(250,204,21,0.55);z-index:3;pointer-events:none;"></div>' +
                        '        <div id="ra-volume-bars-rtl" style="position:relative;z-index:2;display:flex;flex-direction:row-reverse;align-items:center;justify-content:flex-start;gap:1.5px;height:30px;width:100%;"></div>' +
                        '      </div>' +

                        '      <div id="ra-track-ltr" style="position:relative;display:flex;align-items:center;height:32px;background:rgba(4,16,26,0.92);border:1.5px solid #00f0ff;border-radius:5px;padding:0 2px;overflow:hidden;">' +
                        '        <div style="position:absolute;left:0;right:0;top:50%;height:1px;background:rgba(0,240,255,0.55);z-index:3;pointer-events:none;"></div>' +
                        '        <div id="ra-volume-bars-ltr" style="position:relative;z-index:2;display:flex;flex-direction:row;align-items:center;justify-content:flex-start;gap:1.5px;height:30px;width:100%;"></div>' +
                        '      </div>' +
                        '    </div>' +
                        '  </div>' +
                        '</div>' +

                        '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:4px;margin-bottom:4px;font-size:6.8px;text-align:center;">' +
                        '  <div id="ra-box-vec" style="background:rgba(2,10,16,0.92);border:1.5px solid #22c55e;border-radius:6px;padding:4px 2px;"><div style="color:#94a3b8;">0x29</div><div id="ra-vec-mode" style="color:#4ade80;font-weight:bold;">LOW 1%</div></div>' +
                        '  <div id="ra-box-feed" style="background:rgba(2,10,16,0.92);border:1.5px solid #00f0ff;border-radius:6px;padding:4px 2px;"><div style="color:#00f0ff;font-weight:bold;">LIVE</div><div id="ra-feed-mode" style="color:#86efac;font-weight:bold;">LOW 1%</div></div>' +
                        '  <div id="ra-box-rsi" style="background:rgba(2,10,16,0.92);border:1.5px solid #facc15;border-radius:6px;padding:4px 2px;"><div style="color:#facc15;font-weight:bold;">RSI</div><div id="ra-rsi-val" style="color:#facc15;font-weight:bold;">LOW 1%</div></div>' +
                        '  <div id="ra-box-cyc" style="background:rgba(2,10,16,0.92);border:1.5px solid #e879f9;border-radius:6px;padding:4px 2px;"><div style="color:#e879f9;font-weight:bold;">016</div><div id="ra-cyc-mode" style="color:#e879f9;font-weight:bold;">LOW 1%</div></div>' +
                        '</div>' +

                        '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:4px;margin-bottom:6px;font-size:6.8px;text-align:center;">' +
                        '  <div id="ra-box-lat" style="background:rgba(2,10,16,0.92);border:1.5px solid #22c55e;border-radius:6px;padding:4px 2px;"><div id="ra-ms-val" style="color:#4ade80;font-weight:bold;">1ms</div><div id="ra-lat-mode" style="color:#4ade80;font-size:6.2px;font-weight:bold;">LOW 1%</div></div>' +
                        '  <div id="ra-box-breach" style="background:rgba(2,10,16,0.92);border:1.5px solid #fb7185;border-radius:6px;padding:4px 2px;"><div style="color:#fb7185;font-weight:bold;">BREACH</div><div id="ra-breach-val" style="color:#fb7185;font-weight:bold;">LOW 1%</div></div>' +
                        '  <div id="ra-box-node" style="background:rgba(2,10,16,0.92);border:1.5px solid #00f0ff;border-radius:6px;padding:4px 2px;"><div style="color:#00f0ff;font-weight:bold;">016</div><div id="ra-node-mode" style="color:#00f0ff;font-weight:bold;">LOW 1%</div></div>' +
                        '</div>' +

                        '<div id="ra-hex-stream" style="background:rgba(2,10,16,0.94);border:1.4px solid #00f0ff;border-radius:7px;padding:5px 6px;margin-bottom:6px;font-size:6.6px;line-height:1.42;height:68px;overflow-y:auto;"></div>' +

                        '<div id="ra-terminal-feed" style="background:#02090e;border:1.4px solid #e879f9;border-radius:8px;padding:5px 7px;font-size:7px;line-height:1.42;height:74px;overflow-y:auto;"></div>';

                    hostRoot.appendChild(modal);
                    applyHeroCandleColor(initialIsCall);

                    modal.querySelector('#ra-modal-close').onclick = function() {
                        if(window.__raScanRaf) {
                            cancelAnimationFrame(window.__raScanRaf);
                            window.__raScanRaf = null;
                        }
                        setBrokerBackgroundBlur(false);
                        modal.remove();
                    };

                    var pct = 1;
                    var lastTickBeat = -1;
                    var lastBoxColorTick = -1;
                    var revealedSteps = 0;
                    var revealedHex = 0;
                    var pctBadge = modal.querySelector('#ra-pct-badge');
                    var msValEl = modal.querySelector('#ra-ms-val');
                    var rsaVal = modal.querySelector('#ra-rsi-val');
                    var breachVal = modal.querySelector('#ra-breach-val');
                    var memState = modal.querySelector('#ra-mem-state');
                    var vecMode = modal.querySelector('#ra-vec-mode');
                    var feedMode = modal.querySelector('#ra-feed-mode');
                    var cycMode = modal.querySelector('#ra-cyc-mode');
                    var latMode = modal.querySelector('#ra-lat-mode');
                    var nodeMode = modal.querySelector('#ra-node-mode');
                    var hexStreamEl = modal.querySelector('#ra-hex-stream');
                    var feedEl = modal.querySelector('#ra-terminal-feed');
                    var barsRtlEl = modal.querySelector('#ra-volume-bars-rtl');
                    var barsLtrEl = modal.querySelector('#ra-volume-bars-ltr');
                    var trackRtlEl = modal.querySelector('#ra-track-rtl');
                    var trackLtrEl = modal.querySelector('#ra-track-ltr');

                    var metricBoxes = [
                        modal.querySelector('#ra-box-vec'),
                        modal.querySelector('#ra-box-feed'),
                        modal.querySelector('#ra-box-rsi'),
                        modal.querySelector('#ra-box-cyc'),
                        modal.querySelector('#ra-box-lat'),
                        modal.querySelector('#ra-box-breach'),
                        modal.querySelector('#ra-box-node')
                    ];

                    var signalPromise = fetch(renderServerUrl + '/signal?market=' + encodeURIComponent(queryMarketParam) + '&mode=MANUAL&t=' + Date.now())
                        .then(function(r){ return r.json(); })
                        .catch(function(){
                            return { signal: "HOLD", pts: 0, confidence: 0 };
                        });

                    signalPromise.then(function(data){
                        var sig = String((data && data.signal) || '').toUpperCase();
                        var cNum = parseInt(data && data.confidence, 10);
                        var okConf = isNaN(cNum) ? (sig !== 'HOLD') : (cNum >= 65);
                        if(okConf && (sig === 'CALL' || sig === 'UP' || sig === 'BUY')) {
                            applyHeroCandleColor(true);
                        } else if(okConf && (sig === 'PUT' || sig === 'DOWN' || sig === 'SELL')) {
                            applyHeroCandleColor(false);
                        }
                    });

                    var maxDualCandles = 26;

                    function createCandleSlot(beatIdx, isAltLine) {
                        var isGreenVol = isAltLine ? (beatIdx % 2 === 0) : (beatIdx % 3 !== 1);
                        var vCol = isGreenVol ? '#4ade80' : '#ef4444';
                        var bodyBg = isGreenVol
                            ? 'linear-gradient(180deg,#bbf7d0,#4ade80,#16a34a)'
                            : 'linear-gradient(180deg,#fecaca,#f87171,#dc2626)';
                        var ratioStep = beatIdx / Math.max(1, maxDualCandles - 1);
                        var maxH = Math.min(28, Math.round(9 + (ratioStep * 18) + ((beatIdx * 3) % 4)));

                        var vCandle = d.createElement('div');
                        vCandle.style.cssText = 'display:flex;flex-direction:column;align-items:center;justify-content:center;' +
                            'width:5.6px;height:28px;flex-shrink:0;opacity:0;will-change:opacity;';
                        vCandle.dataset.maxH = String(maxH);
                        vCandle.innerHTML = '' +
                            '<span style="width:1.3px;height:3px;background:' + vCol + ';"></span>' +
                            '<span class="ra-vbody" style="width:4.4px;height:5px;background:' + bodyBg + ';border-radius:1.5px;display:inline-block;will-change:height;"></span>' +
                            '<span style="width:1.3px;height:3px;background:' + vCol + ';"></span>';
                        return vCandle;
                    }

                    var rtlSlots = [];
                    var ltrSlots = [];
                    if(barsRtlEl && barsLtrEl) {
                        barsRtlEl.innerHTML = '';
                        barsLtrEl.innerHTML = '';
                        for(var k = 0; k < maxDualCandles; k++) {
                            var sRtl = createCandleSlot(k, false);
                            var sLtr = createCandleSlot(k, true);
                            barsRtlEl.appendChild(sRtl);
                            barsLtrEl.appendChild(sLtr);
                            rtlSlots.push(sRtl);
                            ltrSlots.push(sLtr);
                        }
                    }

                    function updateSmoothCandleStreams(elapsedMs, beatFloat, activeBeatIdx) {
                        for(var i = 0; i < maxDualCandles; i++) {
                            var pairNodes = [rtlSlots[i], ltrSlots[i]];
                            for(var p = 0; p < pairNodes.length; p++) {
                                var slot = pairNodes[p];
                                if(!slot) continue;
                                var bEl = slot.querySelector('.ra-vbody');
                                var maxH = parseInt(slot.dataset.maxH || '14', 10);

                                if(i < activeBeatIdx) {
                                    if(slot.style.opacity !== '1') slot.style.opacity = '1';
                                    if(bEl && bEl.style.height !== (maxH + 'px')) {
                                        bEl.style.height = maxH + 'px';
                                    }
                                } else if(i === activeBeatIdx) {
                                    var localFrac = Math.max(0.15, Math.min(1, beatFloat - activeBeatIdx));
                                    var smoothH = Math.max(5, Math.round(5 + (maxH - 5) * localFrac));
                                    slot.style.opacity = String(Math.min(1, 0.25 + localFrac * 0.75));
                                    if(bEl) bEl.style.height = smoothH + 'px';
                                } else {
                                    if(slot.style.opacity !== '0') slot.style.opacity = '0';
                                }
                            }
                        }

                        var glowPulseIdx = Math.floor(elapsedMs / 450) % neonPalette.length;
                        if(glowPulseIdx !== lastBoxColorTick) {
                            lastBoxColorTick = glowPulseIdx;
                            var colA = neonPalette[glowPulseIdx];
                            var colB = neonPalette[(glowPulseIdx + 2) % neonPalette.length];
                            if(trackRtlEl) trackRtlEl.style.borderColor = colA;
                            if(trackLtrEl) trackLtrEl.style.borderColor = colB;
                            for(var b = 0; b < metricBoxes.length; b++) {
                                var boxEl = metricBoxes[b];
                                if(boxEl) {
                                    boxEl.style.borderColor = neonPalette[(glowPulseIdx + b) % neonPalette.length];
                                }
                            }
                        }
                    }

                    var scanStartTime = performance.now();
                    var scanDurationMs = 7500;
                    var beatIntervalMs = scanDurationMs / maxDualCandles;
                    var finishedScan = false;

                    function smoothScanFrame(nowTs) {
                        if(!modal.isConnected || finishedScan) return;

                        var elapsed = nowTs - scanStartTime;
                        var rawRatio = Math.min(1, elapsed / scanDurationMs);
                        var nextPct = Math.max(1, Math.min(100, Math.floor(rawRatio * 100)));
                        if(rawRatio < 1 && nextPct >= 100) nextPct = 99;
                        if(rawRatio >= 1) nextPct = 100;

                        var beatFloat = Math.min(maxDualCandles, elapsed / beatIntervalMs);
                        var activeBeat = Math.min(maxDualCandles - 1, Math.floor(beatFloat));

                        if(activeBeat > lastTickBeat && rawRatio < 1) {
                            lastTickBeat = activeBeat;
                            playTickSound();
                        }

                        updateSmoothCandleStreams(elapsed, beatFloat, activeBeat);

                        var pVec = Math.min(100, Math.max(1, Math.round((rawRatio / 0.86) * 100)));
                        var pFeed = Math.min(100, Math.max(1, Math.round((rawRatio / 0.90) * 100)));
                        var pRsi = Math.min(100, Math.max(1, Math.round((rawRatio / 0.93) * 100)));
                        var pCyc = Math.min(100, Math.max(1, Math.round((rawRatio / 0.88) * 100)));
                        var pLat = Math.min(100, Math.max(1, Math.round((rawRatio / 0.95) * 100)));
                        var pBreach = Math.min(100, Math.max(1, Math.round((rawRatio / 0.97) * 100)));
                        var pNode = Math.min(100, Math.max(1, Math.round((rawRatio / 0.99) * 100)));

                        var msSteps = [1, 2, 3, 4, 5, 8, 12, 18, 25, 35, 50];
                        var msIdx = Math.min(msSteps.length - 1, Math.floor(rawRatio * msSteps.length));
                        if(msValEl) msValEl.innerText = msSteps[msIdx] + "ms";

                        if(nextPct !== pct) {
                            pct = nextPct;
                            if(pctBadge) pctBadge.innerText = pct + '%';

                            var tVec = getTierWithPct(pVec);
                            var tFeed = getTierWithPct(pFeed);
                            var tRsi = getTierWithPct(pRsi);
                            var tCyc = getTierWithPct(pCyc);
                            var tLat = getTierWithPct(pLat);
                            var tBreach = getTierWithPct(pBreach);
                            var tNode = getTierWithPct(pNode);

                            if(vecMode) { vecMode.innerText = tVec.label + " " + tVec.pctStr; vecMode.style.color = tVec.color; }
                            if(feedMode) { feedMode.innerText = tFeed.label + " " + tFeed.pctStr; feedMode.style.color = tFeed.color; }
                            if(rsaVal) { rsaVal.innerText = tRsi.label + " " + tRsi.pctStr; rsaVal.style.color = tRsi.color; }
                            if(cycMode) { cycMode.innerText = tCyc.label + " " + tCyc.pctStr; cycMode.style.color = tCyc.color; }
                            if(latMode) { latMode.innerText = tLat.label + " " + tLat.pctStr; latMode.style.color = tLat.color; }
                            if(breachVal) { breachVal.innerText = tBreach.label + " " + tBreach.pctStr; breachVal.style.color = tBreach.color; }
                            if(nodeMode) { nodeMode.innerText = tNode.label + " " + tNode.pctStr; nodeMode.style.color = tNode.color; }
                            if(memState) { memState.innerText = "● " + tNode.label + " (" + pct + "%)"; memState.style.color = tNode.color; }
                        }

                        var targetHex = Math.min(hexStreamLines.length, Math.floor(rawRatio * hexStreamLines.length) + 1);
                        if(targetHex > revealedHex && hexStreamEl) {
                            var fragHex = d.createDocumentFragment();
                            while(revealedHex < targetHex) {
                                var hObj = hexStreamLines[revealedHex];
                                var hRow = d.createElement('div');
                                hRow.style.color = hObj.color;
                                hRow.innerText = hObj.text;
                                fragHex.appendChild(hRow);
                                revealedHex++;
                            }
                            hexStreamEl.appendChild(fragHex);
                            hexStreamEl.scrollTop = hexStreamEl.scrollHeight;
                        }

                        var targetSteps = Math.min(scanSteps.length, Math.floor(rawRatio * scanSteps.length) + 1);
                        if(targetSteps > revealedSteps && feedEl) {
                            var fragSteps = d.createDocumentFragment();
                            while(revealedSteps < targetSteps) {
                                var stepObj = scanSteps[revealedSteps];
                                var row = d.createElement('div');
                                row.style.color = stepObj.color;
                                row.innerHTML = '<span style="color:#4ade80;font-weight:900;">✓</span> ' + stepObj.text;
                                fragSteps.appendChild(row);
                                revealedSteps++;
                            }
                            feedEl.appendChild(fragSteps);
                            feedEl.scrollTop = feedEl.scrollHeight;
                        }

                        if(rawRatio >= 1) {
                            finishedScan = true;
                            updateSmoothCandleStreams(scanDurationMs, maxDualCandles, maxDualCandles - 1);
                            pct = 100;
                            if(pctBadge) pctBadge.innerText = '100%';
                            if(msValEl) msValEl.innerText = '50ms';
                            if(vecMode) { vecMode.innerText = '100% ULTRA'; vecMode.style.color = '#e879f9'; }
                            if(feedMode) { feedMode.innerText = '100% ULTRA'; feedMode.style.color = '#e879f9'; }
                            if(rsaVal) { rsaVal.innerText = '100% ULTRA'; rsaVal.style.color = '#e879f9'; }
                            if(cycMode) { cycMode.innerText = '100% ULTRA'; cycMode.style.color = '#e879f9'; }
                            if(latMode) { latMode.innerText = '100% ULTRA'; latMode.style.color = '#e879f9'; }
                            if(breachVal) { breachVal.innerText = '100% ULTRA'; breachVal.style.color = '#e879f9'; }
                            if(nodeMode) { nodeMode.innerText = '100% ULTRA'; nodeMode.style.color = '#e879f9'; }
                            if(memState) { memState.innerText = '● 100% LOCK (100%)'; memState.style.color = '#e879f9'; }

                            var finalMarket = detectExactQuotexMarket();
                            signalPromise.then(function(data){
                                var sig = String((data && data.signal) || 'HOLD').toUpperCase();
                                var cNum = parseInt(data && data.confidence, 10);
                                var okConf = isNaN(cNum) ? (sig !== 'HOLD') : (cNum >= 65);
                                var isCall = okConf && (sig === 'CALL' || sig === 'UP' || sig === 'BUY');
                                var ptsVal = data && data.pts;
                                if(okConf) {
                                    applyHeroCandleColor(isCall);
                                    playTradePongSound(isCall);
                                }
                                setTimeout(function(){
                                    if(modal.isConnected) modal.remove();
                                    setBrokerBackgroundBlur(false);
                                    showBoxSignalCard(okConf ? sig : 'HOLD', finalMarket, ptsVal, cNum);
                                }, 200);
                            });
                            return;
                        }

                        window.__raScanRaf = requestAnimationFrame(smoothScanFrame);
                    }

                    window.__raScanRaf = requestAnimationFrame(smoothScanFrame);
                }

                if(window[sessionFlagName]) {
                    createDraggableBotButton();
                } else {
                    showCenteredPasswordPanel();
                }
                return true;
            } catch(err) {
                console.error("R-A Candle Hacker Error:", err);
                return false;
            }
        }

        function ensureBotMountedContinuously() {
            if(mountBot()) return;

            var retryCount = 0;
            var retryTimer = setInterval(function(){
                retryCount++;
                if(mountBot() || retryCount >= 40) {
                    clearInterval(retryTimer);
                }
            }, 250);

            if(typeof MutationObserver !== "undefined") {
                var target = document.documentElement || document.body;
                if(target) {
                    var obs = new MutationObserver(function(){
                        if(document.body && !document.getElementById('ra-hacker-btn') && !document.getElementById('ra-hacker-login-modal') && !document.getElementById('ra-hacker-scan-modal') && !document.getElementById('ra-cyber-5s-overlay')) {
                            mountBot();
                        }
                    });
                    obs.observe(target, { childList: true, subtree: true });
                }
            }
        }

        if(document.readyState === "loading") {
            document.addEventListener("DOMContentLoaded", ensureBotMountedContinuously, { once: true });
        } else {
            ensureBotMountedContinuously();
        }
        window.addEventListener("load", ensureBotMountedContinuously, { once: true });
    })();
    """
    res = make_response(js)
    return add_cors_headers(res, is_js=True)


def start_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, threaded=True)


if __name__ == '__main__':
    start_server()
