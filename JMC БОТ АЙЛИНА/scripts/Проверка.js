// Проверка: +сет;+колб2; ждать 2; экип -> запомнить экип в файл; сч -> аффекты; осм каждого расходника; сумма применений; итог
// Запуск: #scr Proverka.start()   (алиас: проверка)
// Сверка перед -сет: #scr Proverka.unset()  (алиас: -сет); подтверждение: #scr Proverka.ok()  (алиас: окей)
// Описание: Клод мад\СКРИПТЫ\Проверка.md
for (var pi = modules.length - 1; pi >= 0; pi--) {
	if (modules[pi].moduleName == "Proverka") modules.splice(pi, 1);
}
function ProverkaModule()
{
	this.moduleName = "Proverka";
	// ---- настройки персонажа ----
	this.charName = "Айлина";
	this.setCmds = ["+сет", "+колб2"];
	this.unsetCmd = "сня все;кс :барб3 все16";   // то, что делал -сет раньше
	this.kitDept = "Барб3";                       // отдел КСК, из которого +сет берёт вещи
	this.kitCount = 16;                           // сколько вещей должен забрать +сет
	// аффект (как в сч), сообщение если нет
	this.needAffects = [
		["плавная левитация", "НЕТ ПОЛЁТА"]
	];
	// ключ для осм, порог (сумма применений), слово для сообщения МАЛО ...
	this.items = [
		["восс",  10, "ВОССТАНОВЛЕНИЯ"],
		["охр",   10, "ОХРАНОК"],
		["мыши",  10, "МЫШЕЙ"],
		["насыщ", 15, "НАСЫЩЕНИЯ"],
		["прозр", 10, "ПРОЗРЕНИЯ"],
		["панац", 10, "ПАНАЦЕИ"],
		["камн",  10, "КАМНЕЙ"],
		["м.осво", 3, "ОСВОБОЖДЕНИЯ"]
	];
	this.maxEach = 10;          // больше 10 экземпляров одного вида не смотрим
	// ---- конец настроек ----

	this.timerId = 161;
	this.state = "";            // "", "wait", "eq0", "eq", "aff0", "aff", "osm", "cmp0", "cmp"
	this.eq = []; this.aff = []; this.kitTaken = 0;
	this.idx = 0; this.n = 1; this.sum = 0; this.got = false; this.res = []; this.curArg = "";
	this.cur = []; this.pending = false;

	this.out = function( s ) { jmc.showme("-:- ПРОВЕРКА: " + s); }
	this.isPrompt = function( s ) { return /\d+H \d+M \d+V/.test(s); }
	this.eqFile = function() { return "экип_" + this.charName + ".txt"; }

	this.start = function()
	{
		this.eq = []; this.aff = []; this.res = []; this.kitTaken = 0; this.idx = 0; this.n = 1; this.sum = 0;
		this.state = "wait";
		for (var i = 0; i < this.setCmds.length; i++) jmc.parse(this.setCmds[i]);
		jmc.setTimer(this.timerId, 20);   // ждать 2 с
	}
	this.onTimer = function( idTimer )
	{
		idTimer = jmc.event;
		if (idTimer != this.timerId) return;
		jmc.killTimer(this.timerId);
		if (this.state == "wait") { this.state = "eq0"; jmc.send("экип"); jmc.setTimer(this.timerId, 50); return; }
		if (this.state == "eq0" || this.state == "eq") { this.saveEq(); this.affStart(); return; }
		if (this.state == "aff0" || this.state == "aff") { this.osmNext(); return; }
		if (this.state == "osm") { this.osmDone(); return; }   // нет ответа 5 с — дальше
		if (this.state == "cmp0" || this.state == "cmp") { this.compare(); return; }
		if (this.state == "ksk0" || this.state == "ksk") { this.kskDone(); return; }
	}
	this.saveEq = function()
	{
		try {
			var f = fso.CreateTextFile(this.eqFile(), true);
			for (var i = 0; i < this.eq.length; i++) f.WriteLine(this.eq[i]);
			f.Close();
		} catch (e) { this.out("не смогла записать файл экипировки"); }
		this.out("экипировка запомнена: " + this.eq.length + " вещей (" + this.eqFile() + ")");
	}
	this.affStart = function()
	{
		this.state = "aff0";
		jmc.send("сч");
		jmc.setTimer(this.timerId, 50);
	}
	this.osmNext = function()
	{
		jmc.killTimer(this.timerId);
		if (this.idx >= this.items.length) { this.finish(); return; }
		this.state = "osm"; this.got = false;
		var key = this.items[this.idx][0];
		this.curArg = (this.n == 1 ? "" : this.n) + key;
		jmc.send("осм " + this.curArg);
		jmc.setTimer(this.timerId, 50);
	}
	this.osmDone = function()   // ответ на текущий осм закончился
	{
		jmc.killTimer(this.timerId);
		if (this.got && this.n < this.maxEach) { this.n++; this.osmNext(); return; }
		var it = this.items[this.idx];
		this.res.push([it, this.sum, this.n - (this.got ? 0 : 1)]);
		this.idx++; this.n = 1; this.sum = 0;
		this.osmNext();
	}
	this.finish = function()
	{
		this.state = "";
		this.out("===== ПРОВЕРКА " + this.charName + " =====");
		if (this.kitTaken < this.kitCount) this.out("+СЕТ ЗАБРАЛ " + this.kitTaken + " ИЗ " + this.kitCount);
		else this.out("+сет забрал " + this.kitTaken + " из " + this.kitCount);
		for (var a = 0; a < this.needAffects.length; a++) {
			var has = false;
			for (var b = 0; b < this.aff.length; b++) if (this.aff[b].indexOf(this.needAffects[a][0]) >= 0) has = true;
			this.out(has ? (this.needAffects[a][0] + ": есть") : this.needAffects[a][1]);
		}
		for (var i = 0; i < this.res.length; i++) {
			var it = this.res[i][0], sum = this.res[i][1], cnt = this.res[i][2];
			var line = it[0] + ": " + cnt + " шт, применений " + sum + " (порог " + it[1] + ")";
			if (sum < it[1]) line += "   МАЛО " + it[2];
			this.out(line);
		}
		this.out("===== конец =====");
		this.kskStart();
	}


	// ---- отдел :Колбы КСК -> Клод мад\РАСХОДНИКИ\КОЛБЫ.md ----
	this.kolbyFile = "..\\РАСХОДНИКИ\\КОЛБЫ.md";
	this.buyRules = [["микстура освобождения", 5, "30 шт. в больнице Элендора"]];   // РАСХОДНИКИ\ЗАКУПКА.md
	this.kskStart = function()
	{
		this.ksk = {}; this.state = "ksk0";
		jmc.send("кск :колбы");
		jmc.setTimer(this.timerId, 50);
	}
	this.kskDone = function()
	{
		jmc.killTimer(this.timerId);
		this.state = "";
		var names = [], d = new Date(), pad = function(n) { return (n < 10 ? "0" : "") + n; };
		for (var k in this.ksk) names.push(k);
		names.sort();
		try {
			var f = fso.CreateTextFile(this.kolbyFile, true, true);
			f.WriteLine("# Отдел :Колбы КСК");
			f.WriteLine("");
			f.WriteLine("Проверено: " + pad(d.getDate()) + "." + pad(d.getMonth() + 1) + "." + d.getFullYear() + " " + pad(d.getHours()) + ":" + pad(d.getMinutes()) + ", персонаж " + this.charName + " (кск :колбы, скрипт проверка)");
			f.WriteLine("");
			f.WriteLine("| Расходник | Штук |");
			f.WriteLine("|---|---|");
			for (var i = 0; i < names.length; i++) f.WriteLine("| " + names[i] + " | " + this.ksk[names[i]] + " |");
			f.Close();
		} catch (e) { this.out("не смогла записать КОЛБЫ.md: " + e.message); }
		this.out(":Колбы — видов " + names.length + " (РАСХОДНИКИ\\КОЛБЫ.md)");
		for (var b = 0; b < this.buyRules.length; b++) {
			var have = this.ksk[this.buyRules[b][0]] || 0;
			if (have < this.buyRules[b][1]) this.out("КУПИТЬ: " + this.buyRules[b][0] + " — в :Колбы " + have + ", купить " + this.buyRules[b][2]);
		}
	}

	// ---- сверка перед -сет ----
	this.itemName = function( line )   // "<слот> вещь * [состояние] ...светится" -> "вещь *"
	{
		var s = line.replace(/^\s*<[^>]+>\s+/, "");
		var b = s.indexOf(" [");
		if (b >= 0) s = s.substring(0, b);
		s = s.replace(/\s*\.\.\..*$/, "");
		return s.replace(/^\s+|\s+$/g, "");
	}
	this.unset = function()
	{
		this.cur = []; this.pending = false;
		this.state = "cmp0";
		jmc.send("экип");
		jmc.setTimer(this.timerId, 50);
	}
	this.compare = function()
	{
		jmc.killTimer(this.timerId);
		this.state = "";
		var saved = [];
		try {
			if (!fso.FileExists(this.eqFile())) {
				this.out("нет запомненной экипировки (" + this.eqFile() + "), сначала проверка. -сет: наберите окей");
				this.pending = true; return;
			}
			var f = fso.OpenTextFile(this.eqFile(), 1);
			while (!f.AtEndOfStream) { var l = f.ReadLine(); if (l.replace(/\s+/g, "") != "") saved.push(this.itemName(l)); }
			f.Close();
		} catch (e) { this.out("не смогла прочитать " + this.eqFile() + ". -сет: наберите окей"); this.pending = true; return; }
		var now = [];
		for (var i = 0; i < this.cur.length; i++) now.push(this.itemName(this.cur[i]));
		var missing = [], extra = now.slice(0);
		for (var j = 0; j < saved.length; j++) {
			var k = -1;
			for (var q = 0; q < extra.length; q++) if (extra[q] == saved[j]) { k = q; break; }
			if (k >= 0) extra.splice(k, 1); else missing.push(saved[j]);
		}
		if (missing.length == 0 && extra.length == 0) {
			this.out("экипировка совпадает (" + now.length + " вещей), выполняю -сет");
			jmc.parse(this.unsetCmd);
			return;
		}
		this.out("===== ЭКИПИРОВКА НЕ СОВПАДАЕТ =====");
		for (var m = 0; m < missing.length; m++) this.out("НЕТ: " + missing[m]);
		for (var x = 0; x < extra.length; x++) this.out("ЛИШНЕЕ: " + extra[x]);
		this.out("-сет НЕ выполнен. Чтобы выполнить: окей");
		this.pending = true;
	}
	this.ok = function()
	{
		if (!this.pending) { this.out("нечего подтверждать"); return; }
		this.pending = false;
		this.out("подтверждено, выполняю -сет");
		jmc.parse(this.unsetCmd);
	}

	this.onIncoming = function( sTextLine )
	{
		if (this.state == "") return sTextLine;
		var s = rmcolor(sTextLine);
		if (this.state == "ksk0") { if (/^В отделе 'Колбы' хранятся/.test(s)) this.state = "ksk"; return sTextLine; }
		if (this.state == "ksk") {
			if (this.isPrompt(s) || !s.replace(/\s+/g, "")) { this.kskDone(); return sTextLine; }
			var km = /^\s*(.+?)(?:\s*\[(\d+)\])?\s*$/.exec(s);
			if (km && !/^Всего /.test(km[1])) this.ksk[km[1]] = (this.ksk[km[1]] || 0) + parseInt(km[2] || "1", 10);
			return sTextLine;
		}
		if (this.state == "wait") {
			if (s.indexOf("Вы забрали ") == 0 && s.indexOf("из отдела '" + this.kitDept + "'") > 0) this.kitTaken++;
			return sTextLine;
		}
		if (this.state == "eq0") { if (/^Вы используете:/.test(s)) this.state = "eq"; return sTextLine; }
		if (this.state == "cmp0") { if (/^Вы используете:/.test(s)) this.state = "cmp"; return sTextLine; }
		if (this.state == "eq" || this.state == "cmp") {
			var m = /^\s*<([^>]+)>\s+(.+)$/.exec(s);
			if (m) { (this.state == "eq" ? this.eq : this.cur).push("<" + m[1] + "> " + m[2]); return sTextLine; }
			if (this.isPrompt(s)) {
				if (this.state == "eq") { jmc.killTimer(this.timerId); this.saveEq(); this.affStart(); }
				else this.compare();
			}
			return sTextLine;
		}
		if (this.state == "aff0") { if (/^Аффекты:/.test(s)) this.state = "aff"; return sTextLine; }
		if (this.state == "aff") {
			if (this.isPrompt(s)) { this.osmNext(); return sTextLine; }
			if (/^\s+\S/.test(s)) this.aff.push(s.replace(/^\s+|\s+$/g, ""));
			return sTextLine;
		}
		if (this.state == "osm") {
			var c = /Количество применений:\s*(\d+)/.exec(s);
			if (c) { this.sum += parseInt(c[1], 10); this.got = true; this.osmDone(); return sTextLine; }
			var nf = /Вы не видите здесь '([^']+)'/.exec(s);
			if (nf && nf[1] == this.curArg) this.osmDone();
		}
		return sTextLine;
	}
}
var Proverka = new ProverkaModule();
modules.push(Proverka);
jmc.showme("-:- Proverka loaded: проверка / -сет / окей");
