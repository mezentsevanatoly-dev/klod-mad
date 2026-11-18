// Опасности: опасные аффекты и состояния -> ## DANGER в лог, стоп эксплора, своя реакция. Список: Клод мад\ОПАСНЫЕ_АФФЕКТЫ.md
for (var oi = modules.length - 1; oi >= 0; oi--) {
	if (modules[oi].moduleName == "Opasnosti") modules.splice(oi, 1);
}
function OpasnostiModule()
{
	this.moduleName = "Opasnosti";
	// [строка игры, название, команда-реакция или "", стоп эксплора?]
	// ЗАМЕРЛИ — только предупреждение (15.11 Крепость Тима: холд в бою, моб убит, стоп был лишним)
	this.list = [
		[/^Вы замерли на месте, не в силах шевельнуться/, "ЗАМЕРЛИ", "", false],
		[/потерял\S* часть своей жизнен+ой силы/i, "ПОТЕРЯ ЖИЗНЕННОЙ СИЛЫ", "", true],
		[/превращ\w* в камень/i, "КАМЕНЬ", "зач камне", true],
		[/украсть душу/i, "УКРАСТЬ ДУШУ", "", true]
	];
	this.lastT = {};

	// УД (16.11, слова пользователя): «Вы потеряли часть своей жизненой силы и опыта.» -> очистить; осуш м.осво.
	// Микстура снимает с шансом 90% -> пить снова, пока не придёт «Жизненная сила вернулась к вам.»
	this.osvTimerId = 191;
	this.osvEvery = 10;     // десятые секунды между попытками (1 с, слова пользователя 15.11; пульс 0,1 с, раунд 2,5 с)
	this.osvNoneMax = 5;    // столько «Осушить что?» подряд без «Вы залпом осушили микстуру освобождения» = микстур нет (одно «Осушить что?» бывает от триггера на голод)
	this.osvOn = false;
	this.osvTries = 0;
	this.osvNone = 0;
	this.osvDrink = function()
	{
		this.osvTries++;    // без предела: пить, пока не вернётся жизненная сила (слова пользователя 15.11)
		jmc.send("осуш м.осво");
	}
	this.osvStart = function()
	{
		this.osvTries = 0;
	this.osvNone = 0;
		if (!this.osvOn) jmc.send("очистить");
		this.osvOn = true;
		this.osvDrink();
		jmc.killTimer(this.osvTimerId);
		jmc.setTimer(this.osvTimerId, this.osvEvery);
	}
	this.osvStop = function( why )
	{
		this.osvOn = false;
		jmc.killTimer(this.osvTimerId);
		jmc.showme("-:- " + why);
		if (typeof ClaudeLog != "undefined") ClaudeLog.note("UD " + why);
	}
	this.onTimer = function( idTimer )
	{
		if (idTimer != this.osvTimerId) return;
		if (!this.osvOn) { jmc.killTimer(this.osvTimerId); return; }
		this.osvDrink();
	}

	this.onIncoming = function( sTextLine )
	{
		var s = rmcolor(sTextLine);
		if (/^\s*(\[|##|>>)/.test(s) || /^\S+ (сказал|произнес|крикнул)/.test(s)) return sTextLine;   // не реагировать на чат
		if (/^Жизненная сила вернулась к вам/.test(s)) {
			if (this.osvOn) { jmc.send("очистить"); this.osvStop("УД СНЯТО (попыток: " + this.osvTries + ")"); }   // очистить: не допить микстуры из очереди
			return sTextLine;
		}
		if (this.osvOn && /^Вы залпом осушили микстуру освобождения/.test(s)) this.osvNone = 0;
		if (this.osvOn && /^Осушить что\?/.test(s) && ++this.osvNone >= this.osvNoneMax) {
			this.osvStop("УД: НЕТ МИКСТУРЫ ОСВОБОЖДЕНИЯ");
			return sTextLine;
		}
		if (/^Вы потеряли часть своей жизнен+ой силы/.test(s)) this.osvStart();
		for (var i = 0; i < this.list.length; i++) {
			if (!this.list[i][0].test(s)) continue;
			var nowT = (new Date()).getTime(), nm = this.list[i][1];
			if (nowT - (this.lastT[nm] || 0) < 10000) break;
			this.lastT[nm] = nowT;
			var stop = this.list[i][3];
			if (typeof ClaudeLog != "undefined") ClaudeLog.note((stop ? "DANGER " : "WARN ") + nm + " | " + s.substring(0, 80));
			jmc.showme("-:- ОПАСНОСТЬ: " + nm);
			if (this.list[i][2]) jmc.send(this.list[i][2]);
			// эксплор не останавливаю — внешний скрипт видит DANGER и зовёт Claude (слова пользователя 15.11)
			break;
		}
		return sTextLine;
	}
}
var Opasnosti = new OpasnostiModule();
modules.push(Opasnosti);
jmc.showme("-:- Opasnosti loaded");
