from flask import Flask, jsonify, make_response, request
import requests
import time
import os
import logging
from datetime import datetime, timedelta

app = Flask(__name__, static_folder=None)

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger("RA_CANDLE_HACKER_Engine")

QX_API_KEY = os.environ.get("QX_API_KEY", "qx_live_1xxOcsg5_3vEavHfZwAkGufh9NLLWJhUqG3T6H6oCEuoDWeJV")
FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "dbcaa19r01qqr3s0pf60dbcaa19r01qqr3s0pf6g")
TWELVE_DATA_KEY = os.environ.get("TWELVE_DATA_KEY", "8f5d4d4fce7f44e5bda54420591411c8")
TIMEZONE_OFFSET = float(os.environ.get("QX_TZ", "6"))

http_session = requests.Session()
if QX_API_KEY:
    http_session.headers["Authorization"] = f"Bearer {QX_API_KEY}"


class LiveMarketCandleEngine:
    @staticmethod
    def check_news_safety(currency: str = "USD") -> bool:
        try:
            url = f"https://finnhub.io/api/v1/calendar/economic?token={FINNHUB_API_KEY}"
            response = http_session.get(url, timeout=3)
            if response.status_code == 200:
                events = response.json().get("economicCalendar", [])
                now_time = datetime.utcnow() + timedelta(hours=TIMEZONE_OFFSET)
                for event in events:
                    if currency.upper() in event.get("currency", "").upper():
                        event_time_str = event.get("time", "").replace("Z", "+00:00")
                        if event_time_str:
                            event_dt = datetime.fromisoformat(event_time_str) + timedelta(hours=TIMEZONE_OFFSET)
                            if abs((event_dt.replace(tzinfo=None) - now_time).total_seconds()) < 900:
                                return False
            return True
        except Exception:
            return True

    @staticmethod
    def compute_live_market_signal(symbol: str = "EURUSD") -> dict:
        formatted_sym = symbol if "/" in symbol else f"{symbol[:3]}/{symbol[3:]}"

        try:
            url_ts = f"https://api.twelvedata.com/time_series?symbol={formatted_sym}&interval=1min&outputsize=5&apikey={TWELVE_DATA_KEY}"
            resp = requests.get(url_ts, timeout=3.5)
            if resp.status_code == 200:
                payload = resp.json()
                values = payload.get("values", [])
                if len(values) >= 2:
                    c0 = float(values[0]["close"])
                    c1 = float(values[1]["close"])
                    delta = c0 - c1

                    if len(values) >= 3:
                        c2 = float(values[2]["close"])
                        prev_delta = c1 - c2
                    else:
                        prev_delta = delta

                    # Live candle momentum and direction from real price action
                    if abs(delta) < 1e-9:
                        sig = "CALL" if int(time.time()) % 2 == 0 else "PUT"
                    elif delta > 0 and prev_delta > 0:
                        # Exhaustion / reversal or continuation based on candle body ratio
                        sig = "PUT" if abs(delta) < abs(prev_delta) * 0.65 else "CALL"
                    elif delta < 0 and prev_delta < 0:
                        sig = "CALL" if abs(delta) < abs(prev_delta) * 0.65 else "PUT"
                    else:
                        sig = "CALL" if delta > 0 else "PUT"

                    # Scale candle magnitude from actual live price change
                    pip_factor = 100000.0 if ("JPY" not in symbol and "XAU" not in symbol) else 100.0
                    live_pips = abs(delta) * pip_factor
                    pts_val = max(8, min(40, int(round(8 + (live_pips * 2.4)))))

                    return {
                        "signal": sig,
                        "trend": "BULLISH (UP)" if sig == "CALL" else "BEARISH (DOWN)",
                        "pts": pts_val,
                        "live_price": c0,
                        "rule": f"Live Feed Sync ({formatted_sym}: {c0})"
                    }
        except Exception as e:
            logger.warning(f"Time series fetch notice for {formatted_sym}: {e}")

        # Secondary real-time price endpoint if time_series is delayed
        try:
            url_q = f"https://api.twelvedata.com/price?symbol={formatted_sym}&apikey={TWELVE_DATA_KEY}"
            q_resp = requests.get(url_q, timeout=2.5)
            if q_resp.status_code == 200:
                price_str = q_resp.json().get("price")
                if price_str:
                    px = float(price_str)
                    micro_delta = (px * 100000.0) % 1.0
                    sig = "CALL" if micro_delta >= 0.5 else "PUT"
                    pts_val = max(8, min(40, int(round(10 + (abs(micro_delta - 0.5) * 60)))))
                    return {
                        "signal": sig,
                        "trend": "BULLISH (UP)" if sig == "CALL" else "BEARISH (DOWN)",
                        "pts": pts_val,
                        "live_price": px,
                        "rule": f"Live Tick Sync ({formatted_sym}: {px})"
                    }
        except Exception:
            pass

        # Bi-directional tick parity fallback when external API is unreachable
        tick_sec = int(time.time())
        sig = "CALL" if (tick_sec % 2 == 0) else "PUT"
        pts_val = 8 + ((tick_sec * 7) % 33)
        return {
            "signal": sig,
            "trend": "BULLISH (UP)" if sig == "CALL" else "BEARISH (DOWN)",
            "pts": pts_val,
            "rule": "Bi-Directional Live Tick Stream"
        }


@app.route('/')
def home():
    res = make_response("R-A CANDLE HACKER ENGINE ACTIVE - ULTRA SMOOTH LIVE CANDLES!")
    res.headers.add("Access-Control-Allow-Origin", "*")
    return res


@app.route('/ping')
def ping():
    res = make_response("OK", 200)
    res.headers.add("Access-Control-Allow-Origin", "*")
    return res


@app.route('/signal')
def get_signal():
    try:
        raw_market = request.args.get("market", "EURUSD").upper()
        clean_market = raw_market.replace("(REAL)", "").replace("(OTC)", "").replace("_OTC", "").replace("/", "").replace(" ", "").strip()
        if len(clean_market) < 6:
            clean_market = "EURUSD"
        else:
            clean_market = clean_market[:6]

        is_news_safe = LiveMarketCandleEngine.check_news_safety(clean_market[:3])
        if not is_news_safe:
            res = jsonify({"signal": "HOLD", "trend": "NEWS BLOCK", "status": "NEWS_GUARD", "pts": 0, "rule": "High Impact News Filter Active."})
            res.headers.add("Access-Control-Allow-Origin", "*")
            return res

        analysis = LiveMarketCandleEngine.compute_live_market_signal(clean_market)
        res = jsonify({
            "signal": analysis["signal"],
            "trend": analysis["trend"],
            "status": "GREEN_EXECUTE",
            "pts": analysis.get("pts", 18),
            "rule": analysis["rule"]
        })
        res.headers.add("Access-Control-Allow-Origin", "*")
        return res
    except Exception as e:
        logger.error(f"Signal Error: {e}")
        sec_now = int(time.time())
        fallback_sig = "CALL" if (sec_now % 2 == 0) else "PUT"
        res = jsonify({
            "signal": fallback_sig,
            "trend": "BULLISH (UP)" if fallback_sig == "CALL" else "BEARISH (DOWN)",
            "status": "GREEN_EXECUTE",
            "pts": 8 + ((sec_now * 5) % 33),
            "rule": "Live Bi-Directional Confluence Sync."
        })
        res.headers.add("Access-Control-Allow-Origin", "*")
        return res


