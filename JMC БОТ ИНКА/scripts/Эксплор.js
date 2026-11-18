// Эксплор зоны: обход всех клеток зоны по выходам из MSDP, ближайшая непройденная клетка первой.
// Запуск: эксплор  (алиас -> #scr Explore.cmd("%0")); стоп: эксплор стоп; статус: эксплор инфо
// Описание: Клод мад\СКРИПТЫ\Эксплор.md
for (var ei = modules.length - 1; ei >= 0; ei--) {
	if (modules[ei].moduleName == "Explore") modules.splice(ei, 1);
}
function ExploreModule()
{
	this.moduleName = "Explore";
	this.needAffect = "плавная левитация";
	this.minHpPct = 50;                 // меньше — стоп
	this.stepTimeout = 80;              // 8 с на шаг (двери успевают открыться)
	this.outDir = "..\\ЗОНЫ";
	this.timerId = 171;
	this.dangerMobs = {"Рыцарский рубеж": /отшельник/i, "Эрдер": /(^|[^и] )дракон|мантикор/i};   // по зонам: отшельник у дороги Видрир — хутор Аргниста; в других зонах отшельники не в счёт
	// ключевые мобы зон (ключи / по словам пользователя): бить сразу, как увидели
	this.noKill = /Хасим/i;   // квестовые «не пускает» — не бить, выход закрыть (15.11 Затерянный остров: Хасим пускает после «дать 500 хасим»)
	this.keyMobs = {"Башня вихря": /Страж вихря/, "Тюрьма Геоланта": /Дюжий стражник/i, "Рыцарский рубеж": /рыцарь/i};
	this.lowMovePct = 20;               // энергии меньше 20% или «Вы слишком устали» -> moveCmd (Айлина: слова пользователя 15.11)
	this.moveCmd = "осуш восст";     // слова пользователя: увидел отшельника (Рубеж) — уходи назад, рядом ДТ

	this.K2D = {"n": "север", "s": "юг", "e": "восток", "w": "запад", "u": "вверх", "d": "вниз"};
	this.OPP = {"n": "s", "s": "n", "e": "w", "w": "e", "u": "d", "d": "u"};

	this.reset = function()
	{
		this.state = "";          // "", "aff0", "aff", "run", "back", "home"
		this.zone = ""; this.start = ""; this.cur = ""; this.curName = ""; this.curArea = "";
		this.rooms = {};          // vnum -> {name, exits:{key:vnum}}
		this.blocked = {};        // "vnum|key" -> причина
		this.borders = [];        // "из;направление;в;зона"
		this.dt = {};
	this.dtZ = {};            // "зона|клетка|направление" -> 1 (ручные запреты пользователя)             // "клетка|направление" -> 1 (для этой зоны)
		this.aw = null;           // ожидаемый шаг {from, key, t}
		this.affOk = false; this.fight = false; this.count = 0;
	}
	this.reset();

	this.safe = function( s ) { return String(s).replace(/[\\\/:*?"<>|]/g, "'"); }   // имя зоны -> имя папки/файла
	// «Высокий арбалетчик» -> «арбалетчик», «Страж вихря» -> «страж»
	this.killWord = function( name )
	{
		var w = String(name).replace(/^\s+|\s+$/g, "").split(/\s+/), adj = /(ий|ый|ой|ая|яя|ое|ее|ые|ие)$/i;
		for (var i = 0; i < w.length; i++) if (!adj.test(w[i])) return w[i].toLowerCase();
		return w[w.length - 1].toLowerCase();
	}
	this.attack = function( name )
	{
		var nowT = (new Date()).getTime();
		if (nowT - (this.killT || 0) < 4000) return;          // не дублировать команду
		this.killT = nowT;
		jmc.send("убить " + this.killWord(name)); this.out("бью: " + name);
	}
	this.out = function( s ) { jmc.showme("-:- ЭКСПЛОР: " + s); if (typeof ClaudeLog != "undefined") ClaudeLog.note("EXPLORE " + s); }

	this.cmd = function( a )
	{
		a = String(a || "").replace(/^\s+|\s+$/g, "");
		if (a == "стоп") { this.stop("остановлено командой"); return; }
		if (a == "инфо") { this.info(); return; }
		if (this.state != "") { this.out("уже идёт (эксплор стоп — остановить)"); return; }
		this.reset();
		this.state = "aff0";
		jmc.send("сч");
		jmc.setTimer(this.timerId, 50);
	}
	this.info = function()
	{
		var n = 0; for (var v in this.rooms) n++;
		this.out("зона " + this.zone + ", клеток " + n + ", переходов " + this.borders.length + ", состояние " + (this.state || "стоит"));
	}
	this.stop = function( why )
	{
		jmc.killTimer(this.timerId);
		if (this.state == "") { this.out("не запущен"); return; }
		this.save();
		if (typeof botCore != "undefined" && botCore.enableRecord) botCore.onInput(".бот запись стоп");
		this.state = "";
		this.out("СТОП: " + why);
	}

	// уже записанные клетки и переходы зоны (продолжить, а не затереть). «не прошла»/«нет прохода» не берём — временное
	this.loadKnown = function()
	{
		var W = {"север": "n", "юг": "s", "восток": "e", "запад": "w", "вверх": "u", "вниз": "d"}, n = 0;
		try {
			var dir = this.outDir + "\\" + this.safe(this.zone);
			if (!fso.FileExists(dir + "\\клетки.csv")) return;
			var f = fso.OpenTextFile(dir + "\\клетки.csv", 1); f.ReadLine();
			while (!f.AtEndOfStream) {
				var p = f.ReadLine().split(";"); if (p.length < 3) continue;
				var ex = {}, es = p[2].split(",");
				for (var i = 0; i < es.length; i++) { var kv = es[i].split("="); if (kv.length == 2 && W[kv[0]]) ex[W[kv[0]]] = kv[1]; }
				this.rooms[p[0]] = {name: p[1], exits: ex}; n++;
				var cl = (p[3] || "").split(",");
				for (var j = 0; j < cl.length; j++) {
					var m = /^(\S+): (.+)$/.exec(cl[j]);
					if (m && W[m[1]] && /другая зона|рядом ДТ/.test(m[2])) this.blocked[p[0] + "|" + W[m[1]]] = m[2];
				}
			}
			f.Close();
			if (fso.FileExists(dir + "\\переходы.csv")) {
				var g = fso.OpenTextFile(dir + "\\переходы.csv", 1); g.ReadLine();
				while (!g.AtEndOfStream) { var b = g.ReadLine(); if (b) this.borders.push(b); }
				g.Close();
			}
			if (n) this.out("подхватила записанные клетки: " + n);
		} catch (e) { this.out("не смогла прочитать записанные клетки: " + e.message); }
	}

	this.loadDT = function()
	{
		try {
			var f = fso.OpenTextFile(this.outDir + "\\дт_выходы.txt", 1);
			while (!f.AtEndOfStream) {
				var p = f.ReadLine().split(";");
				if (p.length == 3) this.dt[p[1] + "|" + p[2]] = 1;
				if (p.length == 4 && p[3] == "зона") this.dtZ[p[0] + "|" + p[1] + "|" + p[2]] = 1;   // ручные запреты (ЗОНЫ\запрет_выходы.txt) — только в своей зоне   // без зоны: в маппере и MSDP зоны называются по-разному (15.11 Шиар: «Башня Шиара» = «Город Шиар», погибла в ДТ)
			}
			f.Close();
		} catch (e) { this.out("нет файла дт_выходы.txt — ДТ не учитываю"); }
	}

	// вызывается из JMC с подставленными MSDP-переменными
	this.room = function( vn, name, area, len, k1, v1, k2, v2, k3, v3, k4, v4, k5, v5, k6, v6, hp, hpmax, mv, mvmax )
	{
		var nowT = (new Date()).getTime();
		if (parseInt(mv, 10) * 100 < this.lowMovePct * parseInt(mvmax, 10) && nowT - (this.mvT || 0) > 20000 &&
		    (this.state == "run" || this.state == "back" || this.state == "home")) {
			this.mvT = nowT; jmc.send(this.moveCmd); this.out("энергии мало — " + this.moveCmd);
		}
		if (this.state != "run" && this.state != "back" && this.state != "home") return;
		var ks = [k1, k2, k3, k4, k5, k6], vs = [v1, v2, v3, v4, v5, v6], ex = {};
		for (var i = 0; i < parseInt(len, 10) && i < 6; i++) ex[ks[i]] = String(vs[i]);
		vn = String(vn);
		if (parseInt(hp, 10) * 100 < this.minHpPct * parseInt(hpmax, 10)) { this.stop("хп меньше " + this.minHpPct + "%"); return; }
		if (vn == this.cur) return;              // клетка не сменилась
		var prev = this.cur, aw = this.aw;
		this.prevRoom = prev;
		this.cur = vn; this.curName = name; this.curArea = area;
		if (this.zone == "") {                   // старт
			this.zone = area; this.start = vn; this.loadDT(); this.loadKnown();
			if (typeof botCore != "undefined") botCore.onInput(".бот запись старт эксплор_" + this.safe(area).replace(/\s+/g, "_"));
			jmc.send("смотреть");                // бот запишет мобов стартовой клетки
			this.out("старт: " + area + ", клетка " + vn + " (" + name + ")");
		}
		if (area != this.zone) {                 // вышли за границу зоны
			if (aw) {
				this.borders.push(aw.from + ";" + this.K2D[aw.key] + ";" + vn + ";" + area);
				this.blocked[aw.from + "|" + aw.key] = "другая зона: " + area;
			}
			this.aw = null;
			var back = null;
			for (var k in ex) if (ex[k] == prev) back = k;
			if (!back && aw) back = this.OPP[aw.key];
			this.out("граница: " + area + " — назад");
			this.state = "back";
			this.go(back, vn);
			return;
		}
		if (this.state == "back") this.state = "run";
		if (!this.rooms[vn]) { this.rooms[vn] = {name: name, exits: ex}; this.count++; if (this.count % 20 == 0) this.save(); }
		else this.rooms[vn].exits = ex;
		this.aw = null;
		jmc.killTimer(this.timerId);
		jmc.setTimer(this.timerId, 3);           // следующий шаг через 0.3 с (next ждёт, пока бот досмотрит мобов)
	}

	this.go = function( key, from )
	{
		if (!key) { this.stop("не знаю, куда идти назад"); return; }
		this.aw = {from: from, key: key};
		if (typeof Dveri != "undefined") Dveri.lastDir = this.K2D[key];
		jmc.send(this.K2D[key]);
		jmc.killTimer(this.timerId);
		jmc.setTimer(this.timerId, this.stepTimeout);
	}

	// путь (список ключей) от cur до ближайшей клетки, у которой есть непройденный выход; или до цели target
	this.plan = function( target )
	{
		var q = [this.cur], prev = {}, seen = {};
		seen[this.cur] = 1;
		while (q.length) {
			var v = q.shift(), r = this.rooms[v];
			if (!r) continue;
			for (var k in r.exits) {
				var w = r.exits[k];
				if (this.blocked[v + "|" + k] || this.dt[r.name + "|" + this.K2D[k]] || this.dtZ[this.zone + "|" + r.name + "|" + this.K2D[k]]) continue;
				if (!target && !this.rooms[w]) {          // непройденный выход
					var path = [k], x = v;
					while (x != this.cur) { path.unshift(prev[x].key); x = prev[x].from; }
					return path;
				}
				if (this.rooms[w] && !seen[w]) {
					seen[w] = 1; prev[w] = {from: v, key: k};
					if (target && w == target) {
						var p2 = [], y = w;
						while (y != this.cur) { p2.unshift(prev[y].key); y = prev[y].from; }
						return p2;
					}
					q.push(w);
				}
			}
		}
		return null;
	}

	this.next = function()
	{
		if (!this.rooms[this.cur] && this.state != "back") {   // текущая клетка не записана — перечитать MSDP и подождать
			this.lost = (this.lost || 0) + 1;
			if (this.lost > 5) { this.stop("не знаю, где стою (клетка " + this.cur + " не записана)"); return; }
			this.cur = ""; this.poll(); jmc.setTimer(this.timerId, 10); return;
		}
		this.lost = 0;
		var looking = (typeof botCore != "undefined" && botCore.mobsWaitLook && botCore.mobsWaitLook.length > 0);
		if (looking) {
			this.lookWait = (this.lookWait || 0) + 1;
			if (this.lookWait > 16) {                     // ~5 с: моб ушёл, look попал не туда — сбросить очередь бота
				this.out("бот не досмотрел мобов (" + botCore.mobsWaitLook.length + "), иду дальше");
				botCore.mobsWaitLook = new Array();
				looking = false;
			}
		}
		if (!looking) this.lookWait = 0;
		if (this.fight || looking) {
			jmc.setTimer(this.timerId, 3); return;    // бой или бот ещё смотрит мобов — подождать
		}
		if (this.state == "home") {
			if (this.cur == this.start) { this.finish(); return; }
			var h = this.plan(this.start);
			if (!h) { this.stop("не нашла дорогу на старт"); return; }
			this.go(h[0], this.cur); return;
		}
		var p = this.plan(null);
		if (!p) {
			this.out("непройденных выходов нет — иду на старт");
			this.state = "home";
			this.next(); return;
		}
		this.go(p[0], this.cur);
	}

	this.onTimer = function( idTimer )
	{
		idTimer = jmc.event;
		if (idTimer != this.timerId) return;
		jmc.killTimer(this.timerId);
		if (this.state == "aff0" || this.state == "aff") {
			if (!this.affOk) { this.state = ""; this.out("НЕТ ПОЛЁТА (" + this.needAffect + ") — эксплор не запущен"); return; }
			this.state = "run"; this.cur = ""; this.poll(); return;
		}
		if (this.state == "") return;
		if (this.tired) { this.tired = false; this.next(); return; }
		if (this.aw) {                                   // промпт мог быть скрыт осмотром мобов: проверить клетку ещё раз
			this.poll();
			if (!this.aw) return;                        // шаг был — room() уже поставил следующий
		}
		if (this.aw && (this.fight || this.qcleared)) {  // шаг съел бой / очистка очереди — не закрывать выход, повторить
			this.qcleared = false; this.aw = null; this.next(); return;
		}
		if (this.aw) {                                   // шаг не случился за время ожидания
			this.blocked[this.aw.from + "|" + this.aw.key] = "не прошла";
			this.out("не прошла: " + this.aw.from + " " + this.K2D[this.aw.key]);
			this.aw = null;
			if (this.state == "back") { this.stop("не могу вернуться в зону"); return; }
		}
		this.next();
	}

	this.poll = function()
	{
		// значения в одинарных кавычках: в названиях клеток бывают двойные («Магазин "Серебряный Кот"»)
		var v = ["MsdpRoomVnum", "MsdpRoomName", "MsdpRoomArea", "MsdpRoomExitsLength",
			"MsdpRoomExitsKey1", "MsdpRoomExitsValue1", "MsdpRoomExitsKey2", "MsdpRoomExitsValue2", "MsdpRoomExitsKey3", "MsdpRoomExitsValue3",
			"MsdpRoomExitsKey4", "MsdpRoomExitsValue4", "MsdpRoomExitsKey5", "MsdpRoomExitsValue5", "MsdpRoomExitsKey6", "MsdpRoomExitsValue6",
			"MsdpHealth", "MsdpHealthMax", "MsdpMovement", "MsdpMovementMax"];
		var a = [];
		for (var i = 0; i < v.length; i++) a.push(String(jmc.GetVar(v[i])));   // 15.11: GetVar — в названиях бывают и " и ' («Коридор к гильдии 'неистовых'» ломал #scr)
		this.room.apply(this, a);
	}

	this.onIncoming = function( sTextLine )
	{
		if (this.state == "") return sTextLine;
		var s = rmcolor(sTextLine);
		if (this.state == "aff0") { if (/^Аффекты:/.test(s)) this.state = "aff"; return sTextLine; }
		if (this.state == "aff") {
			if (s.indexOf(this.needAffect) >= 0) this.affOk = true;
			if (/\d+H \d+M \d+V/.test(s)) { jmc.killTimer(this.timerId); jmc.setTimer(this.timerId, 1); }
			return sTextLine;
		}
		if (/\d+H \d+M \d+V/.test(s)) {                  // промпт: бой виден по [имя:состояние]
			this.fight = /\]\s*\[/.test(s) || /\[[^\]]+:[^\]]+\]/.test(s);
			this.poll();
		}
		if (this.dangerMobs[this.zone] && this.dangerMobs[this.zone].test(s) && this.rooms[this.cur]) {    // моб-примета ДТ рядом: дальше из этой клетки не идти
			var ex = this.rooms[this.cur].exits;
			for (var dk in ex) if (ex[dk] != this.prevRoom && !this.rooms[ex[dk]]) this.blocked[this.cur + "|" + dk] = "рядом ДТ (" + s.substring(0, 30) + ")";
			this.out("примета ДТ в клетке " + this.cur + " — дальше не иду");
		}
		var np = /^(.+?) не пускает вас/.exec(s);                     // моб не пускает в зону — бить и повторить шаг
		if (np && this.aw) {
			if (/^Город /.test(this.zone) || this.noKill.test(np[1])) {   // в городах и квестовых (noKill) не бить (15.11 Шиар: перебила совет и стражу) — выход закрыть
				this.blocked[this.aw.from + "|" + this.aw.key] = "не пускает: " + np[1];
				this.aw = null; jmc.killTimer(this.timerId); jmc.setTimer(this.timerId, 3);
				return sTextLine;
			}
			this.aw = null; jmc.killTimer(this.timerId);
			this.attack(np[1]); jmc.setTimer(this.timerId, 30);
			return sTextLine;
		}
		var km = this.keyMobs[this.zone];
		if (km && km.test(s) && !/мертв|убежал|ушел|ушла|пришел|пришла/.test(s) && (this.state == "run" || this.state == "home")) {
			var mm = /^([^,.!]+?)\s+(стоит|сидит|охраняет|ходит|летает|парит|лежит|ждет|внимательно|медленно|быстро)/.exec(s);
			if (mm) this.attack(mm[1]);
		}
		if (this.aw && /^Вы слишком устали/.test(s)) {          // кончилась энергия — отдохнуть 30 с, встать, повторить шаг
			this.aw = null; this.tired = true; jmc.killTimer(this.timerId);
			jmc.send(this.moveCmd); this.mvT = (new Date()).getTime(); this.out("устала — " + this.moveCmd);
			jmc.setTimer(this.timerId, 20);
			return sTextLine;
		}
		if (this.aw && /^Очередь команд очищена/.test(s)) {    // после боя игра выкинула наш шаг
			this.qcleared = true; this.aw = null; jmc.killTimer(this.timerId); jmc.setTimer(this.timerId, 5);
		}
		if (this.aw && /^У вас нет нужного ключа\./.test(s)) {
			this.blocked[this.aw.from + "|" + this.aw.key] = "заперто, нет ключа";
			this.aw = null; jmc.killTimer(this.timerId); jmc.setTimer(this.timerId, 3);
		}
		if (this.aw && /^Вы не можете идти в этом направлении/.test(s)) {
			this.blocked[this.aw.from + "|" + this.aw.key] = "нет прохода";
			this.aw = null; jmc.killTimer(this.timerId); jmc.setTimer(this.timerId, 5);
		}
		return sTextLine;
	}

	this.save = function()
	{
		try {
			var dir = this.outDir + "\\" + this.safe(this.zone);
			if (!fso.FolderExists(this.outDir)) fso.CreateFolder(this.outDir);
			if (!fso.FolderExists(dir)) fso.CreateFolder(dir);
			var f = fso.CreateTextFile(dir + "\\клетки.csv", true);
			f.WriteLine("номер;название;выходы;закрыто");
			for (var v in this.rooms) {
				var r = this.rooms[v], ex = [], bl = [];
				for (var k in r.exits) {
					ex.push(this.K2D[k] + "=" + r.exits[k]);
					if (this.blocked[v + "|" + k]) bl.push(this.K2D[k] + ": " + this.blocked[v + "|" + k]);
				}
				f.WriteLine(v + ";" + r.name + ";" + ex.join(",") + ";" + bl.join(","));
			}
			f.Close();
			var g = fso.CreateTextFile(dir + "\\переходы.csv", true);
			g.WriteLine("из;направление;в;зона");
			for (var i = 0; i < this.borders.length; i++) g.WriteLine(this.borders[i]);
			g.Close();
		} catch (e) { this.out("не смогла сохранить: " + e.message); }
	}
	this.finish = function()
	{
		var n = 0; for (var v in this.rooms) n++;
		this.save();
		if (typeof botCore != "undefined" && botCore.enableRecord) botCore.onInput(".бот запись стоп");
		this.state = "";
		this.out("ГОТОВО: " + this.zone + ", клеток " + n + ", переходов " + this.borders.length + ". Файлы: ЗОНЫ\\" + this.safe(this.zone) + "\\, мобы: areas\\эксплор_" + this.safe(this.zone).replace(/\s+/g, "_") + "_mob.csv");
	}
}
var Explore = new ExploreModule();
modules.push(Explore);
jmc.showme("-:- Explore loaded: эксплор / эксплор стоп / эксплор инфо");
