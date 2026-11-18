// ЧЕК — группа проверок (общий код для всех персонажей). Настройки персонажа — scripts\Чек_<Имя>.js (var ChekSettings).
//   чс      — чекстаф:   экип, сравнить с запомненным (НЕТ / ЛИШНЕЕ), запомнить
//   чколб   — чекколбы:  осм каждого расходника в инвентаре, сумма применений, МАЛО …
//   чафф    — чекафф:    сч, есть ли нужные аффекты
//   чрасход — чекрасход: кск :колбы -> Клод мад\РАСХОДНИКИ\КОЛБЫ.md, КУПИТЬ …
//   -сет    — сверка экипировки перед раздеванием (окей — раздеться, если не совпало)
// Описание: Клод мад\СКРИПТЫ\Чек.md
for (var ci2 = modules.length - 1; ci2 >= 0; ci2--) {
	if (modules[ci2].moduleName == "Chek") modules.splice(ci2, 1);
}
function ChekModule()
{
	this.moduleName = "Chek";
	this.S = (typeof ChekSettings != "undefined") ? ChekSettings : {charName: "?", needAffects: [], items: [], buyRules: [], unset: function(lvl) { return ""; }};
	this.timerId = 181;
	this.state = "";              // "", "st0", "st", "un0", "un", "osm", "aff0", "aff", "ksk0", "ksk"
	this.pending = "";

	this.out = function( s ) { jmc.showme("-:- ЧЕК: " + s); if (typeof ClaudeLog != "undefined") ClaudeLog.note("CHEK " + s); }
	this.isPrompt = function( s ) { return /\d+H \d+M \d+V/.test(s); }
	this.eqFile = function() { return "экип_" + this.S.charName + ".txt"; }
	this.busy = function() { if (this.state != "") { this.out("занят: " + this.state); return true; } return false; }

	// ---------- чекстаф ----------
	this.itemName = function( line )
	{
		var s = line.replace(/^\s*<[^>]+>\s+/, "");
		var b = s.indexOf(" [");
		if (b >= 0) s = s.substring(0, b);
		return s.replace(/\s*\.\.\..*$/, "").replace(/^\s+|\s+$/g, "");
	}
	this.loadEq = function()
	{
		var saved = [];
		if (!fso.FileExists(this.eqFile())) return null;
		var f = fso.OpenTextFile(this.eqFile(), 1);
		while (!f.AtEndOfStream) { var l = f.ReadLine(); if (l.replace(/\s+/g, "") != "") saved.push(this.itemName(l)); }
		f.Close();
		return saved;
	}
	this.diff = function( saved, now )
	{
		var missing = [], extra = now.slice(0);
		for (var j = 0; j < saved.length; j++) {
			var k = -1;
			for (var q = 0; q < extra.length; q++) if (extra[q] == saved[j]) { k = q; break; }
			if (k >= 0) extra.splice(k, 1); else missing.push(saved[j]);
		}
		return [missing, extra];
	}
	this.stuff = function()
	{
		if (this.busy()) return;
		this.eq = []; this.state = "st0";
		jmc.send("экип"); jmc.setTimer(this.timerId, 50);
	}
	this.stuffDone = function()
	{
		jmc.killTimer(this.timerId); this.state = "";
		var now = []; for (var i = 0; i < this.eq.length; i++) now.push(this.itemName(this.eq[i]));
		var saved = this.loadEq();
		if (saved) {
			var d = this.diff(saved, now);
			if (d[0].length == 0 && d[1].length == 0) this.out("экипировка совпадает с запомненной (" + now.length + ")");
			for (var m = 0; m < d[0].length; m++) this.out("НЕТ: " + d[0][m]);
			for (var x = 0; x < d[1].length; x++) this.out("НОВОЕ: " + d[1][x]);
		}
		if (now.length == 0) { this.out("ничего не надето — запомненное не трогаю"); return; }
		try { var f = fso.CreateTextFile(this.eqFile(), true); for (var n = 0; n < this.eq.length; n++) f.WriteLine(this.eq[n]); f.Close(); } catch (e) {}
		this.out("экипировка запомнена: " + now.length + " вещей (" + this.eqFile() + ")");
	}
	// -сет: сверка с запомненным, совпало — раздеться, нет — ждать окей
	this.unset = function( lvl )
	{
		if (this.busy()) return;
		this.unsetCmd = this.S.unset(lvl);
		if (!this.unsetCmd) { this.out("не знаю, что делать -сет (уровень: " + lvl + ") — набери счет"); return; }
		this.eq = []; this.state = "un0";
		jmc.send("экип"); jmc.setTimer(this.timerId, 50);
	}
	this.unsetDone = function()
	{
		jmc.killTimer(this.timerId); this.state = "";
		var now = []; for (var i = 0; i < this.eq.length; i++) now.push(this.itemName(this.eq[i]));
		var saved = this.loadEq();
		if (!saved) { this.out("нет запомненной экипировки — сначала чс. -сет: окей"); this.pending = this.unsetCmd; return; }
		var d = this.diff(saved, now);
		if (d[0].length == 0 && d[1].length == 0) { this.out("экипировка совпадает, -сет"); jmc.parse(this.unsetCmd); return; }
		for (var m = 0; m < d[0].length; m++) this.out("НЕТ: " + d[0][m]);
		for (var x = 0; x < d[1].length; x++) this.out("ЛИШНЕЕ: " + d[1][x]);
		this.out("-сет НЕ выполнен. Выполнить: окей");
		this.pending = this.unsetCmd;
	}
	this.ok = function()
	{
		if (!this.pending) { this.out("нечего подтверждать"); return; }
		var c = this.pending; this.pending = ""; this.out("подтверждено: -сет"); jmc.parse(c);
	}

	// ---------- чекколбы ----------
	this.kolby = function()
	{
		if (this.busy()) return;
		this.res = []; this.idx = 0; this.n = 1; this.sum = 0;
		this.osmNext();
	}
	this.osmNext = function()
	{
		jmc.killTimer(this.timerId);
		if (this.idx >= this.S.items.length) { this.kolbyDone(); return; }
		this.state = "osm"; this.got = false;
		this.curArg = (this.n == 1 ? "" : this.n) + this.S.items[this.idx][0];
		jmc.send("осм " + this.curArg); jmc.setTimer(this.timerId, 50);
	}
	this.osmDone = function()
	{
		jmc.killTimer(this.timerId);
		if (this.got && this.n < 10) { this.n++; this.osmNext(); return; }
		this.res.push([this.S.items[this.idx], this.sum, this.n - (this.got ? 0 : 1)]);
		this.idx++; this.n = 1; this.sum = 0; this.osmNext();
	}
	this.kolbyDone = function()
	{
		this.state = "";
		this.out("===== РАСХОДНИКИ " + this.S.charName + " =====");
		for (var i = 0; i < this.res.length; i++) {
			var it = this.res[i][0], line = it[0] + ": " + this.res[i][2] + " шт, применений " + this.res[i][1] + " (порог " + it[1] + ")";
			if (this.res[i][1] < it[1]) line += "   МАЛО " + it[2];
			this.out(line);
		}
	}

	// ---------- чекафф ----------
	this.aff = function()
	{
		if (this.busy()) return;
		this.affs = []; this.state = "aff0";
		jmc.send("сч"); jmc.setTimer(this.timerId, 50);
	}
	this.affDone = function()
	{
		jmc.killTimer(this.timerId); this.state = "";
		for (var a = 0; a < this.S.needAffects.length; a++) {
			var has = false;
			for (var b = 0; b < this.affs.length; b++) if (this.affs[b].indexOf(this.S.needAffects[a][0]) >= 0) has = true;
			this.out(has ? (this.S.needAffects[a][0] + ": есть") : this.S.needAffects[a][1]);
		}
	}

	// ---------- чекрасход ----------
	this.rashod = function()
	{
		if (this.busy()) return;
		this.ksk = {}; this.state = "ksk0";
		jmc.send("кск :колбы"); jmc.setTimer(this.timerId, 50);
	}
	this.rashodDone = function()
	{
		jmc.killTimer(this.timerId); this.state = "";
		var names = [], d = new Date(), pad = function(n) { return (n < 10 ? "0" : "") + n; };
		for (var k in this.ksk) names.push(k);
		names.sort();
		try {
			var f = fso.CreateTextFile("..\\РАСХОДНИКИ\\КОЛБЫ.md", true, true);
			f.WriteLine("# Отдел :Колбы КСК"); f.WriteLine("");
			f.WriteLine("Проверено: " + pad(d.getDate()) + "." + pad(d.getMonth() + 1) + "." + d.getFullYear() + " " + pad(d.getHours()) + ":" + pad(d.getMinutes()) + ", персонаж " + this.S.charName + " (чрасход)");
			f.WriteLine(""); f.WriteLine("| Расходник | Штук |"); f.WriteLine("|---|---|");
			for (var i = 0; i < names.length; i++) f.WriteLine("| " + names[i] + " | " + this.ksk[names[i]] + " |");
			f.Close();
		} catch (e) { this.out("не смогла записать КОЛБЫ.md: " + e.message); }
		this.out(":Колбы — видов " + names.length + " (РАСХОДНИКИ\\КОЛБЫ.md)");
		for (var r = 0; r < this.S.buyRules.length; r++) {
			var have = this.ksk[this.S.buyRules[r][0]] || 0;
			if (have < this.S.buyRules[r][1]) this.out("КУПИТЬ: " + this.S.buyRules[r][0] + " — в :Колбы " + have + ", купить " + this.S.buyRules[r][2]);
		}
	}

	// ---------- очередь и автозапуск ----------
	// после одевания (+колб…) -> чс, чколб, чафф; первый промпт за день любой JMC -> чрасход (если в КОЛБЫ.md не сегодняшняя дата)
	this.queue = [];
	this.runQueue = function() { if (this.state != "" || !this.queue.length) return; var f = this.queue.shift(); this[f](); }
	this.dayChecked = false;
	this.checkedToday = function()
	{
		try {
			var d = new Date(), pad = function(n) { return (n < 10 ? "0" : "") + n; };
			var today = pad(d.getDate()) + "." + pad(d.getMonth() + 1) + "." + d.getFullYear();
			if (!fso.FileExists("..\\РАСХОДНИКИ\\КОЛБЫ.md")) return false;
			var f = fso.OpenTextFile("..\\РАСХОДНИКИ\\КОЛБЫ.md", 1, false, -1), txt = f.ReadAll(); f.Close();
			return txt.indexOf("Проверено: " + today) >= 0;
		} catch (e) { return false; }
	}
	this.onInput = function( sTextLine )
	{
		if (/(^|;)\s*(\+колб\d|одеться)/.test(String(sTextLine))) { jmc.killTimer(182); jmc.setTimer(182, 30); }
		return sTextLine;
	}

	// ---------- общее ----------
	this.onTimer = function( idTimer )
	{
		idTimer = jmc.event;
		if (idTimer == 182) { jmc.killTimer(182); this.queue = ["stuff", "kolby", "aff"]; this.out("после одевания: чс, чколб, чафф"); this.runQueue(); return; }
		if (idTimer == 183) { jmc.killTimer(183); this.out("первая загрузка за день: чрасход"); if (this.state == "") this.rashod(); else this.queue.push("rashod"); return; }
		if (idTimer != this.timerId) return;
		jmc.killTimer(this.timerId);
		if (this.state == "st0" || this.state == "st") this.stuffDone();
		else if (this.state == "un0" || this.state == "un") this.unsetDone();
		else if (this.state == "osm") this.osmDone();
		else if (this.state == "aff0" || this.state == "aff") this.affDone();
		else if (this.state == "ksk0" || this.state == "ksk") this.rashodDone();
	}
	this.onIncoming = function( sTextLine )
	{
		if (!this.dayChecked && this.isPrompt(rmcolor(sTextLine))) {
			this.dayChecked = true;
			if (!this.checkedToday()) jmc.setTimer(183, 50);
		}
		if (this.state == "") return sTextLine;
		var s = rmcolor(sTextLine), st = this.state;
		if (st == "st0" || st == "un0") { if (/^Вы используете:/.test(s)) this.state = (st == "st0" ? "st" : "un"); return sTextLine; }
		if (st == "st" || st == "un") {
			var m = /^\s*<([^>]+)>\s+(.+)$/.exec(s);
			if (m) { this.eq.push("<" + m[1] + "> " + m[2]); return sTextLine; }
			if (this.isPrompt(s)) { if (st == "st") this.stuffDone(); else this.unsetDone(); }
			return sTextLine;
		}
		if (st == "osm") {
			var c = /Количество применений:\s*(\d+)/.exec(s);
			if (c) { this.sum += parseInt(c[1], 10); this.got = true; this.osmDone(); return sTextLine; }
			var nf = /Вы не видите здесь '([^']+)'/.exec(s);
			if (nf && nf[1] == this.curArg) this.osmDone();
			return sTextLine;
		}
		if (st == "aff0") { if (/^Аффекты:/.test(s)) this.state = "aff"; return sTextLine; }
		if (st == "aff") {
			if (this.isPrompt(s)) { this.affDone(); return sTextLine; }
			if (/^\s+\S/.test(s)) this.affs.push(s.replace(/^\s+|\s+$/g, ""));
			return sTextLine;
		}
		if (st == "ksk0") { if (/^В отделе 'Колбы' хранятся/.test(s)) this.state = "ksk"; return sTextLine; }
		if (st == "ksk") {
			if (this.isPrompt(s) || !s.replace(/\s+/g, "")) { this.rashodDone(); return sTextLine; }
			var km = /^\s*(.+?)(?:\s*\[(\d+)\])?\s*$/.exec(s);
			if (km && !/^Всего /.test(km[1])) this.ksk[km[1]] = (this.ksk[km[1]] || 0) + parseInt(km[2] || "1", 10);
		}
		return sTextLine;
	}
}
var Chek = new ChekModule();
(function( o ) {   // после каждой проверки — следующая из очереди
	var names = ["stuffDone", "kolbyDone", "affDone", "rashodDone"];
	for (var i = 0; i < names.length; i++) (function( n, f ) { o[n] = function() { f.apply(o, arguments); o.runQueue(); }; })(names[i], o[names[i]]);
})(Chek);
modules.push(Chek);
jmc.showme("-:- ЧЕК loaded (" + Chek.S.charName + "): чс / чколб / чафф / чрасход / -сет / окей");
