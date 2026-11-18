// ZoneLevel: zones from ZONE_UNTIL_LEVEL repeat until the character level (read from "сч") reaches the limit.
// Safe to include again (wraps the original handlers only once). Needs BotCore.js loaded first.
var ZONE_UNTIL_LEVEL = {"школа": 5};

(function () {
	var core = botCore;
	if (!core.origOnEndZone) core.origOnEndZone = core.onEndZone;
	if (!core.origOnTimer) core.origOnTimer = core.onTimer;
	core.lvlChecking = false;
	core.lvlTries = 0;
	core.lvlNote = function (m) { if (typeof ClaudeLog != "undefined") ClaudeLog.note(m); };

	// end of the route: instead of stopping, ask "сч" and decide in ~4 s
	core.onEndZone = function () {
		if (!this.lvlChecking && ZONE_UNTIL_LEVEL[zonename]) {
			this.enableBot = false;
			this.lvlChecking = true;
			this.lvlTries = 0;
			this.lvlAsk();
			return;
		}
		this.origOnEndZone();
	};
	core.lvlAsk = function () {
		this.myLevel = 0;
		this.vampCheck = true; this.vampHdr = false; this.vampSeen = false;   // same "сч": drink the bat elixir if vampirism is missing
		jmc.send("сч");
		jmc.setTimer(153, 40);
	};
	core.lvlDecide = function () {
		jmc.killTimer(153);
		var lim = ZONE_UNTIL_LEVEL[zonename];
		if (!(this.myLevel > 0) && this.lvlTries < 2) {
			this.lvlTries++;
			this.lvlAsk();
			return;
		}
		if (this.myLevel > 0 && this.myLevel < lim) {
			this.lvlChecking = false;
			this.lvlNote("ZONE_PASS zone=" + zonename + " level=" + this.myLevel + " limit=" + lim);
			jmc.showme("-:- [Бот: уровень " + this.myLevel + " < " + lim + ", ещё проход зоны '" + zonename + "']");
			jmc.parse("СтатСтоп " + zonename);
			if (this.loadZone(zonename)) {
				this.enableBot = true;
				jmc.parse("СтатСтарт " + zonename);
				jmc.send("look краткий");
			}
			return;
		}
		this.lvlNote("LEVEL_REACHED zone=" + zonename + " level=" + this.myLevel + " limit=" + lim);
		this.origOnEndZone();      // usual end: ZONE_END note, loop/repop handlers
		this.lvlChecking = false;
	};
	core.onTimer = function (idTimer) {
		if (jmc.event == 153) { this.lvlDecide(); return; }
		return this.origOnTimer(idTimer);
	};
})();
jmc.showme("-:- ZoneLevel loaded: " + ZONE_UNTIL_LEVEL["школа"] + " lvl for school");
