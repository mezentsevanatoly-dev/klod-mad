/*
	Мост Claude <-> JMC. Claude дописывает строки в claude\inbox.txt, модуль шлёт их в игру
	только после команды «/клод on». Весь вывод игры (без цветов) пишется в claude\out.log.
	Ввод пользователя (в том числе логин и пароль) в out.log не пишется.
	Подключение (один раз за запуск JMC): #scr include("scripts/ClaudeBridge.js")   (НЕ #read: это JS, а не .set)
*/
function ClaudeBridgeModule(){

	this.moduleName = "ClaudeBridgeModule";
	this.dir        = "claude";
	this.inbox      = "claude\\inbox.txt";
	this.outLog     = "claude\\out.log";
	this.timerID    = 777;
	this.enabled    = false;   // по умолчанию строки из inbox в игру не уходят
	this.consumed   = 0;       // сколько строк inbox уже обработано

	this.ensureFiles = function()
	{
		if (!fso.FolderExists(this.dir)) fso.CreateFolder(this.dir);
		if (!fso.FileExists(this.inbox)) fso.CreateTextFile(this.inbox, true).Close();
		if (!fso.FileExists(this.outLog)) fso.CreateTextFile(this.outLog, true).Close();
	}

	this.readInbox = function()
	{
		var lines = [];
		var f = fso.OpenTextFile(this.inbox, 1, false);
		while (!f.AtEndOfStream) lines.push(f.ReadLine());
		f.Close();
		return lines;
	}

	this.log = function(text)
	{
		var f = fso.OpenTextFile(this.outLog, 8, true);
		f.WriteLine(text);
		f.Close();
	}

	// новые строки из inbox: в игру (если разрешено) или в лог как заблокированные
	this.poll = function()
	{
		var lines = this.readInbox();
		if (lines.length < this.consumed) this.consumed = lines.length;   // файл очистили
		while (this.consumed < lines.length)
		{
			var line = lines[this.consumed++];
			if (!line) continue;
			if (this.enabled)
			{
				jmc.send(line);
				this.log("[claude] " + line);
			}
			else
			{
				this.log("[claude (заблокировано, /клод on)] " + line);
			}
		}
	}

	// весь вывод игры в лог, без цветов
	this.onIncoming = function(sTextLine)
	{
		this.log(sTextLine.replace(/\x1b?\[\d+(;\d+)*m/g, ""));
		return sTextLine;
	}

	// управление из окна JMC: /клод on | /клод off
	this.onInput = function(sTextLine)
	{
		if (sTextLine == "/клод on")
		{
			this.enabled = true;
			jmc.showme("[Claude: строки из claude\\inbox.txt уходят в игру]");
			return;
		}
		if (sTextLine == "/клод off")
		{
			this.enabled = false;
			jmc.showme("[Claude: строки из claude\\inbox.txt не отправляются]");
			return;
		}
		return sTextLine;
	}

	this.onTimer = function(idTimer)
	{
		idTimer = jmc.event;
		if (idTimer == this.timerID)
		{
			this.poll();
			jmc.killTimer(this.timerID);
			jmc.setTimer(this.timerID, 10);   // 1 с (единица таймера 100 мс)
			return false;
		}
	}

	this.ensureFiles();
	this.consumed = this.readInbox().length;   // старые строки не выполнять
	jmc.setTimer(this.timerID, 10);
}

modules.push(new ClaudeBridgeModule());