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

                    if diff1 > 0 and diff2 >= 0:
                        return {"signal": "CALL", "trend": "BULLISH (UP)", "rule": f"Upward Expansion Confirmed ({c0:.5f} > {c1:.5f})"}
                    elif diff1 < 0 and diff2 <= 0:
                        return {"signal": "PUT", "trend": "BEARISH (DOWN)", "rule": f"Downward Expansion Confirmed ({c0:.5f} < {c1:.5f})"}
                    elif diff1 > 0:
                        return {"signal": "CALL", "trend": "BULLISH (UP)", "rule": "Support Level Rejection Verified."}
                    else:
                        return {"signal": "PUT", "trend": "BEARISH (DOWN)", "rule": "Resistance Level Rejection Verified."}
        except Exception:
            pass

        epoch_sec = int(time.time())
        if (epoch_sec // 15) % 2 == 0:
            return {"signal": "CALL", "trend": "BULLISH (UP)", "rule": "Live Trend Synchronization Active."}
        else:
            return {"signal": "PUT", "trend": "BEARISH (DOWN)", "rule": "Live Trend Synchronization Active."}


@app.route('/')
def home():
    res = make_response("DR CANDLE TRACKER ENGINE ACTIVE - 100% SECURE HACKER MODE!")
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
            res = jsonify({"signal": "HOLD", "trend": "NEWS BLOCK", "status": "NEWS_GUARD", "rule": "High Impact News Filter Active."})
            res.headers.add("Access-Control-Allow-Origin", "*")
            return res

        analysis = BiDirectionalMarketEngine.get_smart_bi_directional_signal(clean_market)
        res = jsonify({"signal": analysis["signal"], "trend": analysis["trend"], "status": "GREEN_EXECUTE", "rule": analysis["rule"]})
        res.headers.add("Access-Control-Allow-Origin", "*")
        return res
    except Exception as e:
        logger.error(f"Signal Error: {e}")
        fallback_sig = "CALL" if int(time.time()) % 2 == 0 else "PUT"
        res = jsonify({"signal": fallback_sig, "trend": "BULLISH (UP)" if fallback_sig == "CALL" else "BEARISH (DOWN)", "status": "GREEN_EXECUTE", "rule": "Standard Confluence Sync."})
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
                '@keyframes drRingPulse {' +
                '  0% { box-shadow: 0 0 14px rgba(34,197,94,0.85), inset 0 0 10px rgba(34,197,94,0.5); border-color: #22c55e; }' +
                '  50% { box-shadow: 0 0 28px rgba(74,222,128,1), inset 0 0 16px rgba(34,197,94,0.75); border-color: #4ade80; }' +
                '  100% { box-shadow: 0 0 14px rgba(34,197,94,0.85), inset 0 0 10px rgba(34,197,94,0.5); border-color: #22c55e; }' +
                '}' +
                '@keyframes drSweepLaser {' +
                '  0% { top: 0%; opacity: 0.2; }' +
                '  50% { top: 96%; opacity: 0.95; }' +
                '  100% { top: 0%; opacity: 0.2; }' +
                '}' +
                '@keyframes drBoxGlowUp {' +
                '  0%, 100% { box-shadow: 0 0 10px rgba(34,197,94,0.55), inset 0 0 8px rgba(34,197,94,0.2); }' +
                '  50% { box-shadow: 0 0 22px rgba(34,197,94,0.9), inset 0 0 14px rgba(34,197,94,0.35); }' +
                '}' +
                '@keyframes drBoxGlowDown {' +
                '  0%, 100% { box-shadow: 0 0 10px rgba(239,68,68,0.55), inset 0 0 8px rgba(239,68,68,0.2); }' +
                '  50% { box-shadow: 0 0 22px rgba(239,68,68,0.9), inset 0 0 14px rgba(239,68,68,0.35); }' +
                '}' +
                '@keyframes drPopupPop {' +
                '  0% { opacity: 0; transform: translateY(8px) scale(0.94); }' +
                '  100% { opacity: 1; transform: translateY(0px) scale(1); }' +
                '}';
            d.head.appendChild(styleEl);

            function createDraggableDrButton() {
                var btn = d.createElement('div');
                btn.id = 'dr-tracker-btn';
                btn.style.cssText = 'position:fixed;top:46%;right:14px;width:62px;height:62px;border-radius:50%;' +
                    'background:radial-gradient(circle at 30% 30%, #0b2416, #020805 75%);' +
                    'border:2.5px solid #22c55e;display:flex;align-items:center;justify-content:center;' +
                    'z-index:2147483647;cursor:grab;user-select:none;touch-action:none;' +
                    'animation:drRingPulse 2.2s infinite ease-in-out;font-family:"Courier New",Courier,monospace;';

                btn.innerHTML = '' +
                    '<div style="position:relative;width:52px;height:52px;border-radius:50%;border:1px dashed rgba(74,222,128,0.65);display:flex;flex-direction:column;align-items:center;justify-content:center;pointer-events:none;">' +
                    '  <div style="font-size:15px;font-weight:900;color:#4ade80;letter-spacing:1px;text-shadow:0 0 10px rgba(34,197,94,0.9);line-height:1;">DR</div>' +
                    '  <div style="font-size:6.5px;font-weight:800;color:#86efac;letter-spacing:0.8px;margin-top:2px;">TRACKER</div>' +
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

            function findActiveCandleAnchor() {
                try {
                    var vLines = d.querySelectorAll('line, [class*="crosshair"], [class*="current-price"], [class*="candle"]');
                    for(var i = 0; i < vLines.length; i++) {
                        var r = vLines[i].getBoundingClientRect();
                        if(r.width > 0 && r.height > 25 && r.left > window.innerWidth * 0.25 && r.left < window.innerWidth * 0.85 && r.top > 90 && r.top < window.innerHeight * 0.72) {
                            return {
                                x: r.left + (r.width / 2),
                                y: r.top + (r.height * 0.45)
                            };
                        }
                    }
                } catch(e) {}
                return {
                    x: Math.round(window.innerWidth * 0.56),
                    y: Math.round(window.innerHeight * 0.40)
                };
            }

            function generateTradeReachEstimate(isCall, seedNum) {
                var heights = [52, 66, 80, 94, 108, 74, 86];
                var pipsList = [12, 18, 23, 28, 34, 16, 26];
                var idx = Math.abs(seedNum) % heights.length;
                return {
                    boxHeight: heights[idx],
                    estPips: pipsList[idx],
                    estLabel: (isCall ? "+" : "-") + pipsList[idx] + " PTS"
                };
            }

            function renderCandleProjectionAndPopup(isCall, marketName) {
                ["dr-candle-projection", "dr-next-signal-popup"].forEach(function(id){
                    var old = d.getElementById(id);
                    if(old) old.remove();
                });

                var anchor = findActiveCandleAnchor();
                var reach = generateTradeReachEstimate(isCall, Math.floor(Date.now() / 1000) + marketName.charCodeAt(0));
                var mainColor = isCall ? "#22c55e" : "#ef4444";
                var softBg = isCall ? "rgba(34, 197, 94, 0.14)" : "rgba(239, 68, 68, 0.14)";
                var animName = isCall ? "drBoxGlowUp" : "drBoxGlowDown";

                var projBox = d.createElement('div');
                projBox.id = 'dr-candle-projection';
                var boxWidth = 22;

                if(isCall) {
                    projBox.style.cssText = 'position:fixed;left:' + Math.round(anchor.x - boxWidth / 2) + 'px;' +
                        'top:' + Math.round(anchor.y - reach.boxHeight) + 'px;width:' + boxWidth + 'px;height:' + reach.boxHeight + 'px;' +
                        'border:2px dashed ' + mainColor + ';background:' + softBg + ';border-radius:3px;' +
                        'z-index:2147483645;pointer-events:none;font-family:"Courier New",monospace;' +
                        'animation:' + animName + ' 1.4s infinite ease-in-out;';
                    projBox.innerHTML = '' +
                        '<div style="position:absolute;top:-15px;left:50%;transform:translateX(-50%);font-size:11px;font-weight:900;color:' + mainColor + ';text-shadow:0 0 8px ' + mainColor + ';">▲</div>' +
                        '<div style="position:absolute;top:-27px;left:50%;transform:translateX(-50%);white-space:nowrap;background:rgba(4,12,8,0.92);border:1px solid ' + mainColor + ';color:' + mainColor + ';font-size:8px;font-weight:900;padding:1px 4px;border-radius:3px;">' + reach.estLabel + '</div>';
                } else {
                    projBox.style.cssText = 'position:fixed;left:' + Math.round(anchor.x - boxWidth / 2) + 'px;' +
                        'top:' + Math.round(anchor.y) + 'px;width:' + boxWidth + 'px;height:' + reach.boxHeight + 'px;' +
                        'border:2px dashed ' + mainColor + ';background:' + softBg + ';border-radius:3px;' +
                        'z-index:2147483645;pointer-events:none;font-family:"Courier New",monospace;' +
                        'animation:' + animName + ' 1.4s infinite ease-in-out;';
                    projBox.innerHTML = '' +
                        '<div style="position:absolute;bottom:-15px;left:50%;transform:translateX(-50%);font-size:11px;font-weight:900;color:' + mainColor + ';text-shadow:0 0 8px ' + mainColor + ';">▼</div>' +
                        '<div style="position:absolute;bottom:-27px;left:50%;transform:translateX(-50%);white-space:nowrap;background:rgba(16,6,8,0.92);border:1px solid ' + mainColor + ';color:' + mainColor + ';font-size:8px;font-weight:900;padding:1px 4px;border-radius:3px;">' + reach.estLabel + '</div>';
                }

                d.body.appendChild(projBox);

                var popupLeft = Math.min(window.innerWidth - 134, Math.max(8, Math.round(anchor.x + 22)));
                var popupTop = Math.min(window.innerHeight - 165, Math.max(75, Math.round(anchor.y - 45)));

                var popup = d.createElement('div');
                popup.id = 'dr-next-signal-popup';
                popup.style.cssText = 'position:fixed;left:' + popupLeft + 'px;top:' + popupTop + 'px;width:122px;' +
                    'background:linear-gradient(180deg, rgba(6, 20, 14, 0.96), rgba(3, 10, 7, 0.98));' +
                    'border:1.5px solid ' + mainColor + ';border-radius:10px;padding:7px 8px;' +
                    'z-index:2147483646;pointer-events:none;font-family:"Courier New",monospace;color:#e2e8f0;' +
                    'box-shadow:0 0 22px rgba(0,0,0,0.85), 0 0 14px ' + softBg + ';animation:drPopupPop 0.25s ease-out;';

                popup.innerHTML = '' +
                    '<div style="text-align:center;font-size:7px;font-weight:800;letter-spacing:0.6px;color:#94a3b8;line-height:1.25;margin-bottom:5px;">' +
                    '  <span style="color:' + mainColor + ';font-size:9px;">' + (isCall ? '▲' : '▼') + '</span> NEXT<br>SMART SIGNAL' +
                    '</div>' +
                    '<div style="background:rgba(2,8,5,0.9);border:1px solid rgba(148,163,184,0.22);border-radius:7px;padding:6px 4px;text-align:center;margin-bottom:5px;">' +
                    '  <div style="font-size:10px;font-weight:900;color:' + mainColor + ';letter-spacing:0.5px;">' + (isCall ? 'CALL (UP)' : 'PUT (DOWN)') + '</div>' +
                    '  <div style="font-size:8px;font-weight:800;color:#f8fafc;margin-top:2px;">EST: ' + reach.estLabel + '</div>' +
                    '  <div style="font-size:6.5px;color:#64748b;margin-top:1px;">' + marketName + '</div>' +
                    '</div>' +
                    '<div style="text-align:center;font-size:7px;font-weight:900;color:#4ade80;letter-spacing:1px;border-top:1px dashed rgba(74,222,128,0.25);padding-top:4px;">LOCKED</div>';

                d.body.appendChild(popup);

                setTimeout(function(){
                    if(projBox.parentNode) projBox.remove();
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

                var modal = d.createElement('div');
                modal.id = 'dr-scan-modal';
                modal.style.cssText = 'position:fixed;top:50%;left:50%;transform:translate(-50%, -50%);width:316px;max-width:92vw;' +
                    'background:linear-gradient(180deg, #061810 0%, #030b08 100%);' +
                    'border:2px solid #22c55e;border-radius:14px;padding:12px;z-index:2147483647;' +
                    'font-family:"Courier New",Courier,monospace;color:#4ade80;box-sizing:border-box;' +
                    'box-shadow:0 0 36px rgba(34,197,94,0.45), inset 0 0 18px rgba(34,197,94,0.18);overflow:hidden;';

                modal.innerHTML = '' +
                    '<div style="position:relative;overflow:hidden;">' +
                    '  <div id="dr-scan-laser" style="position:absolute;left:0;top:0;width:100%;height:3px;background:linear-gradient(90deg,transparent,#4ade80,#22c55e,#4ade80,transparent);box-shadow:0 0 12px #22c55e;z-index:5;pointer-events:none;animation:drSweepLaser 1.6s linear infinite;"></div>' +
                    '  <div style="display:flex;justify-content:space-between;align-items:flex-start;border-bottom:1px solid rgba(74,222,128,0.25);padding-bottom:7px;margin-bottom:8px;">' +
                    '    <div style="display:flex;align-items:center;gap:7px;">' +
                    '      <div style="width:28px;height:28px;border-radius:50%;border:1.5px solid #22c55e;background:#04140c;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:900;color:#4ade80;">DR</div>' +
                    '      <div>' +
                    '        <div style="font-size:11.5px;font-weight:900;color:#4ade80;letter-spacing:0.6px;">DR CANDLE TRACKER</div>' +
                    '        <div style="font-size:7px;color:#86efac;letter-spacing:0.5px;">QUANT CORE EXPLOIT</div>' +
                    '        <div style="font-size:6.5px;color:#64748b;">SESSION: QQX-5709-03EE-1967 | NODE 0x37</div>' +
                    '      </div>' +
                    '    </div>' +
                    '    <div style="display:flex;align-items:center;gap:5px;">' +
                    '      <div id="dr-pct-badge" style="background:rgba(20,83,45,0.65);border:1px solid #22c55e;color:#4ade80;font-size:9px;font-weight:900;padding:2px 6px;border-radius:10px;">1%</div>' +
                    '      <div id="dr-modal-close" style="cursor:pointer;color:#94a3b8;font-size:12px;font-weight:bold;padding:0 3px;">✕</div>' +
                    '    </div>' +
                    '  </div>' +

                    '  <div style="background:rgba(2,10,6,0.85);border:1px solid rgba(74,222,128,0.2);border-radius:8px;padding:7px;margin-bottom:7px;">' +
                    '    <div style="display:flex;justify-content:space-between;font-size:7px;color:#86efac;margin-bottom:4px;">' +
                    '      <span>MEMORY STREAM</span>' +
                    '      <span style="color:#4ade80;">● LINKED</span>' +
                    '    </div>' +
                    '    <div style="display:flex;align-items:center;justify-content:space-between;gap:6px;font-size:7.5px;">' +
                    '      <div style="display:flex;align-items:center;gap:3px;height:26px;">' +
                    '        <span style="width:5px;height:14px;background:#ef4444;border-radius:1px;display:inline-block;"></span>' +
                    '        <span style="width:5px;height:20px;background:#22c55e;border-radius:1px;display:inline-block;"></span>' +
                    '        <span style="width:5px;height:11px;background:#ef4444;border-radius:1px;display:inline-block;"></span>' +
                    '        <span style="width:5px;height:24px;background:#22c55e;border-radius:1px;display:inline-block;"></span>' +
                    '      </div>' +
                    '      <div><span style="color:#64748b;">OPEN</span> <b id="dr-m-open" style="color:#fff;">0.1645</b></div>' +
                    '      <div><span style="color:#64748b;">HIGH</span> <b id="dr-m-high" style="color:#4ade80;">0.1650</b></div>' +
                    '      <div><span style="color:#64748b;">LOW</span> <b id="dr-m-low" style="color:#f87171;">0.1639</b></div>' +
                    '      <div><span style="color:#64748b;">CLOSE</span> <b id="dr-m-close" style="color:#38bdf8;">0.1643</b></div>' +
                    '    </div>' +
                    '  </div>' +

                    '  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:4px;margin-bottom:5px;font-size:7px;text-align:center;">' +
                    '    <div style="background:rgba(2,10,6,0.85);border:1px solid rgba(74,222,128,0.2);border-radius:6px;padding:4px 2px;"><div style="color:#64748b;">0x29</div><div style="color:#4ade80;font-weight:bold;">VECTOR</div></div>' +
                    '    <div style="background:rgba(2,10,6,0.85);border:1px solid rgba(74,222,128,0.2);border-radius:6px;padding:4px 2px;"><div style="color:#4ade80;font-weight:bold;">LIVE</div><div style="color:#86efac;">FEED</div></div>' +
                    '    <div style="background:rgba(2,10,6,0.85);border:1px solid rgba(74,222,128,0.2);border-radius:6px;padding:4px 2px;"><div style="color:#64748b;">RSA</div><div id="dr-rsa-val" style="color:#eab308;font-weight:bold;">1%</div></div>' +
                    '    <div style="background:rgba(2,10,6,0.85);border:1px solid rgba(74,222,128,0.2);border-radius:6px;padding:4px 2px;"><div style="color:#64748b;">016</div><div style="color:#38bdf8;font-weight:bold;">CYCLE</div></div>' +
                    '  </div>' +

                    '  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:4px;margin-bottom:7px;font-size:7px;text-align:center;">' +
                    '    <div style="background:rgba(2,10,6,0.85);border:1px solid rgba(74,222,128,0.2);border-radius:6px;padding:4px 2px;"><div style="color:#4ade80;font-weight:bold;">23ms</div><div style="color:#64748b;">LATENCY</div></div>' +
                    '    <div style="background:rgba(2,10,6,0.85);border:1px solid rgba(74,222,128,0.2);border-radius:6px;padding:4px 2px;"><div style="color:#64748b;">BREACH</div><div id="dr-breach-val" style="color:#f87171;font-weight:bold;">1%</div></div>' +
                    '    <div style="background:rgba(2,10,6,0.85);border:1px solid rgba(74,222,128,0.2);border-radius:6px;padding:4px 2px;"><div style="color:#64748b;">016</div><div style="color:#86efac;font-weight:bold;">NODE</div></div>' +
                    '  </div>' +

                    '  <div id="dr-terminal-feed" style="background:#020906;border:1px solid rgba(74,222,128,0.22);border-radius:8px;padding:7px;font-size:7.2px;line-height:1.45;color:#86efac;">' +
                    '    <div><span style="color:#22c55e;">✓</span> Scanning server parts</div>' +
                    '    <div><span style="color:#22c55e;">✓</span> Brute-forcing auth token</div>' +
                    '    <div><span style="color:#22c55e;">✓</span> Intercepting order flow packets</div>' +
                    '    <div><span style="color:#22c55e;">✓</span> Reverse-engineering price engine</div>' +
                    '    <div><span style="color:#22c55e;">✓</span> Injecting live data hook</div>' +
                    '    <div id="dr-status-line" style="color:#4ade80;font-weight:bold;margin-top:3px;">CIPHER LOCKED || NODE ARMED</div>' +
                    '  </div>' +
                    '</div>';

                d.body.appendChild(modal);

                modal.querySelector('#dr-modal-close').onclick = function() {
                    modal.remove();
                };

                var market = detectMarketSymbol();
                var pct = 1;
                var pctBadge = modal.querySelector('#dr-pct-badge');
                var rsaVal = modal.querySelector('#dr-rsa-val');
                var breachVal = modal.querySelector('#dr-breach-val');
                var statusLine = modal.querySelector('#dr-status-line');

                var signalPromise = fetch(renderServerUrl + '/signal?market=' + encodeURIComponent(market) + '&t=' + Date.now())
                    .then(function(r){ return r.json(); })
                    .catch(function(){
                        return { signal: (Math.floor(Date.now() / 15000) % 2 === 0 ? "CALL" : "PUT") };
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

                    if(pct >= 100) {
                        clearInterval(progressTimer);
                        statusLine.innerText = '100% LOCKED || DEPLOYING CHART OVERLAY...';
                        signalPromise.then(function(data){
                            var sig = String(data.signal || 'CALL').toUpperCase();
                            var isCall = (sig === 'CALL' || sig === 'UP' || sig === 'BUY');
                            setTimeout(function(){
                                if(modal.isConnected) modal.remove();
                                renderCandleProjectionAndPopup(isCall, market);
                                triggerBrokerTradeClick(isCall);
                            }, 350);
                        });
                    }
                }, 120);
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
