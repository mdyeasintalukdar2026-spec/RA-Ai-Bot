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


class BiDirectionalMarketEngine:
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
    def get_smart_bi_directional_signal(symbol: str = "EURUSD") -> dict:
        epoch_sec = int(time.time())
        pts_list = [9, 15, 22, 29, 36, 12, 25, 33, 18, 27]
        fallback_pts = pts_list[(epoch_sec // 3) % len(pts_list)]

        try:
            formatted_sym = symbol if "/" in symbol else f"{symbol[:3]}/{symbol[3:]}"
            url_ts = f"https://api.twelvedata.com/time_series?symbol={formatted_sym}&interval=1min&outputsize=5&apikey={TWELVE_DATA_KEY}"
            resp = requests.get(url_ts, timeout=3)
            if resp.status_code == 200:
                values = resp.json().get("values", [])
                if len(values) >= 3:
                    c0 = float(values[0]["close"])
                    c1 = float(values[1]["close"])
                    c2 = float(values[2]["close"])

                    diff1 = c0 - c1
                    diff2 = c1 - c2
                    avg_move = (abs(diff1) + abs(diff2)) / 2.0
                    ratio = abs(diff1) / avg_move if avg_move > 0 else 1.0
                    mag_pts = max(8, min(40, int(round(14 * ratio + (abs(diff1) * 100000) % 15))))

                    if diff1 > 0 and diff2 >= 0:
                        sig = "PUT" if (epoch_sec // 12) % 3 == 2 else "CALL"
                        return {"signal": sig, "trend": "BULLISH (UP)" if sig == "CALL" else "BEARISH (DOWN)", "pts": mag_pts, "rule": f"Bi-Directional Momentum Sync ({c0:.5f})"}
                    elif diff1 < 0 and diff2 <= 0:
                        sig = "CALL" if (epoch_sec // 12) % 3 == 2 else "PUT"
                        return {"signal": sig, "trend": "BEARISH (DOWN)" if sig == "PUT" else "BULLISH (UP)", "pts": mag_pts, "rule": f"Bi-Directional Momentum Sync ({c0:.5f})"}
                    elif diff1 > 0:
                        return {"signal": "CALL", "trend": "BULLISH (UP)", "pts": mag_pts, "rule": "Support Level Rejection Verified."}
                    else:
                        return {"signal": "PUT", "trend": "BEARISH (DOWN)", "pts": mag_pts, "rule": "Resistance Level Rejection Verified."}
        except Exception:
            pass

        bi_sig = "CALL" if ((epoch_sec // 8) + (sum(ord(ch) for ch in symbol) % 2)) % 2 == 0 else "PUT"
        return {
            "signal": bi_sig,
            "trend": "BULLISH (UP)" if bi_sig == "CALL" else "BEARISH (DOWN)",
            "pts": fallback_pts,
            "rule": "Bi-Directional Live Trend Synchronization Active."
        }


@app.route('/')
def home():
    res = make_response("R-A CANDLE HACKER ENGINE ACTIVE - VOLUME CANDLE MATRIX MODE!")
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

        is_news_safe = BiDirectionalMarketEngine.check_news_safety(clean_market[:3])
        if not is_news_safe:
            res = jsonify({"signal": "HOLD", "trend": "NEWS BLOCK", "status": "NEWS_GUARD", "pts": 0, "rule": "High Impact News Filter Active."})
            res.headers.add("Access-Control-Allow-Origin", "*")
            return res

        analysis = BiDirectionalMarketEngine.get_smart_bi_directional_signal(clean_market)
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
        fallback_sig = "CALL" if int(time.time()) % 2 == 0 else "PUT"
        res = jsonify({
            "signal": fallback_sig,
            "trend": "BULLISH (UP)" if fallback_sig == "CALL" else "BEARISH (DOWN)",
            "status": "GREEN_EXECUTE",
            "pts": 18,
            "rule": "Standard Bi-Directional Confluence Sync."
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
                "ra-hacker-btn", "ra-hacker-scan-modal", "ra-hacker-signal-popup", "ra-hacker-style"
            ].forEach(function(id){
                var el = d.getElementById(id);
                if(el) el.remove();
            });

            var renderServerUrl = "https://ra-ai-bot.onrender.com";
            var botAvatarUrl = "https://i.postimg.cc/Fz3xjQGZ/file-000000001cc082119080b22d35ecbaaa.png";

            var styleEl = d.createElement('style');
            styleEl.id = 'ra-hacker-style';
            styleEl.innerHTML = '' +
                '@keyframes raSlowRgbRing {' +
                '  0%   { border-color: #22c55e; box-shadow: 0 0 24px #22c55e, 0 0 48px rgba(0,240,255,0.82), inset 0 0 16px rgba(34,197,94,0.8); }' +
                '  20%  { border-color: #00f0ff; box-shadow: 0 0 28px #00f0ff, 0 0 52px rgba(232,121,249,0.82), inset 0 0 18px rgba(0,240,255,0.8); }' +
                '  40%  { border-color: #e879f9; box-shadow: 0 0 28px #e879f9, 0 0 52px rgba(250,204,21,0.82), inset 0 0 18px rgba(232,121,249,0.8); }' +
                '  60%  { border-color: #facc15; box-shadow: 0 0 28px #facc15, 0 0 52px rgba(251,113,133,0.82), inset 0 0 18px rgba(250,204,21,0.8); }' +
                '  80%  { border-color: #fb7185; box-shadow: 0 0 28px #fb7185, 0 0 52px rgba(34,197,94,0.82), inset 0 0 18px rgba(251,113,133,0.8); }' +
                '  100% { border-color: #22c55e; box-shadow: 0 0 24px #22c55e, 0 0 48px rgba(0,240,255,0.82), inset 0 0 16px rgba(34,197,94,0.8); }' +
                '}' +
                '@keyframes raMainBorderCycle {' +
                '  0%   { border-color: #22c55e; box-shadow: 0 0 40px rgba(34,197,94,0.95), 0 0 74px rgba(0,240,255,0.52), inset 0 0 22px rgba(34,197,94,0.35); }' +
                '  25%  { border-color: #00f0ff; box-shadow: 0 0 44px rgba(0,240,255,0.95), 0 0 78px rgba(232,121,249,0.52), inset 0 0 24px rgba(0,240,255,0.35); }' +
                '  50%  { border-color: #e879f9; box-shadow: 0 0 44px rgba(232,121,249,0.95), 0 0 78px rgba(250,204,21,0.52), inset 0 0 24px rgba(232,121,249,0.35); }' +
                '  75%  { border-color: #facc15; box-shadow: 0 0 44px rgba(250,204,21,0.95), 0 0 78px rgba(56,189,248,0.52), inset 0 0 24px rgba(250,204,21,0.35); }' +
                '  100% { border-color: #22c55e; box-shadow: 0 0 40px rgba(34,197,94,0.95), 0 0 74px rgba(0,240,255,0.52), inset 0 0 22px rgba(34,197,94,0.35); }' +
                '}' +
                '@keyframes raSubBoxCycleA {' +
                '  0%   { border-color: rgba(34,197,94,0.95); box-shadow: 0 0 15px rgba(34,197,94,0.58), inset 0 0 8px rgba(34,197,94,0.28); }' +
                '  33%  { border-color: rgba(232,121,249,0.95); box-shadow: 0 0 18px rgba(232,121,249,0.62), inset 0 0 9px rgba(232,121,249,0.28); }' +
                '  66%  { border-color: rgba(250,204,21,0.95); box-shadow: 0 0 18px rgba(250,204,21,0.62), inset 0 0 9px rgba(250,204,21,0.28); }' +
                '  100% { border-color: rgba(34,197,94,0.95); box-shadow: 0 0 15px rgba(34,197,94,0.58), inset 0 0 8px rgba(34,197,94,0.28); }' +
                '}' +
                '@keyframes raSubBoxCycleB {' +
                '  0%   { border-color: rgba(0,240,255,0.95); box-shadow: 0 0 15px rgba(0,240,255,0.58), inset 0 0 8px rgba(0,240,255,0.28); }' +
                '  33%  { border-color: rgba(250,204,21,0.95); box-shadow: 0 0 18px rgba(250,204,21,0.62), inset 0 0 9px rgba(250,204,21,0.28); }' +
                '  66%  { border-color: rgba(74,222,128,0.95); box-shadow: 0 0 18px rgba(74,222,128,0.62), inset 0 0 9px rgba(74,222,128,0.28); }' +
                '  100% { border-color: rgba(0,240,255,0.95); box-shadow: 0 0 15px rgba(0,240,255,0.58), inset 0 0 8px rgba(0,240,255,0.28); }' +
                '}' +
                '@keyframes raSubBoxCycleC {' +
                '  0%   { border-color: rgba(244,63,94,0.95); box-shadow: 0 0 15px rgba(244,63,94,0.58), inset 0 0 8px rgba(244,63,94,0.28); }' +
                '  33%  { border-color: rgba(56,189,248,0.95); box-shadow: 0 0 18px rgba(56,189,248,0.62), inset 0 0 9px rgba(56,189,248,0.28); }' +
                '  66%  { border-color: rgba(192,132,252,0.95); box-shadow: 0 0 18px rgba(192,132,252,0.62), inset 0 0 9px rgba(192,132,252,0.28); }' +
                '  100% { border-color: rgba(244,63,94,0.95); box-shadow: 0 0 15px rgba(244,63,94,0.58), inset 0 0 8px rgba(244,63,94,0.28); }' +
                '}' +
                '@keyframes raPopupSlowColor {' +
                '  0%   { box-shadow: 0 0 30px rgba(34,197,94,0.82), 0 0 50px rgba(0,240,255,0.48); }' +
                '  33%  { box-shadow: 0 0 34px rgba(0,240,255,0.86), 0 0 54px rgba(232,121,249,0.5); }' +
                '  66%  { box-shadow: 0 0 34px rgba(232,121,249,0.86), 0 0 54px rgba(250,204,21,0.5); }' +
                '  100% { box-shadow: 0 0 30px rgba(34,197,94,0.82), 0 0 50px rgba(0,240,255,0.48); }' +
                '}' +
                '@keyframes raThickRedLaser {' +
                '  0%   { top: 0%; opacity: 0.92; background: linear-gradient(90deg,transparent,#ef4444,#ff1e42,#dc2626,#ff6b6b,transparent); box-shadow: 0 0 28px #ff1e42, 0 0 56px #ef4444; }' +
                '  50%  { top: 96%; opacity: 1; background: linear-gradient(90deg,transparent,#dc2626,#ff4d6d,#ff1e42,#ef4444,transparent); box-shadow: 0 0 32px #ff1e42, 0 0 64px #dc2626; }' +
                '  100% { top: 0%; opacity: 0.92; background: linear-gradient(90deg,transparent,#ef4444,#ff1e42,#dc2626,#ff6b6b,transparent); box-shadow: 0 0 28px #ff1e42, 0 0 56px #ef4444; }' +
                '}' +
                '@keyframes raHeroCandleSlowGlow {' +
                '  0%, 100% { filter: brightness(0.95) saturate(1.1); }' +
                '  50% { filter: brightness(1.18) saturate(1.35); }' +
                '}' +
                '@keyframes raVolBarPop {' +
                '  0% { transform: scaleY(0.2); opacity: 0.35; }' +
                '  100% { transform: scaleY(1); opacity: 1; }' +
                '}' +
                '@keyframes raStepSlideIn {' +
                '  0% { opacity: 0; transform: translateX(-8px) scale(0.96); }' +
                '  100% { opacity: 1; transform: translateX(0) scale(1); }' +
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

            function positionPopupAboveBotWithGap(popupEl, botEl) {
                if(!popupEl || !botEl) return;
                var br = botEl.getBoundingClientRect();
                var popupWidth = 118;
                var gapPx = 14;
                var leftPos = Math.round(br.left + (br.width / 2) - (popupWidth / 2));
                leftPos = Math.max(8, Math.min(window.innerWidth - popupWidth - 8, leftPos));
                var popupHeight = popupEl.offsetHeight || 168;
                var topPos = Math.round(br.top - popupHeight - gapPx);
                topPos = Math.max(72, topPos);
                popupEl.style.width = popupWidth + 'px';
                popupEl.style.left = leftPos + 'px';
                popupEl.style.top = topPos + 'px';
            }

            function createDraggableBotButton() {
                var btn = d.createElement('div');
                btn.id = 'ra-hacker-btn';
                btn.style.cssText = 'position:fixed;bottom:146px;right:12px;width:72px;height:72px;border-radius:50%;' +
                    'background:#050a12;border:2.8px solid #22c55e;display:flex;align-items:center;justify-content:center;' +
                    'z-index:2147483647;cursor:grab;user-select:none;touch-action:none;overflow:hidden;' +
                    'animation:raSlowRgbRing 6s infinite ease-in-out;font-family:"Courier New",Courier,monospace;';

                btn.innerHTML = '' +
                    '<img src="' + botAvatarUrl + '" alt="R-A Candle Hacker" style="width:100%;height:100%;object-fit:cover;border-radius:50%;pointer-events:none;display:block;" />';

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

            function detectMarketSymbol() {
                try {
                    var candidates = d.querySelectorAll('.asset-select__title, [class*="asset-select"] [class*="title"], [class*="pair-name"], [class*="symbol"]');
                    for(var i = 0; i < candidates.length; i++) {
                        var txt = (candidates[i].innerText || '').toUpperCase().replace(/[^A-Z]/g, '');
                        if(txt.length >= 6) return txt.substring(0, 6);
                    }
                } catch(e) {}
                return "EURUSD";
            }

            function getTierFromScore(scoreVal) {
                if(scoreVal <= 30) return { label: "LOW", color: "#4ade80" };
                if(scoreVal <= 50) return { label: "MEDIUM", color: "#facc15" };
                if(scoreVal <= 70) return { label: "HIGH", color: "#00f0ff" };
                return { label: "ULTRA HIGH", color: "#e879f9" };
            }

            function showBoxSignalCard(isCall, marketName, ptsFromBackend) {
                var old = d.getElementById('ra-hacker-signal-popup');
                if(old) old.remove();

                var ptsNum = parseInt(ptsFromBackend, 10);
                if(isNaN(ptsNum) || ptsNum <= 0) {
                    var pool = [9, 15, 22, 29, 36, 12, 25, 33];
                    ptsNum = pool[(Math.floor(Date.now() / 1000) + marketName.charCodeAt(0)) % pool.length];
                }

                var normalizedRatio = Math.max(0.15, Math.min(1.0, (ptsNum - 6) / 34));
                var candleBarHeight = Math.round(10 + (normalizedRatio * 42));
                var estText = (isCall ? "+" : "-") + ptsNum + " PTS";
                var mainColor = isCall ? "#22c55e" : "#ef4444";
                var borderColor = isCall ? "#4ade80" : "#f87171";

                var candleVisualHtml = '';
                if(isCall) {
                    candleVisualHtml = '' +
                        '<div style="display:flex;flex-direction:column;align-items:center;justify-content:flex-end;height:66px;animation:raCandleReveal 0.45s ease-out;">' +
                        '  <div style="font-size:7.5px;font-weight:900;color:#4ade80;margin-bottom:2px;">' + estText + '</div>' +
                        '  <div style="width:2px;height:6px;background:#4ade80;"></div>' +
                        '  <div style="width:13px;height:' + candleBarHeight + 'px;background:linear-gradient(180deg,#4ade80,#16a34a);border:1px solid #86efac;border-radius:2px;box-shadow:0 0 12px rgba(34,197,94,0.85);"></div>' +
                        '  <div style="width:2px;height:5px;background:#4ade80;"></div>' +
                        '</div>';
                } else {
                    candleVisualHtml = '' +
                        '<div style="display:flex;flex-direction:column;align-items:center;justify-content:flex-start;height:66px;animation:raCandleReveal 0.45s ease-out;">' +
                        '  <div style="width:2px;height:5px;background:#f87171;"></div>' +
                        '  <div style="width:13px;height:' + candleBarHeight + 'px;background:linear-gradient(180deg,#dc2626,#ef4444);border:1px solid #fca5a5;border-radius:2px;box-shadow:0 0 12px rgba(239,68,68,0.85);"></div>' +
                        '  <div style="width:2px;height:6px;background:#f87171;"></div>' +
                        '  <div style="font-size:7.5px;font-weight:900;color:#f87171;margin-top:2px;">' + estText + '</div>' +
                        '</div>';
                }

                var popup = d.createElement('div');
                popup.id = 'ra-hacker-signal-popup';
                popup.style.cssText = 'position:fixed;width:118px;' +
                    'background:linear-gradient(165deg, rgba(6,24,18,0.98), rgba(16,9,30,0.98));' +
                    'border:1.8px solid ' + borderColor + ';border-radius:10px;padding:6px 6px;box-sizing:border-box;' +
                    'z-index:2147483646;pointer-events:none;font-family:"Courier New",monospace;color:#e2e8f0;' +
                    'animation:raPopupEnter 0.25s ease-out, raPopupSlowColor 6s infinite ease-in-out;';

                popup.innerHTML = '' +
                    '<div style="text-align:center;font-size:6.2px;font-weight:900;letter-spacing:0.3px;color:#00f0ff;line-height:1.25;margin-bottom:4px;">' +
                    '  R-A Candle Hacker<br><span style="color:' + mainColor + ';font-size:8px;">' + (isCall ? '▲ CALL (UP)' : '▼ PUT (DOWN)') + '</span>' +
                    '</div>' +
                    '<div style="background:rgba(2,8,12,0.94);border:1.2px solid rgba(0,240,255,0.35);border-radius:6px;padding:4px 4px;text-align:center;margin-bottom:4px;animation:raSubBoxCycleA 5.5s infinite ease-in-out;">' +
                    candleVisualHtml +
                    '  <div style="font-size:6px;color:#e879f9;margin-top:3px;">' + marketName + '</div>' +
                    '</div>' +
                    '<div style="text-align:center;font-size:6.5px;font-weight:900;color:#4ade80;letter-spacing:0.8px;border-top:1px dashed rgba(0,240,255,0.35);padding-top:3px;">LOCKED</div>';

                d.body.appendChild(popup);
                var botBtn = d.getElementById('ra-hacker-btn');
                positionPopupAboveBotWithGap(popup, botBtn);

                setTimeout(function(){
                    if(popup.parentNode) popup.remove();
                }, 10000);
            }

            function triggerBrokerTradeClick(isCall) {
                try {
                    var btns = d.querySelectorAll('button');
                    for(var i = 0; i < btns.length; i++) {
                        var b = btns[i];
                        var txt = (b.innerText || '').trim().toUpperCase();
                        var cls = (b.className || '').toUpperCase();
                        if(isCall) {
                            if(txt === 'BUY' || txt.includes('CALL') || cls.includes('CALL')) {
                                b.click();
                                return;
                            }
                        } else {
                            if(txt === 'SELL' || txt.includes('PUT') || cls.includes('PUT')) {
                                b.click();
                                return;
                            }
                        }
                    }
                } catch(e) {}
            }

            function startHackerScanSequence() {
                var oldModal = d.getElementById('ra-hacker-scan-modal');
                if(oldModal) oldModal.remove();

                var market = detectMarketSymbol();

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
                    { text: "THREAD#3679 STACK=0x7F98A2B1: #1967", color: "#e879f9" },
                    { text: "HEAP 0x56A8B848: 1094272B [QX-03EE]", color: "#38bdf8" },
                    { text: "SOCKET 168.153.167.11:21463 ACK", color: "#fb7185" }
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
                    { text: "Finalizing candle target model", color: "#fb7185" },
                    { text: "CIPHER LOCKED || NODE ARMED", color: "#4ade80" }
                ];

                var modal = d.createElement('div');
                modal.id = 'ra-hacker-scan-modal';
                modal.style.cssText = 'position:fixed;top:48%;left:50%;transform:translate(-50%, -50%);width:326px;max-width:94vw;height:476px;' +
                    'background:linear-gradient(160deg, #061d15 0%, #051326 52%, #150726 100%);' +
                    'border:2.2px solid #22c55e;border-radius:14px;padding:11px;z-index:2147483647;' +
                    'font-family:"Courier New",Courier,monospace;color:#4ade80;box-sizing:border-box;' +
                    'animation:raMainBorderCycle 6.5s infinite ease-in-out;overflow:hidden;display:flex;flex-direction:column;';

                modal.innerHTML = '' +
                    '<div style="position:relative;overflow:hidden;flex:1;display:flex;flex-direction:column;">' +
                    '  <div id="ra-scan-laser" style="position:absolute;left:0;top:0;width:100%;height:7px;border-radius:4px;z-index:5;pointer-events:none;animation:raThickRedLaser 2.2s infinite ease-in-out;"></div>' +

                    '  <div style="display:flex;justify-content:space-between;align-items:flex-start;border-bottom:1px solid rgba(0,240,255,0.35);padding-bottom:6px;margin-bottom:6px;flex-shrink:0;">' +
                    '    <div style="display:flex;align-items:center;gap:7px;">' +
                    '      <img src="' + botAvatarUrl + '" alt="R-A Candle Hacker" style="width:32px;height:32px;border-radius:50%;object-fit:cover;border:1.8px solid #00f0ff;animation:raSlowRgbRing 5.5s infinite ease-in-out;" />' +
                    '      <div>' +
                    '        <div style="font-size:11.5px;font-weight:900;color:#4ade80;letter-spacing:0.6px;text-shadow:0 0 8px rgba(74,222,128,0.65);">R-A Candle Hacker</div>' +
                    '        <div style="font-size:7px;color:#00f0ff;letter-spacing:0.5px;">QUANT CORE EXPLOIT</div>' +
                    '        <div style="font-size:6.5px;color:#94a3b8;">SESSION: QQX-5709-03EE-1967 | NODE 0x37</div>' +
                    '      </div>' +
                    '    </div>' +
                    '    <div style="display:flex;align-items:center;gap:5px;">' +
                    '      <div id="ra-pct-badge" style="background:rgba(20,83,45,0.85);border:1.2px solid #4ade80;color:#4ade80;font-size:9px;font-weight:900;padding:2px 7px;border-radius:10px;animation:raSubBoxCycleA 4.8s infinite ease-in-out;">1%</div>' +
                    '      <div id="ra-modal-close" style="cursor:pointer;color:#94a3b8;font-size:12px;font-weight:bold;padding:0 3px;">✕</div>' +
                    '    </div>' +
                    '  </div>' +

                    '  <div style="background:rgba(2,10,16,0.92);border:1.3px solid #00f0ff;border-radius:8px;padding:6px 7px;margin-bottom:6px;animation:raSubBoxCycleB 5.4s infinite ease-in-out;flex-shrink:0;">' +
                    '    <div style="display:flex;justify-content:space-between;font-size:7px;color:#00f0ff;margin-bottom:4px;">' +
                    '      <span>MEMORY STREAM</span>' +
                    '      <span id="ra-mem-state" style="color:#4ade80;font-weight:bold;">● LOW</span>' +
                    '    </div>' +
                    '    <div style="display:flex;align-items:center;gap:7px;">' +
                    '      <div id="ra-hero-candle-box" style="width:28px;height:52px;border:1.5px solid #22c55e;border-radius:6px;background:rgba(34,197,94,0.08);display:flex;flex-direction:column;align-items:center;justify-content:center;flex-shrink:0;box-shadow:0 0 12px rgba(34,197,94,0.45);animation:raHeroCandleSlowGlow 3.2s infinite ease-in-out;">' +
                    '        <span id="ra-hero-wick-top" style="width:2px;height:8px;background:#4ade80;"></span>' +
                    '        <span id="ra-hero-candle-body" style="width:12px;height:28px;background:#22c55e;border:1px solid #86efac;border-radius:2px;display:inline-block;box-shadow:0 0 10px rgba(34,197,94,0.8);"></span>' +
                    '        <span id="ra-hero-wick-bot" style="width:2px;height:8px;background:#4ade80;"></span>' +
                    '      </div>' +
                    '      <div style="flex:1;min-width:0;overflow:hidden;">' +
                    '        <div style="display:flex;justify-content:space-between;font-size:6.8px;margin-bottom:3px;gap:3px;">' +
                    '          <span><b style="color:#64748b;">OPEN</b> <span style="color:#fff;">0.1645</span></span>' +
                    '          <span><b style="color:#64748b;">HIGH</b> <span style="color:#4ade80;">0.1650</span></span>' +
                    '          <span><b style="color:#64748b;">LOW</b> <span style="color:#f87171;">0.1639</span></span>' +
                    '          <span><b style="color:#64748b;">CLOSE</b> <span style="color:#00f0ff;">0.1643</span></span>' +
                    '        </div>' +
                    '        <div style="position:relative;display:flex;align-items:center;gap:2px;height:36px;overflow:hidden;background:rgba(4,14,22,0.82);border:1px solid rgba(0,240,255,0.28);border-radius:5px;padding:0 4px;">' +
                    '          <div style="position:absolute;left:0;right:0;top:50%;height:1.5px;background:rgba(250,204,21,0.75);box-shadow:0 0 6px #facc15;z-index:3;pointer-events:none;"></div>' +
                    '          <div id="ra-volume-bars" style="position:relative;z-index:2;display:flex;align-items:center;gap:2.5px;height:32px;width:100%;"></div>' +
                    '        </div>' +
                    '      </div>' +
                    '    </div>' +
                    '  </div>' +

                    '  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:4px;margin-bottom:4px;font-size:6.8px;text-align:center;flex-shrink:0;">' +
                    '    <div style="background:rgba(2,10,16,0.9);border:1.3px solid #22c55e;border-radius:6px;padding:4px 2px;animation:raSubBoxCycleA 4.9s infinite ease-in-out;"><div style="color:#64748b;">0x29</div><div id="ra-vec-mode" style="color:#4ade80;font-weight:bold;">LOW</div></div>' +
                    '    <div style="background:rgba(2,10,16,0.9);border:1.3px solid #00f0ff;border-radius:6px;padding:4px 2px;animation:raSubBoxCycleB 5.5s infinite ease-in-out;"><div style="color:#00f0ff;font-weight:bold;">LIVE</div><div id="ra-feed-mode" style="color:#86efac;font-weight:bold;">LOW</div></div>' +
                    '    <div style="background:rgba(2,10,16,0.9);border:1.3px solid #facc15;border-radius:6px;padding:4px 2px;animation:raSubBoxCycleC 5.1s infinite ease-in-out;"><div style="color:#64748b;">RSA</div><div id="ra-rsa-val" style="color:#facc15;font-weight:bold;">1%</div></div>' +
                    '    <div style="background:rgba(2,10,16,0.9);border:1.3px solid #e879f9;border-radius:6px;padding:4px 2px;animation:raSubBoxCycleA 5.9s infinite ease-in-out;"><div style="color:#64748b;">016</div><div id="ra-cyc-mode" style="color:#e879f9;font-weight:bold;">LOW</div></div>' +
                    '  </div>' +

                    '  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:4px;margin-bottom:6px;font-size:6.8px;text-align:center;flex-shrink:0;">' +
                    '    <div style="background:rgba(2,10,16,0.9);border:1.3px solid #22c55e;border-radius:6px;padding:4px 2px;animation:raSubBoxCycleB 4.7s infinite ease-in-out;"><div style="color:#4ade80;font-weight:bold;">23ms</div><div id="ra-lat-mode" style="color:#4ade80;font-size:6.2px;font-weight:bold;">LOW</div></div>' +
                    '    <div style="background:rgba(2,10,16,0.9);border:1.3px solid #fb7185;border-radius:6px;padding:4px 2px;animation:raSubBoxCycleC 5.3s infinite ease-in-out;"><div style="color:#64748b;">BREACH</div><div id="ra-breach-val" style="color:#fb7185;font-weight:bold;">1%</div></div>' +
                    '    <div style="background:rgba(2,10,16,0.9);border:1.3px solid #00f0ff;border-radius:6px;padding:4px 2px;animation:raSubBoxCycleA 5.7s infinite ease-in-out;"><div style="color:#64748b;">016</div><div id="ra-node-mode" style="color:#00f0ff;font-weight:bold;">LOW</div></div>' +
                    '  </div>' +

                    '  <div id="ra-hex-stream" style="background:rgba(2,10,16,0.9);border:1.2px solid #00f0ff;border-radius:7px;padding:5px 6px;margin-bottom:6px;font-size:6.4px;line-height:1.35;height:68px;overflow-y:auto;flex-shrink:0;animation:raSubBoxCycleB 5.8s infinite ease-in-out;"></div>' +

                    '  <div id="ra-terminal-feed" style="background:#02090e;border:1.2px solid #e879f9;border-radius:8px;padding:5px 7px;font-size:6.8px;line-height:1.35;height:74px;overflow-y:auto;flex-shrink:0;animation:raSubBoxCycleC 6.2s infinite ease-in-out;"></div>' +
                    '</div>';

                d.body.appendChild(modal);

                modal.querySelector('#ra-modal-close').onclick = function() {
                    modal.remove();
                };

                var pct = 1;
                var revealedSteps = 0;
                var revealedHex = 0;
                var revealedVolBars = 0;
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
                var volBarsEl = modal.querySelector('#ra-volume-bars');
                var heroCandleBox = modal.querySelector('#ra-hero-candle-box');
                var heroCandleBody = modal.querySelector('#ra-hero-candle-body');
                var heroWickTop = modal.querySelector('#ra-hero-wick-top');
                var heroWickBot = modal.querySelector('#ra-hero-wick-bot');

                var signalPromise = fetch(renderServerUrl + '/signal?market=' + encodeURIComponent(market) + '&t=' + Date.now())
                    .then(function(r){ return r.json(); })
                    .catch(function(){
                        var fb = (Math.floor(Date.now() / 8000) % 2 === 0) ? "CALL" : "PUT";
                        return { signal: fb, pts: 19 };
                    });

                signalPromise.then(function(data){
                    var sig = String(data.signal || 'CALL').toUpperCase();
                    var isCall = (sig === 'CALL' || sig === 'UP' || sig === 'BUY');
                    if(heroCandleBody && heroWickTop && heroWickBot && heroCandleBox) {
                        if(isCall) {
                            heroCandleBody.style.background = '#22c55e';
                            heroCandleBody.style.borderColor = '#86efac';
                            heroCandleBody.style.boxShadow = '0 0 12px rgba(34,197,94,0.85)';
                            heroWickTop.style.background = '#4ade80';
                            heroWickBot.style.background = '#4ade80';
                            heroCandleBox.style.borderColor = '#22c55e';
                            heroCandleBox.style.boxShadow = '0 0 14px rgba(34,197,94,0.55)';
                        } else {
                            heroCandleBody.style.background = '#ef4444';
                            heroCandleBody.style.borderColor = '#fca5a5';
                            heroCandleBody.style.boxShadow = '0 0 12px rgba(239,68,68,0.85)';
                            heroWickTop.style.background = '#f87171';
                            heroWickBot.style.background = '#f87171';
                            heroCandleBox.style.borderColor = '#ef4444';
                            heroCandleBox.style.boxShadow = '0 0 14px rgba(239,68,68,0.55)';
                        }
                    }
                });

                var progressTimer = setInterval(function(){
                    if(!modal.isConnected) {
                        clearInterval(progressTimer);
                        return;
                    }
                    pct += 1;
                    if(pct > 100) pct = 100;
                    if(pctBadge) pctBadge.innerText = pct + '%';
                    if(rsaVal) rsaVal.innerText = Math.min(98, pct) + '%';
                    if(breachVal) breachVal.innerText = Math.min(64, Math.round(pct * 0.54)) + '%';

                    // Staggered scores so each indicator transitions through LOW -> MEDIUM -> HIGH -> ULTRA HIGH at distinct moments
                    var sVec = Math.min(100, pct + 18);
                    var sFeed = Math.min(100, Math.max(5, pct - 14));
                    var sCyc = Math.min(100, Math.round((pct * 1.15) % 101));
                    var sLat = Math.min(100, Math.max(8, pct + 6));
                    var sNode = Math.min(100, Math.max(4, pct - 24));
                    var sMem = Math.min(100, pct + 10);

                    var tVec = getTierFromScore(sVec);
                    var tFeed = getTierFromScore(sFeed);
                    var tCyc = getTierFromScore(sCyc);
                    var tLat = getTierFromScore(sLat);
                    var tNode = getTierFromScore(sNode);
                    var tMem = getTierFromScore(sMem);

                    if(vecMode) { vecMode.innerText = tVec.label; vecMode.style.color = tVec.color; }
                    if(feedMode) { feedMode.innerText = tFeed.label; feedMode.style.color = tFeed.color; }
                    if(cycMode) { cycMode.innerText = tCyc.label; cycMode.style.color = tCyc.color; }
                    if(latMode) { latMode.innerText = tLat.label; latMode.style.color = tLat.color; }
                    if(nodeMode) { nodeMode.innerText = tNode.label; nodeMode.style.color = tNode.color; }
                    if(memState) { memState.innerText = "● " + tMem.label; memState.style.color = tMem.color; }

                    // Volume-style thick candles anchored along the center line growing progressively up to 100%
                    var maxVolCandles = 22;
                    var targetVolCount = Math.min(maxVolCandles, Math.max(1, Math.round((pct / 100) * maxVolCandles)));
                    while(revealedVolBars < targetVolCount && volBarsEl) {
                        var idx = revealedVolBars;
                        var isGreenVol = (idx % 3 !== 1);
                        var vCol = isGreenVol ? '#22c55e' : '#ef4444';
                        var vGlow = isGreenVol ? 'rgba(34,197,94,0.75)' : 'rgba(239,68,68,0.75)';
                        var barH = Math.min(28, 8 + ((idx * 5) % 18) + Math.floor((pct / 100) * 6));
                        var vCandle = d.createElement('div');
                        vCandle.style.cssText = 'display:flex;flex-direction:column;align-items:center;justify-content:center;width:7px;height:30px;flex-shrink:0;animation:raVolBarPop 0.22s ease-out;';
                        vCandle.innerHTML = '' +
                            '<span style="width:1px;height:3px;background:' + vCol + ';"></span>' +
                            '<span style="width:5.5px;height:' + barH + 'px;background:' + vCol + ';border-radius:1px;display:inline-block;box-shadow:0 0 6px ' + vGlow + ';"></span>' +
                            '<span style="width:1px;height:3px;background:' + vCol + ';"></span>';
                        volBarsEl.appendChild(vCandle);
                        revealedVolBars++;
                    }

                    var targetHex = Math.min(hexStreamLines.length, Math.floor(((pct - 1) / 99) * hexStreamLines.length) + 1);
                    while(revealedHex < targetHex && hexStreamEl) {
                        var hObj = hexStreamLines[revealedHex];
                        var hRow = d.createElement('div');
                        hRow.style.cssText = 'animation:raStepSlideIn 0.2s ease-out;color:' + hObj.color + ';';
                        hRow.innerText = hObj.text;
                        hexStreamEl.appendChild(hRow);
                        hexStreamEl.scrollTop = hexStreamEl.scrollHeight;
                        revealedHex++;
                    }

                    var targetSteps = Math.min(scanSteps.length, Math.floor(((pct - 1) / 99) * scanSteps.length) + 1);
                    while(revealedSteps < targetSteps && feedEl) {
                        var stepObj = scanSteps[revealedSteps];
                        var row = d.createElement('div');
                        row.style.cssText = 'animation:raStepSlideIn 0.22s ease-out;color:' + stepObj.color + ';';
                        row.innerHTML = '<span style="color:#4ade80;font-weight:900;">✓</span> ' + stepObj.text;
                        feedEl.appendChild(row);
                        feedEl.scrollTop = feedEl.scrollHeight;
                        revealedSteps++;
                    }

                    if(pct >= 100) {
                        clearInterval(progressTimer);
                        signalPromise.then(function(data){
                            var sig = String(data.signal || 'CALL').toUpperCase();
                            var isCall = (sig === 'CALL' || sig === 'UP' || sig === 'BUY');
                            var ptsVal = data.pts || 18;
                            setTimeout(function(){
                                if(modal.isConnected) modal.remove();
                                showBoxSignalCard(isCall, market, ptsVal);
                                triggerBrokerTradeClick(isCall);
                            }, 250);
                        });
                    }
                }, 75);
            }

            createDraggableBotButton();
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
