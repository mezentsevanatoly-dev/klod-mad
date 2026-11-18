// BotFix: "Не получится! Вы сражаетесь за свою жизнь!" must repeat the step only if the character did NOT move.
// (School, room 19076: the move succeeded, the message came from the fight, BotCore stepped back and sent a wrong move.)
// Safe to include again: the original handlers are wrapped only once. Needs BotCore.js.
(function () {
	var core = botCore;
	if (!core.origNextStepFix) {
		core.origNextStepFix = core.nextStep;
		core.origOnIncomingFix = core.onIncoming;
	}
	core.nextStep = function () {
		jmc.parse("#scr botCore.stepVn=(\"x\"+$MsdpRoomVnum)");
		return this.origNextStepFix();
	};
	core.onIncoming = function (sTextLine) {
		var s = rmcolor(sTextLine);
		if (this.enableBot && this.lastStepPure && /^Не получится! Вы сражаетесь за свою жизнь!/.test(s)) {
			jmc.parse("#scr botCore.nowVn=(\"x\"+$MsdpRoomVnum)");
			if (this.nowVn && this.stepVn && this.nowVn != this.stepVn) {
				this.lastStepPure = false;
				if (typeof ClaudeLog != "undefined") ClaudeLog.note("BLOCK_IGNORED moved " + this.stepVn + "->" + this.nowVn);
			}
		}
		return this.origOnIncomingFix(sTextLine);
	};
})();
jmc.showme("-:- BotFix loaded");
