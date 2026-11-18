// CardProbe: a mob from the zone csv with an EMPTY level is looked at once ("смотреть <имя>") before the bot attacks it,
// so its card ("Имя [уровень N], Профессия") lands in claude_game.log (tools/cards_from_log.py puts it into game.db mob_cards).
// Safe to include again. Needs BotCore.js.
(function () {
	var core = botCore;
	if (!core.origOnStatusProbe) core.origOnStatusProbe = core.onStatus;
	core.probed = core.probed || {};
	core.onStatus = function (sTextLine, isRoom) {
		try {
			if (this.enableBot && isRoom && this.BotInZone && this.mobsInRoom) {
				for (var i = 0; i < this.mobsInRoom.length; i++) {
					var m = mobs[this.mobsInRoom[i]];
					if (m && (m.level === "" || m.level == null) && !this.probed[m.name]) {
						this.probed[m.name] = 1;
						jmc.send("смотреть " + m.name.replace(/ /g, "."));
						if (typeof ClaudeLog != "undefined") ClaudeLog.note("CARD_PROBE " + m.name);
					}
				}
			}
		} catch (e) {}
		return this.origOnStatusProbe(sTextLine, isRoom);
	};
})();
jmc.showme("-:- CardProbe loaded");
