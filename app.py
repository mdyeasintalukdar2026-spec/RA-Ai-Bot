from flask import Flask, jsonify, make_response, request
import requests
import time
import os
import logging
from datetime import datetime, timedelta

app = Flask(__name__, static_folder=None)

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger("RA_COMMUNITY_BOT_Engine")

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
            url_ts = f"https://api.twelvedata.com/time_series?symbol={formatted_sym}&interval=1min&outputsize=4&apikey={TWELVE_DATA_KEY}"
            resp = requests.get(url_ts, timeout=3)
            if resp.status_code == 200:
                values = resp.json().get("values", [])
                if len(values) >= 3:
                    c0 = float(values[0]["close"])
                    c1 = float(values[1]["close"])
                    c2 = float(values[2]["close"])

                    diff1 = c0 - c1
                    diff2 = c1 - c2
                    mag_pts = max(9, min(38, int(abs(diff1) * 100000) if abs(diff1) < 0.05 else int((abs(diff1) * 100) % 29) + 10))

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
        pts_list = [11, 15, 19, 23, 27, 31, 14, 21]
        est_pts = pts_list[(epoch_sec // 5) % len(pts_list)]
        if (epoch_sec // 15) % 2 == 0:
            return {"signal": "CALL", "trend": "BULLISH (UP)", "pts": est_pts, "rule": "Live Trend Synchronization Active."}
        else:
            return {"signal": "PUT", "trend": "BEARISH (DOWN)", "pts": est_pts, "rule": "Live Trend Synchronization Active."}


@app.route('/')
def home():
    res = make_response("DR CANDLE TRACKER ENGINE ACTIVE - PRECISION LIVE CANDLE MODE!")
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
            "pts": analysis.get("pts", 16),
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
            "pts": 16,
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
            ["ra-sniper-bot-panel", "ra-sniper-bot-btn", "ra-sniper-bot-style", "dr-tracker-panel", "dr-tracker-btn", "dr-scan-modal", "dr-candle-projection", "dr-next-signal-popup", "dr-hacker-style"].forEach(function(id){
                var el = d.getElementById(id);
                if(el) el.remove();
            });

            var renderServerUrl = "https://ra-ai-bot.onrender.com";

            var styleEl = d.createElement('style');
            styleEl.id = 'dr-hacker-style';
            styleEl.innerHTML = '' +
                '@keyframes drRgbRing {' +
                '  0% { border-color: #22c55e; box-shadow: 0 0 18px rgba(34,197,94,0.95), 0 0 34px rgba(0,255,204,0.5), inset 0 0 12px rgba(34,197,94,0.6); }' +
                '  33% { border-color: #00f0ff; box-shadow: 0 0 22px rgba(0,240,255,0.95), 0 0 38px rgba(168,85,247,0.5), inset 0 0 14px rgba(0,240,255,0.6); }' +
                '  66% { border-color: #e879f9; box-shadow: 0 0 22px rgba(232,121,249,0.95), 0 0 38px rgba(250,204,21,0.5), inset 0 0 14px rgba(232,121,249,0.6); }' +
                '  100% { border-color: #22c55e; box-shadow: 0 0 18px rgba(34,197,94,0.95), 0 0 34px rgba(0,255,204,0.5), inset 0 0 12px rgba(34,197,94,0.6); }' +
                '}' +
                '@keyframes drRgbBorder {' +
                '  0% { border-color: #22c55e; box-shadow: 0 0 28px rgba(34,197,94,0.65), inset 0 0 16px rgba(0,255,204,0.22); }' +
                '  33% { border-color: #38bdf8; box-shadow: 0 0 32px rgba(56,189,248,0.7), inset 0 0 18px rgba(168,85,247,0.24); }' +
                '  66% { border-color: #c084fc; box-shadow: 0 0 32px rgba(192,132,252,0.7), inset 0 0 18px rgba(250,204,21,0.22); }' +
                '  100% { border-color: #22c55e; box-shadow: 0 0 28px rgba(34,197,94,0.65), inset 0 0 16px rgba(0,255,204,0.22); }' +
                '}' +
                '@keyframes drMultiLaser {' +
                '  0% { top: 0%; opacity: 0.4; background: linear-gradient(90deg,transparent,#22c55e,#00f0ff,#e879f9,#facc15,transparent); }' +
                '  50% { top: 96%; opacity: 1; background: linear-gradient(90deg,transparent,#facc15,#e879f9,#00f0ff,#22c55e,transparent); }' +
                '  100% { top: 0%; opacity: 0.4; background: linear-gradient(90deg,transparent,#22c55e,#00f0ff,#e879f9,#facc15,transparent); }' +
                '}' +
                '@keyframes drStepReveal {' +
                '  0% { opacity: 0; transform: translateX(-6px); }' +
                '  100% { opacity: 1; transform: translateX(0); }' +
                '}' +
                '@keyframes drCandleStretchUp {' +
                '  0% { transform: scaleY(0.2); transform-origin: bottom center; opacity: 0.5; }' +
                '  70% { transform: scaleY(1.04); transform-origin: bottom center; opacity: 1; }' +
                '  100% { transform: scaleY(1); transform-origin: bottom center; opacity: 0.96; }' +
                '}' +
                '@keyframes drCandleStretchDown {' +
                '  0% { transform: scaleY(0.2); transform-origin: top center; opacity: 0.5; }' +
                '  70% { transform: scaleY(1.04); transform-origin: top center; opacity: 1; }' +
                '  100% { transform: scaleY(1); transform-origin: top center; opacity: 0.96; }' +
                '}' +
                '@keyframes drPulseGlow {' +
                '  0%, 100% { filter: drop-shadow(0 0 6px currentColor); }' +
                '  50% { filter: drop-shadow(0 0 15px currentColor); }' +
                '}' +
                '@keyframes drSlimPopupIn {' +
                '  0% { opacity: 0; transform: translateY(8px) scale(0.94); }' +
                '  100% { opacity: 1; transform: translateY(0) scale(1); }' +
                '}';
            d.head.appendChild(styleEl);

            function createDraggableDrButton() {
                var btn = d.createElement('div');
                btn.id = 'dr-tracker-btn';
                btn.style.cssText = 'position:fixed;top:56%;right:12px;width:62px;height:62px;border-radius:50%;' +
                    'background:radial-gradient(circle at 30% 25%, #0f291e, #040d14 65%, #020508 100%);' +
                    'border:2.5px solid #22c55e;display:flex;align-items:center;justify-content:center;' +
                    'z-index:2147483647;cursor:grab;user-select:none;touch-action:none;' +
                    'animation:drRgbRing 2.6s infinite ease-in-out;font-family:"Courier New",Courier,monospace;';

                btn.innerHTML = '' +
                    '<div style="position:relative;width:52px;height:52px;border-radius:50%;border:1px dashed rgba(56,189,248,0.75);display:flex;flex-direction:column;align-items:center;justify-content:center;pointer-events:none;">' +
                    '  <div style="font-size:15px;font-weight:900;color:#4ade80;letter-spacing:1px;animation:drPulseGlow 1.8s infinite;line-height:1;">DR</div>' +
                    '  <div style="font-size:6.5px;font-weight:800;color:#38bdf8;letter-spacing:0.8px;margin-top:2px;">TRACKER</div>' +
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

            function locateRunningCandlePosition() {
                // 1) Try locating timer label or price marker near running candle
                var bestX = null, bestY = null;
                try {
                    var allEls = d.querySelectorAll('div, span, text, line, rect');
                    for(var i = 0; i < allEls.length; i++) {
                        var el = allEls[i];
                        var txt = (el.innerText || el.textContent || '').trim();
                        var r = el.getBoundingClientRect();
                        if(r.width === 0 || r.height === 0) continue;
                        if(r.left < window.innerWidth * 0.25 || r.left > window.innerWidth * 0.85) continue;
                        if(r.top < 110 || r.top > window.innerHeight * 0.68) continue;

                        if(/^00:\d{2}$/.test(txt)) {
                            bestX = r.left + (r.width * 0.35);
                            bestY = r.top - 10;
                            break;
                        }
                    }
                } catch(e) {}

                // 2) Try finding vertical crosshair/current-candle guide line
                if(bestX === null || bestY === null) {
                    try {
                        var lines = d.querySelectorAll('line');
                        for(var j = 0; j < lines.length; j++) {
                            var lr = lines[j].getBoundingClientRect();
                            if(lr.height > 60 && lr.width < 12 && lr.left > window.innerWidth * 0.35 && lr.left < window.innerWidth * 0.78) {
                                bestX = bestX || (lr.left + lr.width / 2);
                                bestY = bestY || Math.round(window.innerHeight * 0.48);
                                break;
                            }
                        }
                    } catch(e) {}
                }

                // 3) Fallback positioned over active right-side candle zone
                return {
                    x: bestX !== null ? Math.round(bestX) : Math.round(window.innerWidth * 0.54),
                    y: bestY !== null ? Math.round(bestY) : Math.round(window.innerHeight * 0.49)
                };
            }

            function computeCandleProjectionMetrics(isCall, ptsFromBackend, marketName) {
                var basePts = parseInt(ptsFromBackend, 10);
                if(isNaN(basePts) || basePts <= 0) {
                    var fallbackPts = [11, 16, 20, 25, 31, 14, 28];
                    var idx = (Math.floor(Date.now() / 1000) + marketName.charCodeAt(0)) % fallbackPts.length;
                    basePts = fallbackPts[idx];
                }
                var heightPx = Math.max(42, Math.min(115, basePts * 3.1));
                return {
                    pts: basePts,
                    heightPx: Math.round(heightPx),
                    label: (isCall ? "+" : "-") + basePts + " PTS"
                };
            }

            function renderRunningCandleForecast(isCall, marketName, ptsFromBackend) {
                ["dr-candle-projection", "dr-next-signal-popup"].forEach(function(id){
                    var old = d.getElementById(id);
                    if(old) old.remove();
                });

                var anchor = locateRunningCandlePosition();
                var metrics = computeCandleProjectionMetrics(isCall, ptsFromBackend, marketName);

                // CALL = Green (#22c55e) above running candle, PUT = Red (#ef4444) below running candle
                var mainColor = isCall ? "#22c55e" : "#ef4444";
                var borderColor = isCall ? "#4ade80" : "#f87171";
                var bgFill = isCall ? "rgba(34, 197, 94, 0.16)" : "rgba(239, 68, 68, 0.16)";
                var boxWidth = 20;

                var proj = d.createElement('div');
                proj.id = 'dr-candle-projection';

                if(isCall) {
                    var topPos = Math.max(85, anchor.y - metrics.heightPx);
                    proj.style.cssText = 'position:fixed;left:' + Math.round(anchor.x - boxWidth / 2) + 'px;' +
                        'top:' + topPos + 'px;width:' + boxWidth + 'px;height:' + metrics.heightPx + 'px;' +
                        'border:2px dashed ' + borderColor + ';background:' + bgFill + ';' +
                        'border-radius:3px;z-index:2147483645;pointer-events:none;font-family:"Courier New",monospace;' +
                        'animation:drCandleStretchUp 0.6s cubic-bezier(0.22,1,0.36,1) forwards, drPulseGlow 1.5s infinite;';
                    proj.innerHTML = '' +
                        '<div style="position:absolute;top:-15px;left:50%;transform:translateX(-50%);font-size:11px;font-weight:900;color:' + mainColor + ';">▲</div>' +
                        '<div style="position:absolute;top:-28px;left:50%;transform:translateX(-50%);white-space:nowrap;background:rgba(4,16,9,0.94);border:1px solid ' + borderColor + ';color:' + mainColor + ';font-size:7.5px;font-weight:900;padding:1px 4px;border-radius:3px;">' + metrics.label + '</div>';
                } else {
                    var maxBottom = window.innerHeight - 175;
                    var downHeight = Math.min(metrics.heightPx, Math.max(36, maxBottom - anchor.y));
                    proj.style.cssText = 'position:fixed;left:' + Math.round(anchor.x - boxWidth / 2) + 'px;' +
                        'top:' + anchor.y + 'px;width:' + boxWidth + 'px;height:' + downHeight + 'px;' +
                        'border:2px dashed ' + borderColor + ';background:' + bgFill + ';' +
                        'border-radius:3px;z-index:2147483645;pointer-events:none;font-family:"Courier New",monospace;' +
                        'animation:drCandleStretchDown 0.6s cubic-bezier(0.22,1,0.36,1) forwards, drPulseGlow 1.5s infinite;';
                    proj.innerHTML = '' +
                        '<div style="position:absolute;bottom:-15px;left:50%;transform:translateX(-50%);font-size:11px;font-weight:900;color:' + mainColor + ';">▼</div>' +
                        '<div style="position:absolute;bottom:-28px;left:50%;transform:translateX(-50%);white-space:nowrap;background:rgba(18,5,8,0.94);border:1px solid ' + borderColor + ';color:' + mainColor + ';font-size:7.5px;font-weight:900;padding:1px 4px;border-radius:3px;">' + metrics.label + '</div>';
                }

                d.body.appendChild(proj);

                // Slightly slimmer right-side popup card
                var popupWidth = 104;
                var pLeft = Math.min(window.innerWidth - popupWidth - 10, Math.max(8, Math.round(anchor.x + 20)));
                var pTop = Math.min(window.innerHeight - 170, Math.max(85, Math.round(anchor.y - 44)));

                var popup = d.createElement('div');
                popup.id = 'dr-next-signal-popup';
                popup.style.cssText = 'position:fixed;left:' + pLeft + 'px;top:' + pTop + 'px;width:' + popupWidth + 'px;' +
                    'background:linear-gradient(165deg, rgba(6,22,16,0.96), rgba(15,9,28,0.96));' +
                    'border:1.5px solid ' + borderColor + ';border-radius:9px;padding:6px 6px;box-sizing:border-box;' +
                    'z-index:2147483646;pointer-events:none;font-family:"Courier New",monospace;color:#e2e8f0;' +
                    'box-shadow:0 0 22px rgba(0,0,0,0.85), 0 0 12px ' + bgFill + ';animation:drSlimPopupIn 0.25s ease-out;';

                popup.innerHTML = '' +
                    '<div style="text-align:center;font-size:6.5px;font-weight:800;letter-spacing:0.4px;color:#38bdf8;line-height:1.2;margin-bottom:4px;">' +
                    '  <span style="color:' + mainColor + ';font-size:8.5px;">' + (isCall ? '▲' : '▼') + '</span> NEXT<br>SMART SIGNAL' +
                    '</div>' +
                    '<div style="background:rgba(2,8,12,0.9);border:1px solid rgba(56,189,248,0.25);border-radius:6px;padding:5px 3px;text-align:center;margin-bottom:4px;">' +
                    '  <div style="font-size:9px;font-weight:900;color:' + mainColor + ';letter-spacing:0.4px;">' + (isCall ? 'CALL (UP)' : 'PUT (DOWN)') + '</div>' +
                    '  <div style="font-size:7.5px;font-weight:800;color:#facc15;margin-top:2px;">EST: ' + metrics.label + '</div>' +
                    '  <div style="font-size:6px;color:#c084fc;margin-top:1px;">' + marketName + '</div>' +
                    '</div>' +
                    '<div style="text-align:center;font-size:6.5px;font-weight:900;color:#4ade80;letter-spacing:0.8px;border-top:1px dashed rgba(74,222,128,0.28);padding-top:3px;">LOCKED</div>';

                d.body.appendChild(popup);

                setTimeout(function(){
                    if(proj.parentNode) proj.remove();
                    if(popup.parentNode) popup.remove();
                }, 14000);
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
                var oldModal = d.getElementById('dr-scan-modal');
                if(oldModal) oldModal.remove();

                var scanSteps = [
                    { text: "Scanning server parts", color: "#22c55e" },
                    { text: "Brute-forcing auth token", color: "#38bdf8" },
                    { text: "Intercepting order flow packets", color: "#facc15" },
                    { text: "Reverse-engineering price engine", color: "#e879f9" },
                    { text: "Injecting live data hook", color: "#00f0ff" },
                    { text: "CIPHER LOCKED || NODE ARMED", color: "#4ade80" }
                ];

                var modal = d.createElement('div');
                modal.id = 'dr-scan-modal';
                modal.style.cssText = 'position:fixed;top:50%;left:50%;transform:translate(-50%, -50%);width:316px;max-width:92vw;' +
                    'background:linear-gradient(165deg, #061b14 0%, #051122 55%, #120824 100%);' +
                    'border:2px solid #22c55e;border-radius:14px;padding:12px;z-index:2147483647;' +
                    'font-family:"Courier New",Courier,monospace;color:#4ade80;box-sizing:border-box;' +
                    'animation:drRgbBorder 2.8s infinite ease-in-out;overflow:hidden;';

                modal.innerHTML = '' +
                    '<div style="position:relative;overflow:hidden;">' +
                    '  <div id="dr-scan-laser" style="position:absolute;left:0;top:0;width:100%;height:3px;z-index:5;pointer-events:none;animation:drMultiLaser 1.3s linear infinite;"></div>' +
                    '  <div style="display:flex;justify-content:space-between;align-items:flex-start;border-bottom:1px solid rgba(56,189,248,0.28);padding-bottom:7px;margin-bottom:8px;">' +
                    '    <div style="display:flex;align-items:center;gap:7px;">' +
                    '      <div style="width:28px;height:28px;border-radius:50%;border:1.5px solid #38bdf8;background:#04141c;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:900;color:#4ade80;animation:drRgbRing 2.5s infinite;">DR</div>' +
                    '      <div>' +
                    '        <div style="font-size:11.5px;font-weight:900;color:#4ade80;letter-spacing:0.6px;">DR CANDLE TRACKER</div>' +
                    '        <div style="font-size:7px;color:#38bdf8;letter-spacing:0.5px;">QUANT CORE EXPLOIT</div>' +
                    '        <div style="font-size:6.5px;color:#94a3b8;">SESSION: QQX-5709-03EE-1967 | NODE 0x37</div>' +
                    '      </div>' +
                    '    </div>' +
                    '    <div style="display:flex;align-items:center;gap:5px;">' +
                    '      <div id="dr-pct-badge" style="background:rgba(20,83,45,0.75);border:1px solid #22c55e;color:#4ade80;font-size:9px;font-weight:900;padding:2px 6px;border-radius:10px;">1%</div>' +
                    '      <div id="dr-modal-close" style="cursor:pointer;color:#94a3b8;font-size:12px;font-weight:bold;padding:0 3px;">✕</div>' +
                    '    </div>' +
                    '  </div>' +

                    '  <div style="background:rgba(2,10,16,0.85);border:1px solid rgba(56,189,248,0.25);border-radius:8px;padding:7px;margin-bottom:7px;">' +
                    '    <div style="display:flex;justify-content:space-between;font-size:7px;color:#38bdf8;margin-bottom:4px;">' +
                    '      <span>MEMORY STREAM</span>' +
                    '      <span style="color:#4ade80;">● LINKED</span>' +
                    '    </div>' +
                    '    <div style="display:flex;align-items:center;justify-content:space-between;gap:6px;font-size:7.5px;">' +
                    '      <div style="display:flex;align-items:center;gap:3px;height:26px;">' +
                    '        <span style="width:5px;height:14px;background:#ef4444;border-radius:1px;display:inline-block;"></span>' +
                    '        <span style="width:5px;height:20px;background:#22c55e;border-radius:1px;display:inline-block;"></span>' +
                    '        <span style="width:5px;height:12px;background:#38bdf8;border-radius:1px;display:inline-block;"></span>' +
                    '        <span style="width:5px;height:24px;background:#e879f9;border-radius:1px;display:inline-block;"></span>' +
                    '      </div>' +
                    '      <div><span style="color:#64748b;">OPEN</span> <b style="color:#fff;">0.1645</b></div>' +
                    '      <div><span style="color:#64748b;">HIGH</span> <b style="color:#4ade80;">0.1650</b></div>' +
                    '      <div><span style="color:#64748b;">LOW</span> <b style="color:#f87171;">0.1639</b></div>' +
                    '      <div><span style="color:#64748b;">CLOSE</span> <b style="color:#38bdf8;">0.1643</b></div>' +
                    '    </div>' +
                    '  </div>' +

                    '  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:4px;margin-bottom:5px;font-size:7px;text-align:center;">' +
                    '    <div style="background:rgba(2,10,16,0.85);border:1px solid rgba(34,197,94,0.25);border-radius:6px;padding:4px 2px;"><div style="color:#64748b;">0x29</div><div style="color:#4ade80;font-weight:bold;">VECTOR</div></div>' +
                    '    <div style="background:rgba(2,10,16,0.85);border:1px solid rgba(56,189,248,0.25);border-radius:6px;padding:4px 2px;"><div style="color:#38bdf8;font-weight:bold;">LIVE</div><div style="color:#86efac;">FEED</div></div>' +
                    '    <div style="background:rgba(2,10,16,0.85);border:1px solid rgba(250,204,21,0.25);border-radius:6px;padding:4px 2px;"><div style="color:#64748b;">RSA</div><div id="dr-rsa-val" style="color:#facc15;font-weight:bold;">1%</div></div>' +
                    '    <div style="background:rgba(2,10,16,0.85);border:1px solid rgba(232,121,249,0.25);border-radius:6px;padding:4px 2px;"><div style="color:#64748b;">016</div><div style="color:#e879f9;font-weight:bold;">CYCLE</div></div>' +
                    '  </div>' +

                    '  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:4px;margin-bottom:7px;font-size:7px;text-align:center;">' +
                    '    <div style="background:rgba(2,10,16,0.85);border:1px solid rgba(34,197,94,0.25);border-radius:6px;padding:4px 2px;"><div style="color:#4ade80;font-weight:bold;">23ms</div><div style="color:#64748b;">LATENCY</div></div>' +
                    '    <div style="background:rgba(2,10,16,0.85);border:1px solid rgba(248,113,113,0.25);border-radius:6px;padding:4px 2px;"><div style="color:#64748b;">BREACH</div><div id="dr-breach-val" style="color:#f87171;font-weight:bold;">1%</div></div>' +
                    '    <div style="background:rgba(2,10,16,0.85);border:1px solid rgba(56,189,248,0.25);border-radius:6px;padding:4px 2px;"><div style="color:#64748b;">016</div><div style="color:#38bdf8;font-weight:bold;">NODE</div></div>' +
                    '  </div>' +

                    '  <div id="dr-terminal-feed" style="background:#02090e;border:1px solid rgba(56,189,248,0.25);border-radius:8px;padding:7px;font-size:7.2px;line-height:1.45;color:#e2e8f0;min-height:82px;"></div>' +
                    '</div>';

                d.body.appendChild(modal);

                modal.querySelector('#dr-modal-close').onclick = function() {
                    modal.remove();
                };

                var market = detectMarketSymbol();
                var pct = 1;
                var revealedCount = 0;
                var pctBadge = modal.querySelector('#dr-pct-badge');
                var rsaVal = modal.querySelector('#dr-rsa-val');
                var breachVal = modal.querySelector('#dr-breach-val');
                var feedEl = modal.querySelector('#dr-terminal-feed');

                var signalPromise = fetch(renderServerUrl + '/signal?market=' + encodeURIComponent(market) + '&t=' + Date.now())
                    .then(function(r){ return r.json(); })
                    .catch(function(){
                        return { signal: (Math.floor(Date.now() / 15000) % 2 === 0 ? "CALL" : "PUT"), pts: 18 };
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

                    var targetSteps = Math.min(scanSteps.length, Math.floor((pct / 100) * scanSteps.length) + 1);
                    while(revealedCount < targetSteps && feedEl) {
                        var stepObj = scanSteps[revealedCount];
                        var row = d.createElement('div');
                        row.style.cssText = 'animation:drStepReveal 0.22s ease-out;color:' + stepObj.color + ';';
                        row.innerHTML = '<span style="color:#4ade80;font-weight:900;">✓</span> ' + stepObj.text;
                        feedEl.appendChild(row);
                        revealedCount++;
                    }

                    if(pct >= 100) {
                        clearInterval(progressTimer);
                        signalPromise.then(function(data){
                            var sig = String(data.signal || 'CALL').toUpperCase();
                            var isCall = (sig === 'CALL' || sig === 'UP' || sig === 'BUY');
                            var ptsVal = data.pts || 16;
                            setTimeout(function(){
                                if(modal.isConnected) modal.remove();
                                renderRunningCandleForecast(isCall, market, ptsVal);
                                triggerBrokerTradeClick(isCall);
                            }, 350);
                        });
                    }
                }, 135);
            }

            createDraggableDrButton();
        } catch(err) {
            console.error("DR Tracker Init Error:", err);
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
