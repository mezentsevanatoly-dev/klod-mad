// ClaudeLog: autolog. Every incoming game line and every typed command goes to claude_game.log (CURRENT JMC LAUNCH ONLY) and Logs\game_YYYY-MM-DD_N.log (one file per launch).
// JMC's own #log writes 0 bytes on this build. Re-including this file replaces the previous copy (no double lines).
for (var ci = modules.length - 1; ci >= 0; ci--) {
	if (modules[ci].moduleName == "ClaudeLog") modules.splice(ci, 1);
}
function ClaudeLogModule()
{
	this.moduleName = "ClaudeLog"; this.curDay = null;
	this.pad = function( n ) { return (n < 10 ? "0" : "") + n; }
	// Каждый запуск JMC = свой лог: claude_game.log очищается и содержит только этот запуск,
	// история запуска — Logs\\game_ДАТА_N.log (N — следующий свободный номер).
	this.sessFile = null;
	this.openSession = function()
	{
		var d = new Date();
		var day = d.getFullYear() + "-" + this.pad(d.getMonth() + 1) + "-" + this.pad(d.getDate());
		var n = 1;
		while (fso.FileExists("Logs\\game_" + day + "_" + n + ".log")) n++;
		this.sessFile = "Logs\\game_" + day + "_" + n + ".log";
		var t0 = fso.CreateTextFile("claude_game.log", true); t0.Close();
		var t1 = fso.CreateTextFile(this.sessFile, true); t1.Close();
	}
	this.write = function( prefix, text )
	{
		try {
			if (this.sessFile == null) this.openSession();
			var d = new Date();
			var line = this.pad(d.getHours()) + ":" + this.pad(d.getMinutes()) + ":" + this.pad(d.getSeconds()) + " " + prefix + text;
			var f = fso.OpenTextFile("claude_game.log", 8, true);
			f.WriteLine(line);
			f.Close();
			var g = fso.OpenTextFile(this.sessFile, 8, true);
			g.WriteLine(line);
			g.Close();
		} catch (e) {}
	}
	this.note = function( msg ) { this.write("## ", msg); }
	// bot step with the MSDP room vnum it was sent from (called from BotCore.nextStep)
	this.step = function( idx, vn ) { this.write("## STEP ", idx + " vn=" + vn + " cmd=" + (typeof zons != "undefined" ? zons[idx] : "?")); }
	// ClaudeStartup: settings that must be applied after the profile (дкаре.set) is loaded, every JMC start
	this.startupTimerId = 150;
	this.onTimer = function( idTimer )
	{
		idTimer = jmc.event;
		if (idTimer == 151) {
			jmc.killTimer(151);
			if (this.blind && this.blindTries < 3) { this.blindTries++; jmc.send("осуш прозр"); jmc.setTimer(151, 40); }
		}
		if (idTimer == this.startupTimerId) {
			jmc.killTimer(this.startupTimerId);
			jmc.parse("#group disable resc");
			jmc.parse("#var pWeapon новый");
			jmc.parse("#alias {еда} {#3 осуш насыщ} {default}");
			jmc.parse("#alias {кн} {#3 осуш насыщ} {default}");
			jmc.parse("#alias {kill} {#var AcTarget %1;уби %1} {SET}");
			jmc.parse("#alias {mkill} {#var AcTarget %1;уби %1} {SET}");
			this.note("ClaudeStartup applied: group resc off, pWeapon=новый, blind action");
		}
	};
	this.onInput = function( sTextLine ) { this.write(">> ", sTextLine); return sTextLine; }
	this.blind = false; this.blindTries = 0; this.avatarT = 0;
	this.afterAvatar = function() { return (new Date()).getTime() - this.avatarT < 15000; }
	// вызывается триггером на «Вы ослепли!» из конфига: после перехода Аватары прозрение не тратить
	this.onBlind = function() { if (this.afterAvatar()) { this.note("слепота после Аватары — не снимаю"); return; } jmc.send("осуш прозр"); }
	this.onIncoming = function( sTextLine )
	{
		var s = rmcolor(sTextLine);
		this.write("", s);
		if (/^Мир вокруг вас искривился/.test(s)) this.avatarT = (new Date()).getTime();   // переход Аватары: слепота пройдёт сама
		if (!this.noBlind && /^Вы ослепли!/.test(s) && !this.afterAvatar()) { this.blind = true; this.blindTries = 0; jmc.setTimer(151, 15); }
		if (/^Вы прозрели!/.test(s)) { this.blind = false; jmc.killTimer(151); }
		return sTextLine;
	}
}
var ClaudeLog = new ClaudeLogModule();
modules.push(ClaudeLog);
jmc.setTimer(ClaudeLog.startupTimerId, 80);  // ClaudeStartup in ~8 s
jmc.showme("-:- ClaudeLog (autolog) loaded -> claude_game.log, Logs\\game_DATE.log");