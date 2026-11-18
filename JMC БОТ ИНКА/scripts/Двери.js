// Двери: открывает только ту дверь, о которой сказала игра, и только в нужном направлении (справка ДВЕРИ).
// «Попробуйте сначала открыть X.» -> откр <слово> <направление>; «X заперт(а).» -> отпер, откр; «Вы открыли» -> шаг;
// «У вас нет нужного ключа.» -> стоп, запись в двери_<персонаж>.txt. Не больше 2 попыток на дверь в клетке.
// Описание: Клод мад\СКРИПТЫ\Двери.md
for (var di = modules.length - 1; di >= 0; di--) {
	if (modules[di].moduleName == "Dveri") modules.splice(di, 1);
}
function DveriModule()
{
	this.moduleName = "Dveri";
	this.charName = "Кимпи";
	this.enabled = true;

	this.DIRS = {"север": "север", "с": "север", "юг": "юг", "ю": "юг", "запад": "запад", "з": "запад",
	             "восток": "восток", "в": "восток", "вверх": "вверх", "вв": "вверх", "вниз": "вниз", "вн": "вниз"};
	this.LET = {"С": "север", "Ю": "юг", "З": "запад", "В": "восток", "^": "вверх", "v": "вниз"};
	this.lastDir = "";        // направление последнего шага (из ввода)
	this.pend = null;         // {name, key, dir, stage}
	this.waitPrompt = false;  // ждём промпт после «Попробуйте сначала открыть», чтобы увидеть закрытые выходы
	this.tries = {};          // vnum|dir -> число попыток
	this.vn = "";

	this.out = function( s ) { jmc.showme("-:- ДВЕРИ: " + s); }
	this.setVn = function( v ) { this.vn = String(v); }

	// «железную решетку» -> «решетк», «дверь в кабинет» -> «двер», «бронзовые врата» -> «врат»
	this.keyOf = function( name )
	{
		var w = name.replace(/^\s+|\s+$/g, "").split(/\s+/);
		var adj = /((ую|юю|ый|ий|ой|ые|ие|ое|ее|ая|яя|ых|их)(ся)?|ся|сь)$/;   // «искрящуюся» — тоже не существительное
		var noun = w[0];
		for (var i = 0; i < w.length; i++) { if (!adj.test(w[i])) { noun = w[i]; break; } }
		var k = noun.toLowerCase().replace(/[уюаяьиыео]+$/, "");
		if (k.length < 3) k = noun.toLowerCase();
		return k;
	}
	this.dirFromPrompt = function( s )
	{
		var m = /Вых:([^>]*)>/.exec(s);
		if (!m) return null;
		var closed = [], re = /\(([СЮЗВ\^v])\)/g, r;
		while ((r = re.exec(m[1])) != null) closed.push(this.LET[r[1]]);
		if (closed.length == 1) return closed[0];
		var bd = this.botDir();   // 15.11: шаг бота (zons[seekstep-1]) — бот шлёт через jmc.parse, onInput его не видит
		if (bd) for (var j = 0; j < closed.length; j++) if (closed[j] == bd) return bd;
		for (var i = 0; i < closed.length; i++) if (closed[i] == this.lastDir) return this.lastDir;
		return closed.length ? (this.lastDir || closed[0]) : (this.lastDir || null);
	}
	this.send = function( c ) { jmc.send(c); }
	this.botDir = function()
	{
		try {
			if (typeof zons == "undefined" || typeof seekstep == "undefined" || seekstep < 1) return null;
			var c = String(zons[seekstep - 1]), re = /\{\s*([^{}#;]+?)\s*\}/g, mm, last = null;
			while ((mm = re.exec(c)) != null) { var w = mm[1].toLowerCase(); if (this.DIRS[w]) last = this.DIRS[w]; }
			if (!last) { var w2 = c.replace(/^\s+|\s+$/g, "").toLowerCase(); if (this.DIRS[w2]) last = this.DIRS[w2]; }
			return last;
		} catch (e) { return null; }
	}
	this.giveUp = function( why )
	{
		var p = this.pend; this.pend = null;
		if (!p) return;
		this.out(why + ": " + p.name + " (" + p.dir + "), клетка " + this.vn);
		try {
			var f = fso.OpenTextFile("двери_" + this.charName + ".txt", 8, true);
			f.WriteLine(this.vn + ";" + p.dir + ";" + p.name + ";" + why);
			f.Close();
		} catch (e) {}
	}

	this.onInput = function( sTextLine )
	{
		var parts = String(sTextLine).split(";");
		for (var i = 0; i < parts.length; i++) {
			var c = parts[i].replace(/^\s+|\s+$/g, "").toLowerCase();
			if (this.DIRS[c]) this.lastDir = this.DIRS[c];
		}
		// 15.11: бот шлёт шаг как #if {$MsdpRoomVnum == N} {вниз} — направление в последних фигурных скобках
		var re = /\{\s*([^{}#;]+?)\s*\}/g, mm, last = null;
		while ((mm = re.exec(String(sTextLine))) != null) { var w = mm[1].toLowerCase(); if (this.DIRS[w]) last = this.DIRS[w]; }
		if (last) this.lastDir = last;
		return sTextLine;
	}
	this.onIncoming = function( sTextLine )
	{
		if (!this.enabled) return sTextLine;
		var s = rmcolor(sTextLine);
		var m = /^Попробуйте сначала открыть (.+)\.\s*$/.exec(s);
		if (m) {
			jmc.parse('#scr Dveri.setVn("$MsdpRoomVnum")');
			this.pend = {name: m[1], key: this.keyOf(m[1]), dir: "", stage: "open"};
			this.waitPrompt = true;
			return sTextLine;
		}
		if (this.waitPrompt && /Вых:/.test(s)) {
			this.waitPrompt = false;
			var p = this.pend;
			if (!p) return sTextLine;
			p.dir = this.dirFromPrompt(s);
			if (!p.dir) { this.giveUp("не понял направление"); return sTextLine; }
			var t = this.vn + "|" + p.dir;
			this.tries[t] = (this.tries[t] || 0) + 1;
			if (this.tries[t] > 2) { this.giveUp("2 попытки не помогли"); return sTextLine; }
			this.send("откр " + p.key + " " + p.dir);
			return sTextLine;
		}
		if (!this.pend) return sTextLine;
		var p2 = this.pend;
		if (/^Вы открыли /.test(s)) { this.pend = null; this.send(p2.dir); return sTextLine; }
		if (/^Вы отперли /.test(s)) { this.send("откр " + p2.key + " " + p2.dir); return sTextLine; }
		if (/^У вас нет нужного ключа\./.test(s)) { this.giveUp("ЗАПЕРТО, НЕТ КЛЮЧА"); return sTextLine; }
		if (/заперт[аоы]?\.\s*$/.test(s) && !/не заперт/.test(s) && p2.stage == "open") {
			p2.stage = "unlock";
			this.send("отпер " + p2.key + " " + p2.dir);
			return sTextLine;
		}
		if (/^(Вы не можете (открыть|отпереть)|Похоже, (тут|здесь) нет)/.test(s)) { this.giveUp("не та цель (" + p2.key + ")"); return sTextLine; }
		return sTextLine;
	}
}
var Dveri = new DveriModule();
modules.push(Dveri);
jmc.showme("-:- Dveri loaded (двери по сообщению игры)");