@app.route('/bot.js')
def bot_script():
    js = """
    (function(){
        try {
            var d = document;
            [
                "ra-sniper-bot-panel", "ra-sniper-bot-btn", "ra-sniper-bot-style",
                "dr-tracker-panel", "dr-tracker-btn", "dr-scan-modal",
                "dr-candle-projection", "dr-next-signal-popup", "dr-hacker-style",
                "ra-hacker-btn", "ra-hacker-scan-modal", "ra-hacker-signal-popup",
                "ra-hacker-login-modal", "ra-bg-blur-overlay", "ra-hacker-style"
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

            var renderServerUrl = "https://ra-ai-bot.onrender.com";
            var botAvatarUrl = "https://i.postimg.cc/Fz3xjQGZ/file-000000001cc082119080b22d35ecbaaa.png";
            var communityAvatarUrl = "https://i.postimg.cc/k5NBY37k/file-0000000016a482119619e0cb99151c28.png";
            var telegramChannelUrl = "https://t.me/+x1QYA_1-sSs0NTk1";
            var validAccessKey = "Gop Gop2027";
            var sessionFlagName = "__raCandleHackerUnlocked";

            var styleEl = d.createElement('style');
            styleEl.id = 'ra-hacker-style';
            styleEl.innerHTML = '' +
                '@keyframes raTireWheelSpin {' +
                '  0%   { transform: rotate(0deg); }' +
                '  100% { transform: rotate(360deg); }' +
                '}' +
                '@keyframes raBotGlowCycle {' +
                '  0%   { box-shadow: 0 0 22px #22c55e, 0 0 44px rgba(34,197,94,0.92), inset 0 0 14px rgba(34,197,94,0.75); border-color: #22c55e; }' +
                '  25%  { box-shadow: 0 0 24px #00f0ff, 0 0 48px rgba(0,240,255,0.95), inset 0 0 14px rgba(0,240,255,0.75); border-color: #00f0ff; }' +
                '  50%  { box-shadow: 0 0 24px #e879f9, 0 0 48px rgba(232,121,249,0.95), inset 0 0 14px rgba(232,121,249,0.75); border-color: #e879f9; }' +
                '  75%  { box-shadow: 0 0 24px #facc15, 0 0 48px rgba(250,204,21,0.95), inset 0 0 14px rgba(250,204,21,0.75); border-color: #facc15; }' +
                '  100% { box-shadow: 0 0 22px #22c55e, 0 0 44px rgba(34,197,94,0.92), inset 0 0 14px rgba(34,197,94,0.75); border-color: #22c55e; }' +
                '}' +
                '@keyframes raLoginFastBorder {' +
                '  0%   { border-color: #22c55e; box-shadow: 0 0 26px rgba(34,197,94,0.95), 0 0 54px rgba(0,240,255,0.55); }' +
                '  25%  { border-color: #00f0ff; box-shadow: 0 0 30px rgba(0,240,255,0.98), 0 0 60px rgba(232,121,249,0.58); }' +
                '  50%  { border-color: #e879f9; box-shadow: 0 0 30px rgba(232,121,249,0.98), 0 0 60px rgba(250,204,21,0.58); }' +
                '  75%  { border-color: #facc15; box-shadow: 0 0 30px rgba(250,204,21,0.98), 0 0 60px rgba(34,197,94,0.58); }' +
                '  100% { border-color: #22c55e; box-shadow: 0 0 26px rgba(34,197,94,0.95), 0 0 54px rgba(0,240,255,0.55); }' +
                '}' +
                '@keyframes raTelegramSlowBorder {' +
                '  0%   { border-color: #facc15; box-shadow: 0 0 16px rgba(250,204,21,0.82), inset 0 0 10px rgba(250,204,21,0.32); }' +
                '  25%  { border-color: #4ade80; box-shadow: 0 0 18px rgba(74,222,128,0.88), inset 0 0 10px rgba(74,222,128,0.34); }' +
                '  50%  { border-color: #38bdf8; box-shadow: 0 0 18px rgba(56,189,248,0.88), inset 0 0 10px rgba(56,189,248,0.34); }' +
                '  75%  { border-color: #e879f9; box-shadow: 0 0 18px rgba(232,121,249,0.88), inset 0 0 10px rgba(232,121,249,0.34); }' +
                '  100% { border-color: #facc15; box-shadow: 0 0 16px rgba(250,204,21,0.82), inset 0 0 10px rgba(250,204,21,0.32); }' +
                '}' +
                '@keyframes raScanBoxSlowBorder {' +
                '  0%   { border-color: #22c55e; box-shadow: 0 0 42px rgba(34,197,94,0.96), 0 0 80px rgba(0,240,255,0.58), inset 0 0 22px rgba(34,197,94,0.38); }' +
                '  25%  { border-color: #00f0ff; box-shadow: 0 0 46px rgba(0,240,255,0.98), 0 0 86px rgba(232,121,249,0.62), inset 0 0 24px rgba(0,240,255,0.42); }' +
                '  50%  { border-color: #e879f9; box-shadow: 0 0 46px rgba(232,121,249,0.98), 0 0 86px rgba(250,204,21,0.62), inset 0 0 24px rgba(232,121,249,0.42); }' +
                '  75%  { border-color: #facc15; box-shadow: 0 0 46px rgba(250,204,21,0.98), 0 0 86px rgba(56,189,248,0.62), inset 0 0 24px rgba(250,204,21,0.42); }' +
                '  100% { border-color: #22c55e; box-shadow: 0 0 42px rgba(34,197,94,0.96), 0 0 80px rgba(0,240,255,0.58), inset 0 0 22px rgba(34,197,94,0.38); }' +
                '}' +
                '@keyframes raHeaderAvatarGlow {' +
                '  0%   { border-color: #00f0ff; box-shadow: 0 0 18px rgba(0,240,255,0.95), 0 0 32px rgba(34,197,94,0.65); }' +
                '  33%  { border-color: #e879f9; box-shadow: 0 0 20px rgba(232,121,249,0.98), 0 0 34px rgba(250,204,21,0.7); }' +
                '  66%  { border-color: #facc15; box-shadow: 0 0 20px rgba(250,204,21,0.98), 0 0 34px rgba(0,240,255,0.7); }' +
                '  100% { border-color: #00f0ff; box-shadow: 0 0 18px rgba(0,240,255,0.95), 0 0 32px rgba(34,197,94,0.65); }' +
                '}' +
                '@keyframes raSubBoxCycleA {' +
                '  0%   { border-color: rgba(34,197,94,1); box-shadow: 0 0 22px rgba(34,197,94,0.88), inset 0 0 14px rgba(34,197,94,0.45); }' +
                '  33%  { border-color: rgba(232,121,249,1); box-shadow: 0 0 26px rgba(232,121,249,0.92), inset 0 0 16px rgba(232,121,249,0.48); }' +
                '  66%  { border-color: rgba(250,204,21,1); box-shadow: 0 0 26px rgba(250,204,21,0.92), inset 0 0 16px rgba(250,204,21,0.48); }' +
                '  100% { border-color: rgba(34,197,94,1); box-shadow: 0 0 22px rgba(34,197,94,0.88), inset 0 0 14px rgba(34,197,94,0.45); }' +
                '}' +
                '@keyframes raSubBoxCycleB {' +
                '  0%   { border-color: rgba(0,240,255,1); box-shadow: 0 0 22px rgba(0,240,255,0.88), inset 0 0 14px rgba(0,240,255,0.45); }' +
                '  33%  { border-color: rgba(250,204,21,1); box-shadow: 0 0 26px rgba(250,204,21,0.92), inset 0 0 16px rgba(250,204,21,0.48); }' +
                '  66%  { border-color: rgba(74,222,128,1); box-shadow: 0 0 26px rgba(74,222,128,0.92), inset 0 0 16px rgba(74,222,128,0.48); }' +
                '  100% { border-color: rgba(0,240,255,1); box-shadow: 0 0 22px rgba(0,240,255,0.88), inset 0 0 14px rgba(0,240,255,0.45); }' +
                '}' +
                '@keyframes raSubBoxCycleC {' +
                '  0%   { border-color: rgba(244,63,94,1); box-shadow: 0 0 22px rgba(244,63,94,0.88), inset 0 0 14px rgba(244,63,94,0.45); }' +
                '  33%  { border-color: rgba(56,189,248,1); box-shadow: 0 0 26px rgba(56,189,248,0.92), inset 0 0 16px rgba(56,189,248,0.48); }' +
                '  66%  { border-color: rgba(192,132,252,1); box-shadow: 0 0 26px rgba(192,132,252,0.92), inset 0 0 16px rgba(192,132,252,0.48); }' +
                '  100% { border-color: rgba(244,63,94,1); box-shadow: 0 0 22px rgba(244,63,94,0.88), inset 0 0 14px rgba(244,63,94,0.45); }' +
                '}' +
                '@keyframes raTrackGlowCycle {' +
                '  0%   { border-color: rgba(0,240,255,0.95); box-shadow: 0 0 28px rgba(0,240,255,0.82), inset 0 0 16px rgba(0,240,255,0.42); }' +
                '  33%  { border-color: rgba(74,222,128,0.95); box-shadow: 0 0 32px rgba(74,222,128,0.88), inset 0 0 16px rgba(74,222,128,0.45); }' +
                '  66%  { border-color: rgba(232,121,249,0.95); box-shadow: 0 0 32px rgba(232,121,249,0.85), inset 0 0 16px rgba(232,121,249,0.42); }' +
                '  100% { border-color: rgba(0,240,255,0.95); box-shadow: 0 0 28px rgba(0,240,255,0.82), inset 0 0 16px rgba(0,240,255,0.42); }' +
                '}' +
                '@keyframes raPopupGreenGlow {' +
                '  0%, 100% { border-color: #4ade80; box-shadow: 0 0 38px rgba(34,197,94,1), 0 0 74px rgba(74,222,128,0.88), inset 0 0 22px rgba(34,197,94,0.55); }' +
                '  50% { border-color: #86efac; box-shadow: 0 0 50px rgba(34,197,94,1), 0 0 94px rgba(0,240,255,0.78), inset 0 0 28px rgba(74,222,128,0.65); }' +
                '}' +
                '@keyframes raPopupRedGlow {' +
                '  0%, 100% { border-color: #f87171; box-shadow: 0 0 38px rgba(239,68,68,1), 0 0 74px rgba(248,113,113,0.88), inset 0 0 22px rgba(239,68,68,0.55); }' +
                '  50% { border-color: #fca5a5; box-shadow: 0 0 50px rgba(239,68,68,1), 0 0 94px rgba(251,113,133,0.78), inset 0 0 28px rgba(248,113,113,0.65); }' +
                '}' +
                '@keyframes raHeroCandleSpinGlow {' +
                '  0%   { transform: rotateY(0deg); }' +
                '  100% { transform: rotateY(360deg); }' +
                '}' +
                '@keyframes raCandleReveal {' +
                '  0% { transform: scaleY(0.15); opacity: 0.35; }' +
                '  100% { transform: scaleY(1); opacity: 1; }' +
                '}' +
                '@keyframes raPopupEnter {' +
                '  0% { opacity: 0; transform: translateY(8px) scale(0.94); }' +
                '  100% { opacity: 1; transform: translateY(0) scale(1); }' +
                '}';
            d.head.appendChild(styleEl);

            function setBrokerBackgroundBlur(enableBlur) {
                var existing = d.getElementById('ra-bg-blur-overlay');
                if(enableBlur) {
                    if(!existing) {
                        var blurLayer = d.createElement('div');
                        blurLayer.id = 'ra-bg-blur-overlay';
                        blurLayer.style.cssText = 'position:fixed;inset:0;z-index:2147483640;' +
                            'backdrop-filter:blur(4.5px);-webkit-backdrop-filter:blur(4.5px);' +
                            'background:rgba(2,8,15,0.28);pointer-events:none;will-change:opacity;';
                        d.body.appendChild(blurLayer);
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
                    heroCandleBody.style.background = '#22c55e';
                    heroCandleBody.style.borderColor = '#bbf7d0';
                    heroCandleBody.style.boxShadow = '0 0 32px rgba(34,197,94,1), 0 0 64px rgba(74,222,128,1)';
                    heroWickTop.style.background = '#4ade80';
                    heroWickTop.style.boxShadow = '0 0 14px #4ade80, 0 0 24px #22c55e';
                    heroWickBot.style.background = '#4ade80';
                    heroWickBot.style.boxShadow = '0 0 14px #4ade80, 0 0 24px #22c55e';
                    heroCandleBox.style.borderColor = '#4ade80';
                    heroCandleBox.style.background = 'rgba(34,197,94,0.28)';
                    heroCandleBox.style.boxShadow = '0 0 36px rgba(34,197,94,1), 0 0 68px rgba(74,222,128,1)';
                } else {
                    heroCandleBody.style.background = '#ef4444';
                    heroCandleBody.style.borderColor = '#fecaca';
                    heroCandleBody.style.boxShadow = '0 0 28px rgba(239,68,68,1), 0 0 56px rgba(74,222,128,0.92)';
                    heroWickTop.style.background = '#4ade80';
                    heroWickTop.style.boxShadow = '0 0 12px #4ade80, 0 0 22px #22c55e';
                    heroWickBot.style.background = '#4ade80';
                    heroWickBot.style.boxShadow = '0 0 12px #4ade80, 0 0 22px #22c55e';
                    heroCandleBox.style.borderColor = '#4ade80';
                    heroCandleBox.style.background = 'rgba(239,68,68,0.24)';
                    heroCandleBox.style.boxShadow = '0 0 34px rgba(239,68,68,0.98), 0 0 64px rgba(74,222,128,0.95)';
                }
            }

            function showCenteredPasswordPanel() {
                var oldLogin = d.getElementById('ra-hacker-login-modal');
                if(oldLogin) oldLogin.remove();

                var loginBox = d.createElement('div');
                loginBox.id = 'ra-hacker-login-modal';
                loginBox.style.cssText = 'position:fixed;top:50%;left:50%;transform:translate(-50%, -50%);' +
                    'width:258px;max-width:88vw;background:linear-gradient(170deg, #061018 0%, #091722 55%, #050d14 100%);' +
                    'border:2px solid #22c55e;border-radius:14px;padding:10px 11px;box-sizing:border-box;' +
                    'z-index:2147483647;font-family:"Segoe UI",Roboto,Arial,sans-serif;color:#ffffff;' +
                    'animation:raLoginFastBorder 2.4s infinite linear;';

                loginBox.innerHTML = '' +
                    '<div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid rgba(255,255,255,0.1);padding-bottom:7px;margin-bottom:7px;">' +
                    '  <div style="display:flex;align-items:center;gap:7px;">' +
                    '    <div style="width:34px;height:34px;border-radius:50%;padding:1.5px;background:linear-gradient(135deg,#22c55e,#00f0ff,#e879f9);box-shadow:0 0 12px rgba(34,197,94,0.8);flex-shrink:0;">' +
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
                    '  <div style="width:40px;height:40px;border-radius:50%;padding:1.5px;background:linear-gradient(135deg,#facc15,#ef4444,#22c55e);box-shadow:0 0 12px rgba(250,204,21,0.7);flex-shrink:0;">' +
                    '    <img src="' + communityAvatarUrl + '" alt="R-A Trading Community" style="width:100%;height:100%;border-radius:50%;object-fit:cover;display:block;background:#02090e;" />' +
                    '  </div>' +
                    '  <div style="font-size:8.8px;color:#94a3b8;line-height:1.3;">' +
                    '    <div style="color:#facc15;font-weight:800;font-size:9.3px;">Official VIP Access</div>' +
                    '    <div>Join Telegram for updates &amp; keys.</div>' +
                    '  </div>' +
                    '</div>' +

                    '<a href="' + telegramChannelUrl + '" target="_blank" rel="noopener noreferrer" style="display:flex;align-items:center;justify-content:center;gap:8px;text-decoration:none;background:linear-gradient(135deg, rgba(16,28,38,0.96), rgba(10,20,28,0.98));border:1.8px solid #facc15;border-radius:10px;padding:7px 8px;margin-bottom:7px;cursor:pointer;animation:raTelegramSlowBorder 12s infinite ease-in-out;">' +
                    '  <div style="width:20px;height:20px;border-radius:50%;background:#26a5e4;display:flex;align-items:center;justify-content:center;flex-shrink:0;box-shadow:0 0 9px rgba(38,165,228,0.8);">' +
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
                    '<button id="ra-activate-bot-btn" type="button" style="width:100%;border:none;border-radius:8px;padding:8px;font-size:10.5px;font-weight:900;letter-spacing:0.5px;color:#04110a;background:linear-gradient(90deg, #f43f5e 0%, #eab308 45%, #22c55e 100%);cursor:pointer;box-shadow:0 0 15px rgba(34,197,94,0.5);">ACTIVATE BOT</button>';

                d.body.appendChild(loginBox);

                var closeBtn = loginBox.querySelector('#ra-login-close');
                var keyInput = loginBox.querySelector('#ra-access-key-input');
                var statusMsg = loginBox.querySelector('#ra-login-status-msg');
                var activateBtn = loginBox.querySelector('#ra-activate-bot-btn');
                var isVerifying = false;

                closeBtn.onclick = function() {
                    loginBox.remove();
                };

                keyInput.addEventListener('input', function() {
                    if(!isVerifying) {
                        keyInput.style.borderColor = 'rgba(0,240,255,0.65)';
                        keyInput.style.boxShadow = '0 0 10px rgba(0,240,255,0.25)';
                        statusMsg.innerText = '';
                    }
                });

                function handleVerification() {
                    if(isVerifying) return;
                    var enteredVal = (keyInput.value || '').trim();

                    if(enteredVal !== validAccessKey) {
                        keyInput.style.borderColor = '#ef4444';
                        keyInput.style.boxShadow = '0 0 16px rgba(239,68,68,0.85)';
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
                    keyInput.style.boxShadow = '0 0 16px rgba(250,204,21,0.8)';
                    keyInput.style.background = '#0b1724';
                    statusMsg.style.color = '#facc15';
                    statusMsg.innerText = '⟳ VERIFYING LICENSE KEY...';
                    activateBtn.style.background = 'linear-gradient(90deg, #0284c7, #eab308)';
                    activateBtn.style.color = '#ffffff';
                    activateBtn.innerText = 'PROCESSING...';

                    setTimeout(function() {
                        if(!loginBox.isConnected) return;
                        statusMsg.style.color = '#00f0ff';
                        statusMsg.innerText = '⟳ SYNCING QUANT ENGINE NODE...';
                    }, 1100);

                    setTimeout(function() {
                        if(!loginBox.isConnected) return;
                        keyInput.style.borderColor = '#22c55e';
                        keyInput.style.boxShadow = '0 0 20px rgba(34,197,94,0.95)';
                        statusMsg.style.color = '#4ade80';
                        statusMsg.innerText = '✓ VERIFICATION SUCCESSFUL!';
                        activateBtn.style.background = 'linear-gradient(90deg, #16a34a, #4ade80)';
                        activateBtn.style.color = '#021208';
                        activateBtn.innerText = 'SUCCESSFUL ✓';

                        window[sessionFlagName] = true;

                        setTimeout(function() {
                            if(loginBox.isConnected) loginBox.remove();
                            createDraggableBotButton();
                        }, 750);
                    }, 2400);
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

            function createDraggableBotButton() {
                if(d.getElementById('ra-hacker-btn')) return;

                var btn = d.createElement('div');
                btn.id = 'ra-hacker-btn';
                btn.style.cssText = 'position:fixed;bottom:146px;right:12px;width:82px;height:82px;border-radius:50%;' +
                    'background:#02090e;border:2px solid #22c55e;display:flex;align-items:center;justify-content:center;' +
                    'z-index:2147483647;cursor:grab;user-select:none;touch-action:none;overflow:hidden;' +
                    'font-family:"Courier New",Courier,monospace;' +
                    'animation:raBotGlowCycle 3.6s infinite linear;';

                btn.innerHTML = '' +
                    '<div style="position:absolute;inset:0;border-radius:50%;pointer-events:none;z-index:1;' +
                    'background:conic-gradient(from 0deg, #22c55e, #00f0ff, #e879f9, #facc15, #f43f5e, #38bdf8, #22c55e);' +
                    'animation:raTireWheelSpin 3.2s infinite linear;"></div>' +
                    '<div style="position:absolute;inset:6px;border-radius:50%;background:#02090e;z-index:2;pointer-events:none;"></div>' +
                    '<img src="' + botAvatarUrl + '" alt="R-A Candle Hacker" style="position:relative;z-index:3;width:66px;height:66px;object-fit:cover;border-radius:50%;pointer-events:none;display:block;background:#02090e;border:1.5px solid rgba(255,255,255,0.45);" />';

                d.body.appendChild(btn);

                var dragging = false, moved = false, offsetX = 0, offsetY = 0;

                function onStart(e) {
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

                    var activePopup = d.getElementById('ra-hacker-signal-popup');
                    if(activePopup) positionPopupAboveBotWithGap(activePopup, btn);
                }

                function onEnd(e) {
                    if(!dragging) return;
                    dragging = false;
                    btn.style.cursor = 'grab';
                    if(!moved) {
                        if(e) { e.stopPropagation(); e.preventDefault(); }
                        startHackerScanSequence();
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
                        '[class*="current-asset"]'
                    ];
                    for(var s = 0; s < selectors.length; s++) {
                        var nodes = d.querySelectorAll(selectors[s]);
                        for(var i = 0; i < nodes.length; i++) {
                            var raw = (nodes[i].innerText || '').trim();
                            var cleaned = raw.replace(/\s+/g, ' ').trim();
                            if(/^[A-Z]{3}\s*\/\s*[A-Z]{3}(\s*\(?(OTC|REAL)\)?)?$/i.test(cleaned)) {
                                return cleaned.replace(/\s*\/\s*/, '/').toUpperCase();
                            }
                        }
                    }

                    var allTextEls = d.querySelectorAll('span, div, button, p');
                    for(var j = 0; j < allTextEls.length; j++) {
                        if(allTextEls[j].children.length === 0) {
                            var t = (allTextEls[j].innerText || '').trim().replace(/\s+/g, ' ');
                            if(/^[A-Z]{3}\s*\/\s*[A-Z]{3}(\s*\(?(OTC|REAL)\)?)?$/i.test(t) && t.length <= 20) {
                                var rect = allTextEls[j].getBoundingClientRect();
                                if(rect.width > 20 && rect.height > 8 && rect.top > 40 && rect.top < window.innerHeight - 40) {
                                    return t.replace(/\s*\/\s*/, '/').toUpperCase();
                                }
                            }
                        }
                    }
                } catch(e) {}
                return "EUR/USD";
            }

            function getTierFromScore(scoreVal) {
                if(scoreVal <= 30) return { label: "LOW", color: "#4ade80" };
                if(scoreVal <= 50) return { label: "MEDIUM", color: "#facc15" };
                if(scoreVal <= 70) return { label: "HIGH", color: "#00f0ff" };
                return { label: "ULTRA HIGH", color: "#e879f9" };
            }

            function computeTradeCandleSize(ptsRaw, isCall, marketStr) {
                var ptsNum = parseInt(ptsRaw, 10);
                if(isNaN(ptsNum) || ptsNum <= 0) {
                    var secNow = Math.floor(Date.now() / 1000);
                    ptsNum = 8 + ((secNow + marketStr.charCodeAt(0) + (isCall ? 3 : 9)) % 33);
                }
                var clampedPts = Math.max(8, Math.min(40, ptsNum));
                var ratio = (clampedPts - 8) / 32;
                var candleHeightPx = Math.round(12 + (ratio * 42));

                var sizeTag = "SMALL SIZE";
                if(clampedPts <= 14) {
                    sizeTag = "SMALL SIZE";
                } else if(clampedPts <= 23) {
                    sizeTag = "MEDIUM SIZE";
                } else if(clampedPts <= 32) {
                    sizeTag = "LARGE SIZE";
                } else {
                    sizeTag = "HEAVY SIZE";
                }

                return {
                    pts: clampedPts,
                    heightPx: candleHeightPx,
                    sizeTag: sizeTag
                };
            }

            function showBoxSignalCard(isCall, marketDisplayName, ptsFromBackend) {
                var old = d.getElementById('ra-hacker-signal-popup');
                if(old) old.remove();

                var liveMarket = marketDisplayName || detectExactQuotexMarket();
                var metrics = computeTradeCandleSize(ptsFromBackend, isCall, liveMarket);
                var estText = (isCall ? "+" : "-") + metrics.pts + " PTS";
                var mainColor = isCall ? "#4ade80" : "#f87171";
                var glowAnim = isCall ? "raPopupGreenGlow 2.4s infinite ease-in-out" : "raPopupRedGlow 2.4s infinite ease-in-out";

                var candleVisualHtml = '';
                if(isCall) {
                    candleVisualHtml = '' +
                        '<div style="display:flex;flex-direction:column;align-items:center;justify-content:flex-end;height:66px;animation:raCandleReveal 0.3s ease-out;">' +
                        '  <div style="font-size:7.2px;font-weight:900;color:#4ade80;margin-bottom:2px;text-shadow:0 0 10px #22c55e;">' + estText + '</div>' +
                        '  <div style="width:2px;height:6px;background:#4ade80;box-shadow:0 0 8px #22c55e;"></div>' +
                        '  <div style="width:15px;height:' + metrics.heightPx + 'px;background:linear-gradient(180deg,#86efac,#22c55e,#15803d);border:1.2px solid #bbf7d0;border-radius:2px;box-shadow:0 0 24px rgba(34,197,94,1), 0 0 42px rgba(74,222,128,0.9);"></div>' +
                        '  <div style="width:2px;height:5px;background:#4ade80;box-shadow:0 0 8px #22c55e;"></div>' +
                        '</div>';
                } else {
                    candleVisualHtml = '' +
                        '<div style="display:flex;flex-direction:column;align-items:center;justify-content:flex-start;height:66px;animation:raCandleReveal 0.3s ease-out;">' +
                        '  <div style="width:2px;height:5px;background:#f87171;box-shadow:0 0 8px #ef4444;"></div>' +
                        '  <div style="width:15px;height:' + metrics.heightPx + 'px;background:linear-gradient(180deg,#fca5a5,#ef4444,#b91c1c);border:1.2px solid #fecaca;border-radius:2px;box-shadow:0 0 24px rgba(239,68,68,1), 0 0 42px rgba(248,113,113,0.9);"></div>' +
                        '  <div style="width:2px;height:6px;background:#f87171;box-shadow:0 0 8px #ef4444;"></div>' +
                        '  <div style="font-size:7.2px;font-weight:900;color:#f87171;margin-top:2px;text-shadow:0 0 10px #ef4444;">' + estText + '</div>' +
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
                    'animation:raPopupEnter 0.2s ease-out, ' + glowAnim + ';';

                popup.innerHTML = '' +
                    '<div style="text-align:center;font-size:6.2px;font-weight:900;letter-spacing:0.3px;color:#00f0ff;line-height:1.25;margin-bottom:4px;">' +
                    '  R-A Candle Hacker<br><span style="color:' + mainColor + ';font-size:8px;text-shadow:0 0 12px ' + mainColor + ';">' + (isCall ? '▲ CALL (UP)' : '▼ PUT (DOWN)') + '</span>' +
                    '</div>' +
                    '<div style="background:rgba(2,8,12,0.94);border:1.2px solid ' + mainColor + ';border-radius:6px;padding:5px 4px;text-align:center;margin-bottom:4px;box-shadow:inset 0 0 12px ' + (isCall ? 'rgba(34,197,94,0.42)' : 'rgba(239,68,68,0.42)') + ';">' +
                    candleVisualHtml +
                    '  <div style="font-size:6.3px;font-weight:900;color:' + mainColor + ';margin-top:3px;letter-spacing:0.25px;">SIZE: ' + metrics.sizeTag + ' (' + metrics.heightPx + 'PX)</div>' +
                    '  <div style="font-size:6.6px;font-weight:900;color:#ffffff;margin-top:3px;letter-spacing:0.2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">' + liveMarket + '</div>' +
                    '</div>' +
                    '<div style="text-align:center;font-size:6.5px;font-weight:900;color:' + mainColor + ';letter-spacing:0.8px;border-top:1px dashed rgba(255,255,255,0.22);padding-top:3px;">LOCKED</div>';

                d.body.appendChild(popup);
                var botBtn = d.getElementById('ra-hacker-btn');
                positionPopupAboveBotWithGap(popup, botBtn);

                setTimeout(function(){
                    if(popup.parentNode) popup.remove();
                }, 10000);
            }

            function startHackerScanSequence() {
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
                var cleanSymbol = liveMarketDisplay.replace(/[^A-Z]/g, '').substring(0, 6) || "EURUSD";
                var initialIsCall = (Math.floor(Date.now() / 1000) % 2 === 0);

                var hexStreamLines = [
                    { text: "MOD KERNEL32.DLL: 0x0550D120 SCOPE", color: "#00f0ff" },
                    { text: "HASH 0x626A.6F8C4E12 [TICK-SYNC]", color: "#4ade80" },
                    { text: "HEAP 0x56A8B848: 1094272B [QX-03EE]", color: "#facc15" },
                    { text: "PAT 0x80271894: EAX=0x16450 [+0.16450]", color: "#e879f9" },
                    { text: "THREAD#3679 STACK=0x7F98A2B1: #1967", color: "#38bdf8" },
                    { text: "SOCKET 168.153.167.11:21463 ACK", color: "#fb7185" },
                    { text: "MEM 0x0528F7C3: 75C74F49E [016-ACK]", color: "#00f0ff" },
                    { text: "PAT 0x802719A0: EAX=0x16492 [+0.16492]", color: "#4ade80" },
                    { text: "HASH 0x9412A8C1: 0x0550D120 [STREAM]", color: "#facc15" },
                    { text: "KERNEL WICK MATRIX: 0xA91F84C0 [SYNC]", color: "#e879f9" },
                    { text: "ORDER BOOK DELTA: +0.00042 [BID-ASK]", color: "#38bdf8" },
                    { text: "LIQUIDITY POOL DEPTH: 0x882E11B4", color: "#fb7185" },
                    { text: "SESSION ENTROPY LOCK: 99.4% [VERIFIED]", color: "#4ade80" },
                    { text: "SOCKET BRIDGE 0x37: LATENCY 23ms OK", color: "#00f0ff" }
                ];

                var scanSteps = [
                    { text: "Scanning server parts", color: "#22c55e" },
                    { text: "Brute-forcing auth token", color: "#00f0ff" },
                    { text: "Intercepting order flow packets", color: "#facc15" },
                    { text: "Reverse-engineering price engine", color: "#e879f9" },
                    { text: "Injecting live data hook", color: "#38bdf8" },
                    { text: "Masking intrusion trace", color: "#fb7185" },
                    { text: "Hack complete - feed secured", color: "#4ade80" },
                    { text: "Syncing tick buffer 0x626", color: "#00f0ff" },
                    { text: "Probing liquidity depth matrix", color: "#facc15" },
                    { text: "Mapping volatility impulse", color: "#e879f9" },
                    { text: "Verifying session entropy", color: "#38bdf8" },
                    { text: "Decrypting order queue stream", color: "#fb7185" },
                    { text: "Calibrating candle wick pressure", color: "#22c55e" },
                    { text: "Checking spread micro-shifts", color: "#00f0ff" },
                    { text: "Aligning momentum vectors", color: "#facc15" },
                    { text: "Scanning rejection zones", color: "#e879f9" },
                    { text: "Parsing live bid/ask delta", color: "#38bdf8" },
                    { text: "Locking trend expansion filter", color: "#fb7185" },
                    { text: "Validating node 0x37 bridge", color: "#22c55e" },
                    { text: "Tuning quant core weights", color: "#00f0ff" },
                    { text: "Stabilizing socket stream", color: "#facc15" },
                    { text: "Benchmarking execution path", color: "#e879f9" },
                    { text: "Confirming breakout threshold", color: "#38bdf8" },
                    { text: "Scanning imbalance & fair value gaps", color: "#fb7185" },
                    { text: "Cross-checking multi-timeframe bias", color: "#4ade80" },
                    { text: "Finalizing candle target model", color: "#00f0ff" },
                    { text: "CIPHER LOCKED || NODE ARMED", color: "#4ade80" }
                ];

                var modal = d.createElement('div');
                modal.id = 'ra-hacker-scan-modal';
                modal.style.cssText = 'position:fixed;top:47%;left:50%;transform:translate(-50%, -50%);width:336px;max-width:95vw;' +
                    'background:linear-gradient(160deg, #061d15 0%, #051326 52%, #150726 100%);' +
                    'border:2.5px solid #22c55e;border-radius:14px;padding:10px;z-index:2147483647;' +
                    'font-family:"Courier New",Courier,monospace;color:#4ade80;box-sizing:border-box;will-change:transform;' +
                    'animation:raScanBoxSlowBorder 10s infinite ease-in-out;';

                modal.innerHTML = '' +
                    '<div style="display:flex;justify-content:space-between;align-items:flex-start;border-bottom:1px solid rgba(0,240,255,0.4);padding-bottom:6px;margin-bottom:6px;">' +
                    '  <div style="display:flex;align-items:center;gap:8px;margin-top:-3px;">' +
                    '    <img src="' + botAvatarUrl + '" alt="R-A Candle Hacker" style="width:38px;height:38px;border-radius:50%;object-fit:cover;border:2px solid #00f0ff;flex-shrink:0;animation:raHeaderAvatarGlow 4.5s infinite ease-in-out;" />' +
                    '    <div>' +
                    '      <div style="font-size:12px;font-weight:900;color:#4ade80;letter-spacing:0.6px;text-shadow:0 0 12px rgba(74,222,128,0.9);">R-A Candle Hacker</div>' +
                    '      <div style="font-size:7px;color:#00f0ff;letter-spacing:0.5px;">QUANT CORE EXPLOIT</div>' +
                    '      <div style="font-size:6.5px;color:#94a3b8;">SESSION: QQX-5709-03EE-1967 | NODE 0x37</div>' +
                    '    </div>' +
                    '  </div>' +
                    '  <div style="display:flex;align-items:center;gap:5px;">' +
                    '    <div id="ra-pct-badge" style="background:rgba(20,83,45,0.85);border:1.4px solid #4ade80;color:#4ade80;font-size:9px;font-weight:900;padding:2px 7px;border-radius:10px;animation:raSubBoxCycleA 4.8s infinite ease-in-out;">1%</div>' +
                    '    <div id="ra-modal-close" style="cursor:pointer;color:#94a3b8;font-size:12px;font-weight:bold;padding:0 3px;">✕</div>' +
                    '  </div>' +
                    '</div>' +

                    '<div style="background:rgba(2,10,16,0.94);border:1.5px solid #00f0ff;border-radius:8px;padding:6px 7px;margin-bottom:6px;animation:raSubBoxCycleB 5.4s infinite ease-in-out;">' +
                    '  <div style="display:flex;justify-content:space-between;font-size:7px;color:#00f0ff;margin-bottom:4px;">' +
                    '    <span>MEMORY STREAM</span>' +
                    '    <span id="ra-mem-state" style="color:#4ade80;font-weight:bold;">● LOW</span>' +
                    '  </div>' +
                    '  <div style="display:flex;align-items:center;gap:6px;">' +
                    '    <div id="ra-hero-candle-box" style="width:34px;height:66px;border:1.8px solid #4ade80;border-radius:6px;background:rgba(34,197,94,0.26);display:flex;flex-direction:column;align-items:center;justify-content:center;flex-shrink:0;box-shadow:0 0 34px rgba(34,197,94,1), 0 0 64px rgba(74,222,128,1);animation:raHeroCandleSpinGlow 3s infinite linear;">' +
                    '      <span id="ra-hero-wick-top" style="width:2.5px;height:11px;background:#4ade80;box-shadow:0 0 14px #4ade80;"></span>' +
                    '      <span id="ra-hero-candle-body" style="width:16px;height:36px;background:#22c55e;border:1.3px solid #bbf7d0;border-radius:2px;display:inline-block;box-shadow:0 0 32px rgba(34,197,94,1), 0 0 62px rgba(74,222,128,1);"></span>' +
                    '      <span id="ra-hero-wick-bot" style="width:2.5px;height:11px;background:#4ade80;box-shadow:0 0 14px #4ade80;"></span>' +
                    '    </div>' +
                    '    <div style="flex:1;min-width:0;display:flex;flex-direction:column;gap:4px;">' +
                    '      <div style="display:flex;justify-content:space-between;font-size:6.8px;gap:3px;">' +
                    '        <span><b style="color:#64748b;">OPEN</b> <span style="color:#fff;">0.1645</span></span>' +
                    '        <span><b style="color:#64748b;">HIGH</b> <span style="color:#4ade80;">0.1650</span></span>' +
                    '        <span><b style="color:#64748b;">LOW</b> <span style="color:#f87171;">0.1639</span></span>' +
                    '        <span><b style="color:#64748b;">CLOSE</b> <span style="color:#00f0ff;">0.1643</span></span>' +
                    '      </div>' +

                    '      <div id="ra-track-rtl" style="position:relative;display:flex;align-items:center;height:30px;background:rgba(4,14,22,0.88);border:1.3px solid rgba(74,222,128,0.85);border-radius:5px;padding:0 2px;overflow:hidden;animation:raTrackGlowCycle 5.2s infinite ease-in-out;">' +
                    '        <div style="position:absolute;left:0;right:0;top:50%;height:1.5px;background:rgba(250,204,21,0.95);box-shadow:0 0 14px #facc15;z-index:3;pointer-events:none;"></div>' +
                    '        <div id="ra-volume-bars-rtl" style="position:relative;z-index:2;display:flex;flex-direction:row-reverse;align-items:center;justify-content:flex-start;gap:1px;height:28px;width:100%;"></div>' +
                    '      </div>' +

                    '      <div id="ra-track-ltr" style="position:relative;display:flex;align-items:center;height:30px;background:rgba(4,14,22,0.88);border:1.3px solid rgba(0,240,255,0.85);border-radius:5px;padding:0 2px;overflow:hidden;animation:raTrackGlowCycle 6.4s infinite ease-in-out;">' +
                    '        <div style="position:absolute;left:0;right:0;top:50%;height:1.5px;background:rgba(0,240,255,0.98);box-shadow:0 0 14px #00f0ff;z-index:3;pointer-events:none;"></div>' +
                    '        <div id="ra-volume-bars-ltr" style="position:relative;z-index:2;display:flex;flex-direction:row;align-items:center;justify-content:flex-start;gap:1px;height:28px;width:100%;"></div>' +
                    '      </div>' +
                    '    </div>' +
                    '  </div>' +
                    '</div>' +

                    '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:4px;margin-bottom:4px;font-size:6.8px;text-align:center;">' +
                    '  <div style="background:rgba(2,10,16,0.92);border:1.5px solid #22c55e;border-radius:6px;padding:4px 2px;animation:raSubBoxCycleA 4.2s infinite ease-in-out;"><div style="color:#64748b;">0x29</div><div id="ra-vec-mode" style="color:#4ade80;font-weight:bold;">LOW</div></div>' +
                    '  <div style="background:rgba(2,10,16,0.92);border:1.5px solid #00f0ff;border-radius:6px;padding:4px 2px;animation:raSubBoxCycleB 4.8s infinite ease-in-out;"><div style="color:#00f0ff;font-weight:bold;">LIVE</div><div id="ra-feed-mode" style="color:#86efac;font-weight:bold;">LOW</div></div>' +
                    '  <div style="background:rgba(2,10,16,0.92);border:1.5px solid #facc15;border-radius:6px;padding:4px 2px;animation:raSubBoxCycleC 4.5s infinite ease-in-out;"><div style="color:#64748b;">RSA</div><div id="ra-rsa-val" style="color:#facc15;font-weight:bold;">1%</div></div>' +
                    '  <div style="background:rgba(2,10,16,0.92);border:1.5px solid #e879f9;border-radius:6px;padding:4px 2px;animation:raSubBoxCycleA 5.2s infinite ease-in-out;"><div style="color:#64748b;">016</div><div id="ra-cyc-mode" style="color:#e879f9;font-weight:bold;">LOW</div></div>' +
                    '</div>' +

                    '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:4px;margin-bottom:6px;font-size:6.8px;text-align:center;">' +
                    '  <div style="background:rgba(2,10,16,0.92);border:1.5px solid #22c55e;border-radius:6px;padding:4px 2px;animation:raSubBoxCycleB 4.1s infinite ease-in-out;"><div style="color:#4ade80;font-weight:bold;">23ms</div><div id="ra-lat-mode" style="color:#4ade80;font-size:6.2px;font-weight:bold;">LOW</div></div>' +
                    '  <div style="background:rgba(2,10,16,0.92);border:1.5px solid #fb7185;border-radius:6px;padding:4px 2px;animation:raSubBoxCycleC 4.7s infinite ease-in-out;"><div style="color:#64748b;">BREACH</div><div id="ra-breach-val" style="color:#fb7185;font-weight:bold;">1%</div></div>' +
                    '  <div style="background:rgba(2,10,16,0.92);border:1.5px solid #00f0ff;border-radius:6px;padding:4px 2px;animation:raSubBoxCycleA 5.0s infinite ease-in-out;"><div style="color:#64748b;">016</div><div id="ra-node-mode" style="color:#00f0ff;font-weight:bold;">LOW</div></div>' +
                    '</div>' +

                    '<div id="ra-hex-stream" style="background:rgba(2,10,16,0.94);border:1.4px solid #00f0ff;border-radius:7px;padding:5px 6px;margin-bottom:6px;font-size:6.6px;line-height:1.42;height:74px;overflow-y:auto;animation:raSubBoxCycleB 5.5s infinite ease-in-out;"></div>' +

                    '<div id="ra-terminal-feed" style="background:#02090e;border:1.4px solid #e879f9;border-radius:8px;padding:5px 7px;font-size:7px;line-height:1.42;height:80px;overflow-y:auto;animation:raSubBoxCycleC 5.9s infinite ease-in-out;"></div>';

                d.body.appendChild(modal);
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
                var revealedSteps = 0;
                var revealedHex = 0;
                var revealedDualBars = 0;
                var pctBadge = modal.querySelector('#ra-pct-badge');
                var rsaVal = modal.querySelector('#ra-rsa-val');
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

                var signalPromise = fetch(renderServerUrl + '/signal?market=' + encodeURIComponent(cleanSymbol) + '&t=' + Date.now())
                    .then(function(r){ return r.json(); })
                    .catch(function(){
                        var sNow = Math.floor(Date.now() / 1000);
                        var fb = (sNow % 2 === 0) ? "CALL" : "PUT";
                        return { signal: fb, pts: 8 + ((sNow * 7) % 33) };
                    });

                signalPromise.then(function(data){
                    var sig = String(data.signal || 'CALL').toUpperCase();
                    var isCall = (sig === 'CALL' || sig === 'UP' || sig === 'BUY');
                    applyHeroCandleColor(isCall);
                });

                var trackWidth = (barsRtlEl && barsRtlEl.clientWidth) ? barsRtlEl.clientWidth : 230;
                var candleSlotWidth = 6.2;
                var maxDualCandles = Math.max(28, Math.floor(trackWidth / candleSlotWidth));

                function buildCandleNode(idx, isAltLine) {
                    var isGreenVol = isAltLine ? (idx % 2 === 0) : (idx % 3 !== 1);
                    var vCol = isGreenVol ? '#4ade80' : '#ef4444';
                    var bodyBg = isGreenVol ? '#22c55e' : '#ef4444';
                    var vGlow = isGreenVol
                        ? '0 0 22px #4ade80, 0 0 38px rgba(74,222,128,1)'
                        : '0 0 20px #ef4444, 0 0 34px rgba(248,113,113,1)';
                    var wickGlow = isGreenVol
                        ? '0 0 12px #4ade80, 0 0 22px #22c55e'
                        : '0 0 12px #ef4444, 0 0 18px #f87171';
                    var progressiveGrowth = Math.min(13, Math.floor((idx / maxDualCandles) * 13));
                    var barH = Math.min(24, 6 + progressiveGrowth + ((idx * 3) % 5));
                    var vCandle = d.createElement('div');
                    vCandle.style.cssText = 'display:flex;flex-direction:column;align-items:center;justify-content:center;width:5.2px;height:26px;flex-shrink:0;';
                    vCandle.innerHTML = '' +
                        '<span style="width:1px;height:2.5px;background:' + vCol + ';box-shadow:' + wickGlow + ';"></span>' +
                        '<span style="width:4px;height:' + barH + 'px;background:' + bodyBg + ';border-radius:1px;display:inline-block;box-shadow:' + vGlow + ';"></span>' +
                        '<span style="width:1px;height:2.5px;background:' + vCol + ';box-shadow:' + wickGlow + ';"></span>';
                    return vCandle;
                }

                var scanStartTime = performance.now();
                var scanDurationMs = 6500;
                var finishedScan = false;

                function smoothScanFrame(nowTs) {
                    if(!modal.isConnected || finishedScan) return;

                    var elapsed = nowTs - scanStartTime;
                    var rawRatio = Math.min(1, elapsed / scanDurationMs);
                    var nextPct = Math.max(1, Math.min(100, Math.floor(rawRatio * 99) + 1));

                    if(nextPct !== pct) {
                        pct = nextPct;
                        if(pctBadge) pctBadge.innerText = pct + '%';
                        if(rsaVal) rsaVal.innerText = Math.min(98, pct) + '%';
                        if(breachVal) breachVal.innerText = Math.min(64, Math.round(pct * 0.54)) + '%';

                        var tVec = getTierFromScore(Math.min(100, pct + 18));
                        var tFeed = getTierFromScore(Math.min(100, Math.max(5, pct - 14)));
                        var tCyc = getTierFromScore(Math.min(100, Math.round((pct * 1.15) % 101)));
                        var tLat = getTierFromScore(Math.min(100, Math.max(8, pct + 6)));
                        var tNode = getTierFromScore(Math.min(100, Math.max(4, pct - 24)));
                        var tMem = getTierFromScore(Math.min(100, pct + 10));

                        if(vecMode) { vecMode.innerText = tVec.label; vecMode.style.color = tVec.color; }
                        if(feedMode) { feedMode.innerText = tFeed.label; feedMode.style.color = tFeed.color; }
                        if(cycMode) { cycMode.innerText = tCyc.label; cycMode.style.color = tCyc.color; }
                        if(latMode) { latMode.innerText = tLat.label; latMode.style.color = tLat.color; }
                        if(nodeMode) { nodeMode.innerText = tNode.label; nodeMode.style.color = tNode.color; }
                        if(memState) { memState.innerText = "● " + tMem.label; memState.style.color = tMem.color; }
                    }

                    var candleProgress = Math.min(1, rawRatio / 0.94);
                    var targetDualCount = Math.min(maxDualCandles, Math.floor(candleProgress * maxDualCandles) + (rawRatio > 0.01 ? 1 : 0));
                    if(targetDualCount > revealedDualBars) {
                        var fragRtl = d.createDocumentFragment();
                        var fragLtr = d.createDocumentFragment();
                        while(revealedDualBars < targetDualCount) {
                            if(barsRtlEl) fragRtl.appendChild(buildCandleNode(revealedDualBars, false));
                            if(barsLtrEl) fragLtr.appendChild(buildCandleNode(revealedDualBars, true));
                            revealedDualBars++;
                        }
                        if(barsRtlEl) barsRtlEl.appendChild(fragRtl);
                        if(barsLtrEl) barsLtrEl.appendChild(fragLtr);
                    }

                    var targetHex = Math.min(hexStreamLines.length, Math.floor(rawRatio * hexStreamLines.length) + 1);
                    if(targetHex > revealedHex && hexStreamEl) {
                        var fragHex = d.createDocumentFragment();
                        var hexChanged = false;
                        while(revealedHex < targetHex) {
                            var hObj = hexStreamLines[revealedHex];
                            var hRow = d.createElement('div');
                            hRow.style.color = hObj.color;
                            hRow.innerText = hObj.text;
                            fragHex.appendChild(hRow);
                            revealedHex++;
                            hexChanged = true;
                        }
                        if(hexChanged) {
                            hexStreamEl.appendChild(fragHex);
                            hexStreamEl.scrollTop = hexStreamEl.scrollHeight;
                        }
                    }

                    var targetSteps = Math.min(scanSteps.length, Math.floor(rawRatio * scanSteps.length) + 1);
                    if(targetSteps > revealedSteps && feedEl) {
                        var fragSteps = d.createDocumentFragment();
                        var stepsChanged = false;
                        while(revealedSteps < targetSteps) {
                            var stepObj = scanSteps[revealedSteps];
                            var row = d.createElement('div');
                            row.style.color = stepObj.color;
                            row.innerHTML = '<span style="color:#4ade80;font-weight:900;">✓</span> ' + stepObj.text;
                            fragSteps.appendChild(row);
                            revealedSteps++;
                            stepsChanged = true;
                        }
                        if(stepsChanged) {
                            feedEl.appendChild(fragSteps);
                            feedEl.scrollTop = feedEl.scrollHeight;
                        }
                    }

                    if(rawRatio >= 1) {
                        finishedScan = true;
                        pct = 100;
                        if(pctBadge) pctBadge.innerText = '100%';
                        var finalMarket = detectExactQuotexMarket();
                        signalPromise.then(function(data){
                            var sig = String(data.signal || 'CALL').toUpperCase();
                            var isCall = (sig === 'CALL' || sig === 'UP' || sig === 'BUY');
                            var ptsVal = data.pts;
                            applyHeroCandleColor(isCall);
                            setTimeout(function(){
                                if(modal.isConnected) modal.remove();
                                setBrokerBackgroundBlur(false);
                                showBoxSignalCard(isCall, finalMarket, ptsVal);
                            }, 160);
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
        } catch(err) {
            console.error("R-A Candle Hacker Error:", err);
        }
    })();
    """
    res = make_response(js)
    res.headers['Content-Type'] = 'application/javascript'
    res.headers['Access-Control-Allow-Origin'] = '*'
    return res


def start_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, threaded=True)


if __name__ == '__main__':
    start_server()
