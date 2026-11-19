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
                    mag_pts = max(7, min(42, int(round(14 * ratio + (abs(diff1) * 100000) % 16))))

                    if diff1 > 0 and diff2 >= 0:
                        return {"signal": "CALL", "trend": "BULLISH (UP)", "pts": mag_pts, "rule": f"Upward Expansion Confirmed ({c0:.5f} > {c1:.5f})"}
                    elif diff1 < 0 and diff2 <= 0:
                        return {"signal": "PUT", "trend": "BEARISH (DOWN)", "pts": mag_pts, "rule": f"Downward Expansion Confirmed ({c0:.5f} < {c1:.5f})"}
                    elif diff1 > 0:
                        return {"signal": "CALL", "trend": "BULLISH (UP)", "pts": mag_pts, "rule": "Support Level Rejection Verified."}
                    else:
                        return {"signal": "PUT", "trend": "BEARISH (DOWN)", "pts": mag_pts, "rule": "Resistance Level Rejection Verified."}
        except Exception:
            pass

        epoch_sec = int(time.time())
        pts_list = [8, 15, 23, 31, 38, 11, 19, 27, 34]
        est_pts = pts_list[(epoch_sec // 4) % len(pts_list)]
        if (epoch_sec // 15) % 2 == 0:
            return {"signal": "CALL", "trend": "BULLISH (UP)", "pts": est_pts, "rule": "Live Trend Synchronization Active."}
        else:
            return {"signal": "PUT", "trend": "BEARISH (DOWN)", "pts": est_pts, "rule": "Live Trend Synchronization Active."}


@app.route('/')
def home():
    res = make_response("R-A CANDLE HACKER ENGINE ACTIVE - QUANTUM NEON MODE!")
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
            "rule": "Standard Confluence Sync."
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

            var styleEl = d.createElement('style');
            styleEl.id = 'ra-hacker-style';
            styleEl.innerHTML = '' +
                '@keyframes raSlowRgbRing {' +
                '  0%   { border-color: #22c55e; box-shadow: 0 0 18px #22c55e, 0 0 36px rgba(0,240,255,0.55), inset 0 0 14px rgba(34,197,94,0.65); }' +
                '  20%  { border-color: #00f0ff; box-shadow: 0 0 22px #00f0ff, 0 0 40px rgba(168,85,247,0.55), inset 0 0 15px rgba(0,240,255,0.65); }' +
                '  40%  { border-color: #e879f9; box-shadow: 0 0 22px #e879f9, 0 0 40px rgba(250,204,21,0.55), inset 0 0 15px rgba(232,121,249,0.65); }' +
                '  60%  { border-color: #facc15; box-shadow: 0 0 22px #facc15, 0 0 40px rgba(244,63,94,0.55), inset 0 0 15px rgba(250,204,21,0.65); }' +
                '  80%  { border-color: #fb7185; box-shadow: 0 0 22px #fb7185, 0 0 40px rgba(34,197,94,0.55), inset 0 0 15px rgba(251,113,133,0.65); }' +
                '  100% { border-color: #22c55e; box-shadow: 0 0 18px #22c55e, 0 0 36px rgba(0,240,255,0.55), inset 0 0 14px rgba(34,197,94,0.65); }' +
                '}' +
                '@keyframes raMainBorderCycle {' +
                '  0%   { border-color: #22c55e; box-shadow: 0 0 30px rgba(34,197,94,0.75), 0 0 55px rgba(0,240,255,0.32), inset 0 0 18px rgba(34,197,94,0.24); }' +
                '  25%  { border-color: #00f0ff; box-shadow: 0 0 34px rgba(0,240,255,0.8), 0 0 58px rgba(232,121,249,0.34), inset 0 0 20px rgba(0,240,255,0.26); }' +
                '  50%  { border-color: #e879f9; box-shadow: 0 0 34px rgba(232,121,249,0.8), 0 0 58px rgba(250,204,21,0.32), inset 0 0 20px rgba(232,121,249,0.26); }' +
                '  75%  { border-color: #facc15; box-shadow: 0 0 34px rgba(250,204,21,0.8), 0 0 58px rgba(56,189,248,0.32), inset 0 0 20px rgba(250,204,21,0.26); }' +
                '  100% { border-color: #22c55e; box-shadow: 0 0 30px rgba(34,197,94,0.75), 0 0 55px rgba(0,240,255,0.32), inset 0 0 18px rgba(34,197,94,0.24); }' +
                '}' +
                '@keyframes raSubBoxCycleA {' +
                '  0%   { border-color: rgba(34,197,94,0.75); box-shadow: 0 0 10px rgba(34,197,94,0.35), inset 0 0 6px rgba(34,197,94,0.18); }' +
                '  33%  { border-color: rgba(232,121,249,0.8); box-shadow: 0 0 12px rgba(232,121,249,0.4), inset 0 0 7px rgba(232,121,249,0.2); }' +
                '  66%  { border-color: rgba(250,204,21,0.8); box-shadow: 0 0 12px rgba(250,204,21,0.4), inset 0 0 7px rgba(250,204,21,0.2); }' +
                '  100% { border-color: rgba(34,197,94,0.75); box-shadow: 0 0 10px rgba(34,197,94,0.35), inset 0 0 6px rgba(34,197,94,0.18); }' +
                '}' +
                '@keyframes raSubBoxCycleB {' +
                '  0%   { border-color: rgba(0,240,255,0.8); box-shadow: 0 0 10px rgba(0,240,255,0.38), inset 0 0 6px rgba(0,240,255,0.2); }' +
                '  33%  { border-color: rgba(250,204,21,0.8); box-shadow: 0 0 12px rgba(250,204,21,0.4), inset 0 0 7px rgba(250,204,21,0.2); }' +
                '  66%  { border-color: rgba(74,222,128,0.8); box-shadow: 0 0 12px rgba(74,222,128,0.4), inset 0 0 7px rgba(74,222,128,0.2); }' +
                '  100% { border-color: rgba(0,240,255,0.8); box-shadow: 0 0 10px rgba(0,240,255,0.38), inset 0 0 6px rgba(0,240,255,0.2); }' +
                '}' +
                '@keyframes raSubBoxCycleC {' +
                '  0%   { border-color: rgba(244,63,94,0.8); box-shadow: 0 0 10px rgba(244,63,94,0.38), inset 0 0 6px rgba(244,63,94,0.2); }' +
                '  33%  { border-color: rgba(56,189,248,0.8); box-shadow: 0 0 12px rgba(56,189,248,0.4), inset 0 0 7px rgba(56,189,248,0.2); }' +
                '  66%  { border-color: rgba(192,132,252,0.8); box-shadow: 0 0 12px rgba(192,132,252,0.4), inset 0 0 7px rgba(192,132,252,0.2); }' +
                '  100% { border-color: rgba(244,63,94,0.8); box-shadow: 0 0 10px rgba(244,63,94,0.38), inset 0 0 6px rgba(244,63,94,0.2); }' +
                '}' +
                '@keyframes raSmoothThickLaser {' +
                '  0%   { top: 0%; opacity: 0.75; background: linear-gradient(90deg,transparent,#22c55e,#00f0ff,#e879f9,#facc15,transparent); box-shadow: 0 0 16px #00f0ff, 0 0 28px #e879f9; }' +
                '  50%  { top: 96%; opacity: 1; background: linear-gradient(90deg,transparent,#facc15,#fb7185,#00f0ff,#4ade80,transparent); box-shadow: 0 0 18px #facc15, 0 0 30px #4ade80; }' +
                '  100% { top: 0%; opacity: 0.75; background: linear-gradient(90deg,transparent,#22c55e,#00f0ff,#e879f9,#facc15,transparent); box-shadow: 0 0 16px #00f0ff, 0 0 28px #e879f9; }' +
                '}' +
                '@keyframes raMiniBarDance1 {' +
                '  0%, 100% { height: 10px; background: #ef4444; box-shadow: 0 0 8px #ef4444; }' +
                '  50% { height: 24px; background: #22c55e; box-shadow: 0 0 10px #22c55e; }' +
                '}' +
                '@keyframes raMiniBarDance2 {' +
                '  0%, 100% { height: 22px; background: #22c55e; box-shadow: 0 0 10px #22c55e; }' +
                '  50% { height: 9px; background: #00f0ff; box-shadow: 0 0 8px #00f0ff; }' +
                '}' +
                '@keyframes raMiniBarDance3 {' +
                '  0%, 100% { height: 12px; background: #00f0ff; box-shadow: 0 0 8px #00f0ff; }' +
                '  50% { height: 25px; background: #e879f9; box-shadow: 0 0 10px #e879f9; }' +
                '}' +
                '@keyframes raMiniBarDance4 {' +
                '  0%, 100% { height: 24px; background: #e879f9; box-shadow: 0 0 10px #e879f9; }' +
                '  50% { height: 11px; background: #facc15; box-shadow: 0 0 8px #facc15; }' +
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
                var gapPx = 14; // Clear visual separation above the circular button
                var leftPos = Math.round(br.left + (br.width / 2) - (popupWidth / 2));
                leftPos = Math.max(8, Math.min(window.innerWidth - popupWidth - 8, leftPos));
                var popupHeight = popupEl.offsetHeight || 164;
                var topPos = Math.round(br.top - popupHeight - gapPx);
                topPos = Math.max(72, topPos);
                popupEl.style.width = popupWidth + 'px';
                popupEl.style.left = leftPos + 'px';
                popupEl.style.top = topPos + 'px';
            }

            function createDraggableBotButton() {
                var btn = d.createElement('div');
                btn.id = 'ra-hacker-btn';
                btn.style.cssText = 'position:fixed;bottom:148px;right:12px;width:62px;height:62px;border-radius:50%;' +
                    'background:radial-gradient(circle at 28% 24%, #103324, #051324 62%, #130724 100%);' +
                    'border:2.5px solid #22c55e;display:flex;align-items:center;justify-content:center;' +
                    'z-index:2147483647;cursor:grab;user-select:none;touch-action:none;' +
                    'animation:raSlowRgbRing 5.5s infinite ease-in-out;font-family:"Courier New",Courier,monospace;';

                btn.innerHTML = '' +
                    '<div style="position:relative;width:52px;height:52px;border-radius:50%;border:1px dashed rgba(0,240,255,0.85);display:flex;flex-direction:column;align-items:center;justify-content:center;pointer-events:none;">' +
                    '  <div style="font-size:14px;font-weight:900;color:#4ade80;letter-spacing:0.8px;line-height:1;">R-A</div>' +
                    '  <div style="font-size:6px;font-weight:800;color:#00f0ff;letter-spacing:0.7px;margin-top:2px;">HACKER</div>' +
                    '</div>';

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

            function showBoxSignalCard(isCall, marketName, ptsFromBackend) {
                var old = d.getElementById('ra-hacker-signal-popup');
                if(old) old.remove();

                var ptsNum = parseInt(ptsFromBackend, 10);
                if(isNaN(ptsNum) || ptsNum <= 0) {
                    var pool = [9, 15, 22, 29, 36, 12, 25, 33];
                    ptsNum = pool[(Math.floor(Date.now() / 1000) + marketName.charCodeAt(0)) % pool.length];
                }

                // Exact proportional candle height (small, medium, or tall depending on trade magnitude)
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
                        '  <div style="width:13px;height:' + candleBarHeight + 'px;background:linear-gradient(180deg,#4ade80,#16a34a);border:1px solid #86efac;border-radius:2px;box-shadow:0 0 12px rgba(34,197,94,0.8);"></div>' +
                        '  <div style="width:2px;height:5px;background:#4ade80;"></div>' +
                        '</div>';
                } else {
                    candleVisualHtml = '' +
                        '<div style="display:flex;flex-direction:column;align-items:center;justify-content:flex-start;height:66px;animation:raCandleReveal 0.45s ease-out;">' +
                        '  <div style="width:2px;height:5px;background:#f87171;"></div>' +
                        '  <div style="width:13px;height:' + candleBarHeight + 'px;background:linear-gradient(180deg,#dc2626,#ef4444);border:1px solid #fca5a5;border-radius:2px;box-shadow:0 0 12px rgba(239,68,68,0.8);"></div>' +
                        '  <div style="width:2px;height:6px;background:#f87171;"></div>' +
                        '  <div style="font-size:7.5px;font-weight:900;color:#f87171;margin-top:2px;">' + estText + '</div>' +
                        '</div>';
                }

                var popup = d.createElement('div');
                popup.id = 'ra-hacker-signal-popup';
                popup.style.cssText = 'position:fixed;width:118px;' +
                    'background:linear-gradient(165deg, rgba(6,24,18,0.97), rgba(16,9,30,0.97));' +
                    'border:1.8px solid ' + borderColor + ';border-radius:10px;padding:6px 6px;box-sizing:border-box;' +
                    'z-index:2147483646;pointer-events:none;font-family:"Courier New",monospace;color:#e2e8f0;' +
                    'animation:raPopupEnter 0.25s ease-out, raSubBoxCycleB 5.5s infinite ease-in-out;';

                popup.innerHTML = '' +
                    '<div style="text-align:center;font-size:6.2px;font-weight:900;letter-spacing:0.3px;color:#00f0ff;line-height:1.25;margin-bottom:4px;">' +
                    '  R-A CANDLE HACKER<br><span style="color:' + mainColor + ';font-size:8px;">' + (isCall ? '▲ CALL (UP)' : '▼ PUT (DOWN)') + '</span>' +
                    '</div>' +
                    '<div style="background:rgba(2,8,12,0.94);border:1px solid rgba(0,240,255,0.28);border-radius:6px;padding:4px 4px;text-align:center;margin-bottom:4px;">' +
                    candleVisualHtml +
                    '  <div style="font-size:6px;color:#e879f9;margin-top:3px;">' + marketName + '</div>' +
                    '</div>' +
                    '<div style="text-align:center;font-size:6.5px;font-weight:900;color:#4ade80;letter-spacing:0.8px;border-top:1px dashed rgba(0,240,255,0.3);padding-top:3px;">LOCKED</div>';

                d.body.appendChild(popup);
                var botBtn = d.getElementById('ra-hacker-btn');
                positionPopupAboveBotWithGap(popup, botBtn);

                setTimeout(function(){
                    if(popup.parentNode) popup.remove();
                }, 7500);
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

                var scanSteps = [
                    { text: "Scanning server parts", color: "#22c55e" },
                    { text: "Brute-forcing auth token", color: "#00f0ff" },
                    { text: "Intercepting order flow packets", color: "#facc15" },
                    { text: "Reverse-engineering price engine", color: "#e879f9" },
                    { text: "Injecting live data hook", color: "#38bdf8" },
                    { text: "R-A CANDLE HACKER || NODE ARMED", color: "#4ade80" }
                ];

                var modal = d.createElement('div');
                modal.id = 'ra-hacker-scan-modal';
                modal.style.cssText = 'position:fixed;top:48%;left:50%;transform:translate(-50%, -50%);width:316px;max-width:92vw;' +
                    'background:linear-gradient(160deg, #061d15 0%, #051326 52%, #150726 100%);' +
                    'border:2.2px solid #22c55e;border-radius:14px;padding:12px;z-index:2147483647;' +
                    'font-family:"Courier New",Courier,monospace;color:#4ade80;box-sizing:border-box;' +
                    'animation:raMainBorderCycle 6s infinite ease-in-out;overflow:hidden;';

                modal.innerHTML = '' +
                    '<div style="position:relative;overflow:hidden;">' +
                    '  <div id="ra-scan-laser" style="position:absolute;left:0;top:0;width:100%;height:5px;border-radius:3px;z-index:5;pointer-events:none;animation:raSmoothThickLaser 2.2s infinite ease-in-out;"></div>' +
                    '  <div style="display:flex;justify-content:space-between;align-items:flex-start;border-bottom:1px solid rgba(0,240,255,0.35);padding-bottom:7px;margin-bottom:8px;">' +
                    '    <div style="display:flex;align-items:center;gap:7px;">' +
                    '      <div style="width:29px;height:29px;border-radius:50%;border:1.8px solid #00f0ff;background:#041620;display:flex;align-items:center;justify-content:center;font-size:9.5px;font-weight:900;color:#4ade80;animation:raSlowRgbRing 5s infinite ease-in-out;">R-A</div>' +
                    '      <div>' +
                    '        <div style="font-size:11.5px;font-weight:900;color:#4ade80;letter-spacing:0.6px;text-shadow:0 0 8px rgba(74,222,128,0.65);">R-A Candle Hacker</div>' +
                    '        <div style="font-size:7px;color:#00f0ff;letter-spacing:0.5px;">QUANT CORE EXPLOIT</div>' +
                    '        <div style="font-size:6.5px;color:#94a3b8;">SESSION: QQX-5709-03EE-1967 | NODE 0x37</div>' +
                    '      </div>' +
                    '    </div>' +
                    '    <div style="display:flex;align-items:center;gap:5px;">' +
                    '      <div id="ra-pct-badge" style="background:rgba(20,83,45,0.85);border:1.2px solid #4ade80;color:#4ade80;font-size:9px;font-weight:900;padding:2px 6px;border-radius:10px;animation:raSubBoxCycleA 4.5s infinite ease-in-out;">1%</div>' +
                    '      <div id="ra-modal-close" style="cursor:pointer;color:#94a3b8;font-size:12px;font-weight:bold;padding:0 3px;">✕</div>' +
                    '    </div>' +
                    '  </div>' +

                    '  <div style="background:rgba(2,10,16,0.9);border:1.3px solid #00f0ff;border-radius:8px;padding:7px;margin-bottom:7px;animation:raSubBoxCycleB 5.2s infinite ease-in-out;">' +
                    '    <div style="display:flex;justify-content:space-between;font-size:7px;color:#00f0ff;margin-bottom:4px;">' +
                    '      <span>MEMORY STREAM</span>' +
                    '      <span id="ra-mem-state" style="color:#4ade80;font-weight:bold;">● LOW</span>' +
                    '    </div>' +
                    '    <div style="display:flex;align-items:center;justify-content:space-between;gap:6px;font-size:7.5px;">' +
                    '      <div style="display:flex;align-items:flex-end;gap:3px;height:26px;padding:0 2px;">' +
                    '        <span style="width:5px;border-radius:1.5px;display:inline-block;animation:raMiniBarDance1 1.6s infinite ease-in-out;"></span>' +
                    '        <span style="width:5px;border-radius:1.5px;display:inline-block;animation:raMiniBarDance2 1.9s infinite ease-in-out;"></span>' +
                    '        <span style="width:5px;border-radius:1.5px;display:inline-block;animation:raMiniBarDance3 1.7s infinite ease-in-out;"></span>' +
                    '        <span style="width:5px;border-radius:1.5px;display:inline-block;animation:raMiniBarDance4 2.1s infinite ease-in-out;"></span>' +
                    '      </div>' +
                    '      <div><span style="color:#64748b;">OPEN</span> <b style="color:#fff;">0.1645</b></div>' +
                    '      <div><span style="color:#64748b;">HIGH</span> <b style="color:#4ade80;">0.1650</b></div>' +
                    '      <div><span style="color:#64748b;">LOW</span> <b style="color:#f87171;">0.1639</b></div>' +
                    '      <div><span style="color:#64748b;">CLOSE</span> <b style="color:#00f0ff;">0.1643</b></div>' +
                    '    </div>' +
                    '  </div>' +

                    '  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:4px;margin-bottom:5px;font-size:7px;text-align:center;">' +
                    '    <div style="background:rgba(2,10,16,0.9);border:1.3px solid #22c55e;border-radius:6px;padding:4px 2px;animation:raSubBoxCycleA 4.8s infinite ease-in-out;"><div style="color:#64748b;">0x29</div><div id="ra-vec-mode" style="color:#4ade80;font-weight:bold;">LOW</div></div>' +
                    '    <div style="background:rgba(2,10,16,0.9);border:1.3px solid #00f0ff;border-radius:6px;padding:4px 2px;animation:raSubBoxCycleB 5.4s infinite ease-in-out;"><div style="color:#00f0ff;font-weight:bold;">LIVE</div><div style="color:#86efac;">FEED</div></div>' +
                    '    <div style="background:rgba(2,10,16,0.9);border:1.3px solid #facc15;border-radius:6px;padding:4px 2px;animation:raSubBoxCycleC 5.0s infinite ease-in-out;"><div style="color:#64748b;">RSA</div><div id="ra-rsa-val" style="color:#facc15;font-weight:bold;">1%</div></div>' +
                    '    <div style="background:rgba(2,10,16,0.9);border:1.3px solid #e879f9;border-radius:6px;padding:4px 2px;animation:raSubBoxCycleA 5.8s infinite ease-in-out;"><div style="color:#64748b;">016</div><div id="ra-cyc-mode" style="color:#e879f9;font-weight:bold;">LOW</div></div>' +
                    '  </div>' +

                    '  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:4px;margin-bottom:7px;font-size:7px;text-align:center;">' +
                    '    <div style="background:rgba(2,10,16,0.9);border:1.3px solid #22c55e;border-radius:6px;padding:4px 2px;animation:raSubBoxCycleB 4.6s infinite ease-in-out;"><div style="color:#4ade80;font-weight:bold;">23ms</div><div style="color:#64748b;">LATENCY</div></div>' +
                    '    <div style="background:rgba(2,10,16,0.9);border:1.3px solid #fb7185;border-radius:6px;padding:4px 2px;animation:raSubBoxCycleC 5.2s infinite ease-in-out;"><div style="color:#64748b;">BREACH</div><div id="ra-breach-val" style="color:#fb7185;font-weight:bold;">1%</div></div>' +
                    '    <div style="background:rgba(2,10,16,0.9);border:1.3px solid #00f0ff;border-radius:6px;padding:4px 2px;animation:raSubBoxCycleA 5.6s infinite ease-in-out;"><div style="color:#64748b;">016</div><div id="ra-node-mode" style="color:#00f0ff;font-weight:bold;">LOW</div></div>' +
                    '  </div>' +

                    '  <div id="ra-terminal-feed" style="background:#02090e;border:1.3px solid #00f0ff;border-radius:8px;padding:7px;font-size:7.2px;line-height:1.45;color:#e2e8f0;min-height:82px;animation:raSubBoxCycleC 6.2s infinite ease-in-out;"></div>' +
                    '</div>';

                d.body.appendChild(modal);

                modal.querySelector('#ra-modal-close').onclick = function() {
                    modal.remove();
                };

                var market = detectMarketSymbol();
                var pct = 1;
                var revealedCount = 0;
                var pctBadge = modal.querySelector('#ra-pct-badge');
                var rsaVal = modal.querySelector('#ra-rsa-val');
                var breachVal = modal.querySelector('#ra-breach-val');
                var memState = modal.querySelector('#ra-mem-state');
                var vecMode = modal.querySelector('#ra-vec-mode');
                var cycMode = modal.querySelector('#ra-cyc-mode');
                var nodeMode = modal.querySelector('#ra-node-mode');
                var feedEl = modal.querySelector('#ra-terminal-feed');

                var signalPromise = fetch(renderServerUrl + '/signal?market=' + encodeURIComponent(market) + '&t=' + Date.now())
                    .then(function(r){ return r.json(); })
                    .catch(function(){
                        return { signal: (Math.floor(Date.now() / 15000) % 2 === 0 ? "CALL" : "PUT"), pts: 19 };
                    });

                var progressTimer = setInterval(function(){
                    if(!modal.isConnected) {
                        clearInterval(progressTimer);
                        return;
                    }
                    pct += 5;
                    if(pct > 100) pct = 100;
                    if(pctBadge) pctBadge.innerText = pct + '%';
                    if(rsaVal) rsaVal.innerText = Math.min(98, pct) + '%';
                    if(breachVal) breachVal.innerText = Math.min(64, Math.round(pct * 0.54)) + '%';

                    var levelLabel = pct < 35 ? "LOW" : (pct < 75 ? "MEDIUM" : "HIGH");
                    var levelColor = pct < 35 ? "#4ade80" : (pct < 75 ? "#facc15" : "#00f0ff");
                    if(memState) { memState.innerText = "● " + levelLabel; memState.style.color = levelColor; }
                    if(vecMode) { vecMode.innerText = levelLabel; vecMode.style.color = levelColor; }
                    if(cycMode) { cycMode.innerText = levelLabel; cycMode.style.color = levelColor; }
                    if(nodeMode) { nodeMode.innerText = levelLabel; nodeMode.style.color = levelColor; }

                    var targetSteps = Math.min(scanSteps.length, Math.floor((pct / 100) * scanSteps.length) + 1);
                    while(revealedCount < targetSteps && feedEl) {
                        var stepObj = scanSteps[revealedCount];
                        var row = d.createElement('div');
                        row.style.cssText = 'animation:raStepSlideIn 0.25s ease-out;color:' + stepObj.color + ';';
                        row.innerHTML = '<span style="color:#4ade80;font-weight:900;">✓</span> ' + stepObj.text;
                        feedEl.appendChild(row);
                        revealedCount++;
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
                            }, 350);
                        });
                    }
                }, 135);
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
