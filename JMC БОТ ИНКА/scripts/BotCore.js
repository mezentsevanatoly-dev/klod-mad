/*
	вывод в оутпуты
*/

var zons = new Array();
var mobs = new Array();
var seekstep = 0;
var mobcount = 0;
var wTimerCount = 0;
var zonename = "";
var HOLDERS = {"Набожный парнишка": 1, "Скромная прихожанка": 1, "Мужчина с тростью": 1, "Бабушка с клюкой": 1, "Хранитель спокойствия": 1, "Дух безумца": 1, "Бурундук": 1};   // Claude: холдеры церкви: бить обычным `уби`, без заклинания (по логам пользователя)
var GROUP_MIN_LEVEL = {"Кантор": 25};   // Claude: комнаты с этим мобом (группа Кантора) не бить, пока уровень персонажа ниже

function BotModule(){
	
	this.moduleName 		= "BotModule";
	this.enableRecord		= false;
	this.enableBot			= false;
	
	this.waitFlag		= false;
	this.lastStatusInBattle   = false;
	
	this.playerInRoom		= false;
	this.BotInZone		= false;

	this.mobsWaitLook = new Array();

	this.zoneLoopList = new Array(); // список зон
	this.zoneLoopNum = 0;	// текущая зона из списка
	
	this.zoneRepopList = new Array(); // список зон
	this.zoneRepopTimerList = new Array();	// репопы зон
	this.zoneRepopCurTimerList = new Array();	// репопы зон
	this.zoneRepopNum = 0;
	this.zoneRepopHasMobs = false;
	this.zoneRepopListNames = new Array(); // список полных имен зон - заполняется игроком и используется для корректировки репопов по команде “обл”

	
	//валидные мобы в комнате
	this.mobsInRoom	= new Array();
	
	//согрупы
	this.groupPlayerInRoom = new Array();
	this.groupPlayerInLastRoom = new Array();
	this.groupPlayerInRest	= false;
	this.groupPlayerInBattle = false;
	this.groupPlayerInHold	= false;
	this.groupPlayerInBlind	= false;
	
	// обработка исходящих сообщений из jmc ( alias )
	this.onInput = function( sTextLine )
	{
		if (!sTextLine) return sTextLine;
		sCommands = sTextLine.split(" ");
		if (sCommands[0] == ".бот")
		{
			if (sCommands[1]=="?" || sCommands[1] == null)
			{
				jmc.showme ( color(1,36)+"[Справка Bot v.1]"+ color(0,0));
				jmc.showme ( color(0,36)+" .бот ?                        - данная справка"+ color(0,0));
				jmc.showme ( color(0,36)+" .бот инфо                     - информация"+ color(0,0));
				jmc.showme ( color(0,36)+" .бот инфо <имя>               - информация о зоне"+ color(0,0));
				jmc.showme ( color(0,36)+" .бот установить               - устанавливает конфигу бота"+ color(0,0));
				jmc.showme ( color(0,36)+" .бот запись старт <имя>       - начало записи зоны"+ color(0,0));
				jmc.showme ( color(0,36)+" .бот запись стоп              - окончание записи зоны"+ color(0,0));
				jmc.showme ( color(0,36)+" .бот запись сброс             - сброс пути зоны"+ color(0,0));
				jmc.showme ( color(0,36)+" .бот старт <имя>              - включение бота"+ color(0,0));
				jmc.showme ( color(0,36)+" .бот стоп                     - выключение бота"+ color(0,0));
				jmc.showme ( color(0,36)+" .бот круг <зона1> ... <зонаN> - цикличный маршрут бота"+ color(0,0));
				jmc.showme ( color(0,36)+" .бот круг стоп                - остановка маршрута бота"+ color(0,0));
				jmc.showme ( color(0,36)+" .бот репоп                    - список репопа"+ color(0,0));
				jmc.showme ( color(0,36)+" .бот репоп + <зона> <время>    - добавление в репоп"+ color(0,0));
				jmc.showme ( color(0,36)+" .бот репоп - <зона>            - удаление из репопа"+ color(0,0));
			}
			
			if (sCommands[1]=="установить" && sCommands[2] == null)
			{
				jmc.showme ( color(1,36)+"[Настройка цветовых установок бота...]"+ color(0,0));
				jmc.send("статус сброс");
				jmc.send("цвет 1 8 ярко.розов");
				jmc.send("цвет 1 6 голубой");
			}
			
			if (sCommands[1]=="инфо" && sCommands[2] == null)
			{
				jmc.showme ( color(1,36)+"[Инфо Bot v.1]"+ color(0,0));
				jmc.showme ( color(0,36)+"     Хп: "+player.hp+ color(0,0));
				jmc.showme ( color(0,36)+"   Мувы: "+player.vp+ color(0,0));
				jmc.showme ( color(0,36)+"    ДСУ: "+player.xexp+ color(0,0));
				jmc.showme ( color(0,36)+" Монеты: "+player.gold+ color(0,0));
				jmc.showme ( color(0,36)+"Комната: "+player.roomname+ color(0,0));
			}
			
			if (sCommands[1]=="инфо" && sCommands[2]!=null)
			{
				jmc.showme ( color(1,36)+"[Информация о зоне "+sCommands[2]+"]"+ color(0,0));
				jmc.showme ( color(0,36)+"     Клеток: "+zons.length+ color(0,0));
				jmc.showme ( color(0,36)+"      Мобов: "+mobcount+ color(0,0));
			}
			
			if (sCommands[1]=="запись" && sCommands[2]=="старт")
			{
				if (!sCommands[3]) {
					jmc.showme ( color(1,31)+"[Ошибка: Введите название зоны]"+ color(0,0));					 
					 return;
				}
				zons = new Array();
				mobs = new Array();
				this.mobsWaitLook = new Array();
				mobcount = 0;
				zonename = sCommands[3];
				this.enableRecord = true;
				jmc.showme ( color(1,36)+"[Начата запись зоны: "+sCommands[3]+"]"+ color(0,0));
			}
			
			if (sCommands[1]=="запись" && sCommands[2]=="стоп")
			{
				this.enableRecord = false;
				jmc.showme ( color(1,36)+"[Окончена запись зоны: "+zonename+"]"+ color(0,0));
				jmc.showme ( color(0,36)+"  Сохранено "+zons.length+" комнат"+color(0,0));
				
				// сохраняем в файл
				this.saveZone(zonename);
			}
			
			if (sCommands[1]=="запись" && sCommands[2]=="сброс")
			{
				zons = new Array();
				mobs = new Array();
				mobcount = 0;
				this.mobsWaitLook = new Array();
				jmc.showme ( color(0,36)+"Запись зоны сброшена"+color(0,0));
			}
			
			if (sCommands[1]=="старт")
			{
				if (!sCommands[2]) {
					jmc.showme ( color(1,31)+"[Ошибка: Введите название зоны]"+ color(0,0));
					return;
				}
				var param = 2;
				while(sCommands[param]){
					if (this.loadZone(sCommands[param])) {
						if (!this.enableBot){
							jmc.showme ( color(1,36)+"[Бот включен: иду зону '"+sCommands[param]+"']"+color(0,0));
							jmc.parse("СтатСтарт "+sCommands[param]);
						}else {
							jmc.showme ( color(1,36)+"[Бот: в очередь добавленна зона '"+sCommands[param]+"']"+color(0,0));
						}
					}
					this.enableBot = true;
					param++;
				}
				if (typeof ClaudeLog != "undefined") ClaudeLog.note("BOT_START zone=" + zonename + " steps=" + zons.length); // Claude: перед стартом зоны проверить аффекты, при отсутствии вампиризма выпить эликсир летучей мыши
				this.vampCheck = true; this.vampHdr = false; this.vampSeen = false;
				jmc.send("сч");
				this.stuffCheck = true; this.stuffHdr = false; this.stuffW = false;
				jmc.send("экипировка");
				//this.nextStep();
				jmc.send("look краткий");
			}
			
			if (sCommands[1]=="стоп")
			{
				this.enableBot = false;
				if (typeof ClaudeLog != "undefined") ClaudeLog.note("BOT_STOP step=" + seekstep + "/" + zons.length); jmc.showme ( color(0,36)+"Бот отключен"+color(0,0));
				jmc.parse("СтатСтоп ОШИБКА");
			}
			
			if (sCommands[1]=="круг")
			{
				if (sCommands[2]=="стоп") 
				{
					this.zoneLoopList = new Array(); // список зон
					this.zoneLoopNum = 0;	// текущая зона из списка
					jmc.showme ( color(1,36)+"[Круговое вырезание зон остановленно]"+color(0,0));
					return;
				}
				jmc.showme ( color(1,36)+"[Задан круг зон]"+color(0,0));
				jmc.showme ( color(0,36)+" Список зон в круге:"+color(0,0));
				var i=2;
				
				this.zoneLoopList = new Array(); // список зон
				this.zoneLoopNum = 0;	// текущая зона из списка
	
				while(sCommands[i]){
					this.zoneLoopList.push(sCommands[i]);
					jmc.showme ( color(0,33)+" - "+sCommands[i]+color(0,0));
					i++;
				}
				
				if (this.loadZone(this.zoneLoopList[this.zoneLoopNum])) 
				{
					this.enableBot = true;
					jmc.send("look краткий");
				}
			}
			
			if (sCommands[1]=="репоп")
			{
			
				if (sCommands[2]=="+" && (!sCommands[3] || !sCommands[4])) {
					jmc.showme ( color(1,36)+"[Ошибка: формат команды - .бот репоп + <зона> <время_репопа>]"+color(0,0));
				}else
				if (sCommands[2]=="+" && sCommands[3] && sCommands[4]) 
				{
					jmc.setTimer(102,600); // таймер репопера				
				
					jmc.showme ( color(1,36)+"[Репоп: добавлена зона "+sCommands[3]+"]"+color(0,0));
					this.zoneRepopList.push(sCommands[3]);
					this.zoneRepopTimerList.push(sCommands[4]);
					this.zoneRepopCurTimerList.push(0);
				
					return;
				}
				
				if (sCommands[2]=="-" && !sCommands[3]) {
					jmc.showme ( color(1,36)+"[Ошибка: формат команды - .бот репоп - <зона>]"+color(0,0));
				}else
				if (sCommands[2]=="-" && sCommands[3]) 
				{
					jmc.showme ( color(1,36)+"[Репоп: убрана зона "+sCommands[3]+"]"+color(0,0));
					
					var tmpZoneCount = this.zoneRepopList.length;
					for(var ii=0;ii<tmpZoneCount;ii++) {
					
					 	var tmpZoneName = this.zoneRepopList.shift();
						var tmpZoneTimer = this.zoneRepopTimerList.shift();
						var tmpZoneCurTimer = this.zoneRepopCurTimerList.shift();
						
						if (tmpZoneName != sCommands[3]) 
						{ 
							this.zoneRepopList.push(tmpZoneName);
							this.zoneRepopTimerList.push(tmpZoneTimer);
							this.zoneRepopCurTimerList.push(tmpZoneCurTimer);
						}

					}
					
					return;
				}
				
				jmc.showme ( color(1,36)+"[Список репопа зон]"+color(0,0));
				jmc.showme ( color(1,33)+"  № Наименование                   | Время репопа | до репопа|Серверный ID"+color(0,0));
				jmc.parse( "#out "+ color(1,36)+"[Список репопа зон]"+color(0,0));
				jmc.parse( "#out "+ color(1,33)+"  № Наименование                   | Время репопа | до репопа|Серверный ID"+color(0,0));
				

				var tab1,tab2;
				var i=0;
				
				jmc.showme ( "#scr botCore.zoneRepopCurTimerList[N] = T");
				jmc.parse( "#out #scr botCore.zoneRepopCurTimerList[N] = T");
				while(this.zoneRepopList[i]){
					tab1 = "";
					tab2 = "";
					tab3 = "       ";
					while((tab1.length+this.zoneRepopList[i].length)-30<0) tab1+=" ";
					while((tab2.length+this.zoneRepopTimerList[i].length)-12<0) tab2+=" ";
				// Добавлено выравнивание. Спасибо Славе (Нарред, Хашаган)
				if( i < 10 ) {
								jmc.showme ( color(0,33)+ "  " + i + " "+this.zoneRepopList[i]+tab1+
											" | "+this.zoneRepopTimerList[i]+tab2+ 
											" | "+this.zoneRepopCurTimerList[i]+tab3+
											" | " + this.zoneRepopListNames[i] +color(0,0));
								jmc.parse( "#out " + color(0,33)+ "  " + i + " "+this.zoneRepopList[i]+tab1+
											" | "+this.zoneRepopTimerList[i]+tab2+ 
											" | "+this.zoneRepopCurTimerList[i]+tab3+
											" | " + this.zoneRepopListNames[i] +color(0,0));
																						
				} else {
						jmc.showme ( color(0,33)+ " " + i + " "+this.zoneRepopList[i]+tab1+
						" | "+this.zoneRepopTimerList[i]+tab2+
						" | "+this.zoneRepopCurTimerList[i]  + tab3 +
						" | " + this.zoneRepopListNames[i] +color(0,0));
						jmc.parse( "#out " + color(0,33)+ " " + i + " "+this.zoneRepopList[i]+tab1+
						" | "+this.zoneRepopTimerList[i]+tab2+
						" | "+this.zoneRepopCurTimerList[i]  + tab3 +
						" | " + this.zoneRepopListNames[i] +color(0,0));
						}
					i++;
				}
			}
			
			return;
		}
		
		// команды бота
		// 

		if (sCommands[0] == ".пауза" && this.enableBot) 
		{
			jmc.showme("[Пауза "+sCommands[1]/10.0+" секунд]");
			this.wait(sCommands[1]);
			return;
		}
		
		// перехват при записи				
		if (sCommands[0] == ".пауза" && this.enableRecord) 
		{
			jmc.showme("[Пауза "+sCommands[1]/10.0+" секунд]");
			zons.push(sTextLine);
			return;
		}
		
		
		if ((sCommands[0] == "север" || sCommands[0] == "с" ) && this.enableRecord) 
		{
			zons.push("север");
			this.mobsWaitLook = new Array();
		}
		
		if ((sCommands[0] == "запад" || sCommands[0] == "з" ) && this.enableRecord) 
		{
			zons.push("запад");
			this.mobsWaitLook = new Array();
		}
		
		if ((sCommands[0] == "восток" || sCommands[0] == "в" ) && this.enableRecord) 
		{
			zons.push("восток");
			this.mobsWaitLook = new Array();
		}
		
		if ((sCommands[0] == "юг"  || sCommands[0] == "ю" ) && this.enableRecord) 
		{
			zons.push("юг");
			this.mobsWaitLook = new Array();
		}
		
		if ((sCommands[0] == "вверх" || sCommands[0] == "вв" ) && this.enableRecord) 
		{
			zons.push("вверх");
			this.mobsWaitLook = new Array();
		}
		
		if ((sCommands[0] == "вниз" || sCommands[0] == "вн" ) && this.enableRecord) 
		{
			zons.push("вниз");
			this.mobsWaitLook = new Array();
		}
		
		if (sCommands[0] == ".триг" && this.enableRecord) 
		{
			sTextLine = sTextLine.replace(/^(\.триг )/,"");
			log(sTextLine);
			zons.push(".триг "+sTextLine);
		}
		
		return sTextLine;
	}
	
	// обработка входящих в jmc строк ( action )
	this.onIncoming = function( sTextLine )
	{
		sLine=rmcolor(sTextLine); // убираем цвет
		//sLine=sTextLine;
		// Claude: список аффектов после .бот старт: нет вампиризма -> осуш мыш
		if (rx(sLine,/^Вы .+, .+ (\d+) уровня\./)) { this.myLevel = parseInt(result[1], 10); }
		// Claude: одиночный ход отклонён боем ("Не получится!...") -> шаг не засчитан, повторить; составные шаги (с у 2.) не трогаем
		if (this.enableBot && this.lastStepPure && rx(sLine,/^Не получится! Вы сражаетесь за свою жизнь!/)) {
			if ((new Date()).getTime() - this.lastStepTime < 4000 && seekstep > 0) {
				seekstep--;
				this.lastStepPure = false;
				jmc.showme('-:- Ход не прошёл (бой), повторяю шаг ' + seekstep); if (typeof ClaudeLog != "undefined") ClaudeLog.note("MOVE_BLOCKED_BATTLE step=" + seekstep);
			}
		}
		var mflee = sLine.match(/^Бурундук убежал на (север|юг|запад|восток|вверх|вниз)\./);
		if (mflee) { this.chaseOnFlee(mflee[1]); }
		else if (this.chase && /^Бурундук мертв\./.test(sLine)) { this.chaseEnd(); }
		if (this.stuffCheck) {
			if (rx(sLine,/^Вы используете:/)) { this.stuffHdr = true; }
			else if (this.stuffHdr && rx(sLine,/<(в обеих руках|в правой руке|держится в правой руке)>/)) { this.stuffW = true; }
			else if (this.stuffHdr && rx(sLine,/^\d+H \d+M \d+V/)) {
				this.stuffCheck = false; this.stuffHdr = false;
				if (!this.stuffW) { jmc.showme('-:- Оружия в руках нет, беру'); jmc.send('воор новый'); }
				else { jmc.showme('-:- Оружие в руках'); }
			}
		}
		if (this.vampCheck) {
			if (rx(sLine,/^Аффекты:/)) { this.vampHdr = true; }
			else if (this.vampHdr && rx(sLine,/вампиризм/i)) { this.vampSeen = true; }
			else if (this.vampHdr && rx(sLine,/^\d+H \d+M \d+V/)) {
				this.vampCheck = false; this.vampHdr = false;
				if (!this.vampSeen) { jmc.showme('-:- Вампиризма нет, пью эликсир'); jmc.send('осуш мыш'); }
				else { jmc.showme('-:- Вампиризм есть'); }
			}
		}
		
				// Я ДОБАВИЛ
		// Создан экземпляр зоны 'Больница Геоланта'.
		if (rx(sLine,/^(Создан экземпляр зоны|Для вас уже создан активный экземпляр зоны|Вы сможете создать новый экземпляр зоны) (.+)/)){
			this.zoneRepopHasMobs = true;
			this.BotInZone		= true; // ФЛАГ ВХОДА В ЗОНУ
			this.zoneRepopCurTimerList[this.zoneRepopNum] = this.zoneRepopTimerList[this.zoneRepopNum];
			return sTextLine;
		};	
		
//Вы произнесли магические слова
//^([А-Яа-я \-\.\,]+) героически спас вас
		if (rx(sLine,/^([А-Яа-я \-\.\,]+) героически спас вас/)){
			if (this.enableBot) { 
					jmc.send("очистить;вст;пом");
					this.wait(50);
			};
			return sTextLine;
		};	
		if (rx(sLine,/^Вы([а-я ]+)произнесли магические слова/)){
			if (this.enableBot) { 
			this.wait(30);
			};
			return sTextLine;
		};	

		if (rx(sLine,/^([А-Яа-я \-]+) удар([а-я]+) вас ногой!/)){
			if (this.enableBot) { 
			this.wait(30);
			};
			return sTextLine;
		};	
		// Я ДОБАВИЛ

		if (rx(sTextLine,/^Вы не можете идти в этом направлении.../)){
			if (this.enableRecord) {
				zons.pop();
			}
			//return ; // при раскоменте, мессаги не выводяться в основном окне! %)						
		}
		
		if (sTextLine=="" && this.mobsWaitLook.length>0) return GAG_EVENT;
		
		return sTextLine;
	}
	
	this.onRoom = function( sTextLine ) 
	{
		sLine = rmcolor(sTextLine);
		
		// сохранение прошлых 
		this.groupPlayerInLastRoom = this.groupPlayerInRoom;
		
		// сброс переменных
		this.playerInRoom = false;
		this.groupPlayerInRest	= false;
		this.groupPlayerInHold	= false;
		this.groupPlayerInBattle = false;
		this.groupPlayerInBlind	= false;
		
		if (this.enableRecord) 
			sTextLine += color(1,31)+" [Комната №"+zons.length+" записана]";
		
		if (this.enableBot) {
			sTextLine += color(1,31)+" [РЕЖИМ БОТА]"+color(0,36)+" ("+seekstep+"/"+zons.length+")"+color(1,30);
			this.mobsInRoom	= new Array();
			this.skipRoom = false;
			this.groupPlayerInRoom = new Array();
		}
		return sTextLine;
	}
	
	this.onRoomMob = function( sTextLine , numInRoom ) 
	{
		mobLookName = rmcolor(sTextLine);
		
		// Удаляем из имени моба все, что после точки изи воск.  (аффекты, флай, санки и т.п.)
		mobLookName = mobLookName.replace(/[ ]+\.\.\.(.+)$/,"");
		mobLookName = mobLookName.replace(/\.(.+)$/,".");
		mobLookName = mobLookName.replace(/\!(.+)$/,"!");
		mobLookName = mobLookName.replace(/\s+$/,"");   // Claude: сравнение без пробелов на конце
		//jmc.showme ("[" + mobLookName + "]");
		//jmc.parse("магр");


		if (this.enableRecord){ 
		//	mobLookName = rmcolor(sTextLine);
			if(mobs[mobLookName]!=null){
				sTextLine += color(1,32)+" [ "+mobs[mobLookName].name+" ("+mobs[mobLookName].prof+" "+mobs[mobLookName].level+", "+mobs[mobLookName].race+") ]"+color(1,35);
			}else {
				sTextLine += color(1,32)+" [ Запоминаю моба "+numInRoom+". ]"+color(1,35);
				this.lookLoreMob(mobLookName,numInRoom);
				mobcount++;
			}
		}

		// при ключеном боте
		if (this.enableBot) { 
		//	mobLookName = rmcolor(sTextLine);
			if (mobs[mobLookName]==null){
				if (this.BotInZone) {jmc.parse ("#wout 5 [Моб не в целях]-[" + zonename + "]-[" + mobLookName + "]");}
				return sTextLine;
			} else {
				sTextLine+= color(1,32)+" ("+mobs[mobLookName].level+")"+color(1,35);
			}
			
			if (typeof GROUP_MIN_LEVEL != "undefined" && GROUP_MIN_LEVEL[mobs[mobLookName].name] && this.myLevel > 0 && this.myLevel < GROUP_MIN_LEVEL[mobs[mobLookName].name]) { this.skipRoom = true; }
			if ( mobs[mobLookName].flags=="" )
				this.mobsInRoom.push(mobLookName);
			
		}
		
		return sTextLine;
	}
	
	this.onRoomPlayer = function( sTextLine ) 
	{
		sLine = rmcolor(sTextLine);
		if (this.enableRecord) {
			sTextLine += color(1,33)+" [ Игрок ]"+color(1,31);
		}
		if (this.enableBot) {
			sTextLine += color(1,33)+" [ Игрок ]"+color(1,31);
			this.playerInRoom = true;
		}
		return sTextLine;
	}
	
	this.onRoomGroupPlayer = function( sTextLine ) 
	{
		sLine = rmcolor(sTextLine);
		if (this.enableRecord) {
			sTextLine += color(0,33)+" [ Группа ]"+color(0,36);
		}
		if (this.enableBot) {
		
			// добавляет в переменную согрупников в комнате
			this.groupPlayerInRoom.push(result[1]);

			if (rx(sLine,/^([А-Яа-я \-\.\,]+) (\.\.\.обезд[а-я]+)/)) {
				jmc.send("гг Согрупник в холде!");
				this.groupPlayerInHold	= true;
			}
			// сидит ли согрупник?
			if (rx(sLine,/^([А-Яа-я \-\.\,]+) (сидит) здесь./)) {
				this.groupPlayerInRest	= true;
			}
			// в холде ли согрупник?

			// слеп ли согруп? //т здесь. ...слепа .
			if (rx(sLine,/^([А-Яа-я \-\.\,]+) (\.\.\.сле[а-я]+)/)) {
				this.groupPlayerInBlind	= true;
			}
			// в бою ли согрупник? 
			if (rx(sLine,/^([А-Яа-я \-\.\,]+) здесь\, сражается с ([А-Яа-я \-\.\,]+).*/)) {
				this.groupPlayerInBattle = true;
			}

			sTextLine += color(0,33)+" [ Группа ]"+color(0,36);
		}
		return sTextLine;
	}
	
	
	this.onStatus = function ( sTextLine, isRoom )
	{
		if (this.enableBot && !this.waitFlag) {
			
			if ( isRoom  ) { //&& !player.isBattle
			
			// обработка
				if (this.groupPlayerInBattle){
					jmc.send("вали;гг !фраг;гг !пом;помочь");
					this.wait(25);
					return sTextLine;
				}
				if (this.groupPlayerInHold){
					jmc.send("гговорить где расхолд, че спим;пом;бгр");
					this.wait(25);
					return sTextLine;
				}
				if (this.groupPlayerInBlind){
					jmc.send("гговорить Снять слепоту! Не спим!;пом;бгр;гг !кол слов.свет");
					this.wait(25);
					return sTextLine;
				}
				if (this.groupPlayerInRest){
					jmc.send("гговорить ! вст;пом");
					this.wait(25);
					return sTextLine;
				}
				if (player.vp < countMinVp) {
					jmc.send("отдых");
					this.wait(300);
					seekstep--;
					zons[seekstep] = ".триг встать";
					return sTextLine;
				}
				
				 if (this.groupPlayerInRoom.length < this.groupPlayerInLastRoom.length ) { //&&
					jmc.parse("#showme - = БотДумаетЧтоНасМало = -;бгр");
					this.wait(25);
					//	zons[seekstep-1].split(" ")[0]!=".триг") {
					// this.reverseStep();
					// jmc.send("кол м.восс");
					// this.wait(25);
					// //jmc.send("гг рест");
					// //jmc.send("отдых");
					// this.wait(300);
					// seekstep--;
					// zons[seekstep] = ".триг гг вст";
					// seekstep--;
					// zons[seekstep] = ".триг встать";
					return sTextLine;
				}
				
				
				// агрим моба 
				// && player.hp > player.maxhp*(percentMinHp/100.0) 
				// && !this.playerInRoom 
				if (this.mobsInRoom.length > 0  && this.BotInZone && !this.skipRoom) {
					this.zoneRepopHasMobs = true;
					this.wait(25);
					//player.isBattle = true;
					this.lastStatusInBattle = true;
					var mk = mobs[this.mobsInRoom[0]].name;
					if (HOLDERS[mk]) { jmc.parse("уби "+mk.replace(" ",".")); } else { jmc.parse("kill "+mk.replace(" ",".")); }	
					return sTextLine;
				}
				if (!player.isBattle) {this.nextStep();}
			}
		
			if ( !player.isBattle && this.lastStatusInBattle ) {
				// бой окончен
				//this.nextStep(); 
				jmc.send("look краткий");
			}		
		
			this.lastStatusInBattle =  player.isBattle;
		
		}
		
		if (this.mobsWaitLook.length>0 && this.enableRecord) return GAG_EVENT;
		
		return sTextLine;
	}
	
	
	// Claude: погоня за убегающим бурундуком (запомнить путь, добить, вернуться на маршрут)
	this.chase = null;
	this.chaseRev = {"север": "юг", "юг": "север", "запад": "восток", "восток": "запад", "вверх": "вниз", "вниз": "вверх"};
	this.chaseOnFlee = function( dir )
	{
		if (!this.enableBot) return;
		if (!this.chase) this.chase = {dirs: [], tries: 0, phase: "go", back: []};
		if (this.chase.dirs.length >= 8) { this.chaseEnd(); return; }
		this.chase.dirs.push(dir);
		this.chase.tries = 0;
		this.chase.phase = "go";
		this.wait(80);
		jmc.send(dir);
		jmc.setTimer(152, 15);
		jmc.showme('-:- Бурундук убежал на ' + dir + ', иду за ним');
	};
	this.chaseEnd = function()
	{
		var c = this.chase;
		if (!c || c.phase == "back") return;
		c.phase = "back";
		c.back = [];
		for (var i = c.dirs.length - 1; i >= 0; i--) c.back.push(this.chaseRev[c.dirs[i]]);
		this.wait(60);
		jmc.setTimer(152, 15);
	};
	this.chaseTick = function()
	{
		jmc.killTimer(152);
		var c = this.chase;
		if (!c) return;
		if (c.phase == "go") {
			jmc.send("уби бурундук");
			c.phase = "hit";
			jmc.setTimer(152, 25);
		} else if (c.phase == "hit") {
			if (c.tries < 3) { c.tries++; jmc.send("уби бурундук"); this.wait(60); jmc.setTimer(152, 25); }
			else { this.chaseEnd(); }
		} else if (c.phase == "back") {
			var d = c.back.shift();
			if (d) { jmc.send(d); this.wait(40); jmc.setTimer(152, 15); }
			else { this.chase = null; jmc.send("look краткий"); }
		}
	};
	this.nextStep = function()
	{
		if (zons.length>seekstep) {
			var command = zons[seekstep];
			// 15.11 Claude: шаг из клетки N, а стоим в другой (ход прошёл, а бот посчитал, что нет: бой, «Не получится!») —
			// найти рядом в маршруте (±15, сначала вперёд) шаг из текущей клетки и идти с него; иначе как раньше (ждать, назад на 2)
			var mvn = /MsdpRoomVnum == (\d+)\}/.exec(command), curv = String(jmc.GetVar("MsdpRoomVnum"));
			if (mvn && curv && mvn[1] != curv) {
				var best = -1;
				for (var dd = 1; dd <= 15 && best < 0; dd++) {
					var cands = [seekstep + dd, seekstep - dd];
					for (var ci = 0; ci < 2; ci++) {
						var kk = cands[ci];
						if (kk >= 0 && kk < zons.length && zons[kk].indexOf("MsdpRoomVnum == " + curv + "}") >= 0) { best = kk; break; }
					}
				}
				if (best >= 0) {
					if (typeof ClaudeLog != "undefined") ClaudeLog.note("RESYNC step " + seekstep + " -> " + best + " vn=" + curv);
					seekstep = best; command = zons[seekstep];
				}
			}
			sCommands = command.split(" ");
			if (sCommands[0] == ".пауза" && sCommands[1] > 0 ) {
				this.wait(sCommands[1]);
				seekstep++;
				return;
			}
			if (sCommands[0] == ".триг" && sCommands[1] ) {
				this.wait(5);
				command = command.replace(/^(\.триг )/,"");
			}
			if (typeof ClaudeLog != "undefined") jmc.parse("#scr ClaudeLog.step(" + seekstep + ",$MsdpRoomVnum)");
			this.lastStepTime = (new Date()).getTime();
			this.lastStepWasMove = /(^|;)(север|юг|запад|восток|вверх|вниз)(;|$)/.test(command);
			this.lastStepPure = /^(север|юг|запад|восток|вверх|вниз)$/.test(command) || /\{(север|юг|запад|восток|вверх|вниз)\}\s*$/.test(command);
			jmc.parse(command);
			seekstep++;
		} else {
			// кончилось, вырубаем
			this.onEndZone();
		}
	}
	
	this.reverseStep = function()
	{
		if (seekstep>0) {
			var command = zons[seekstep-1];
			sCommands = command.split(" ");
			if (sCommands[0] == ".пауза" && sCommands[1] > 0 ) {
				this.wait(sCommands[1]);
				return;
			}
			if (sCommands[0] == ".триг" && sCommands[1] ) {
				this.wait(5);
				command = command.replace(/^(\.триг )/,"");
			}
			jmc.showme(command);
			if (command=="север" ) {
				command = "юг";
			} else 
			
			if (command=="юг" ) {
				command = "север";
			} else 
			
			if (command=="запад" ) {
				command = "восток";
			} else 
			
			if (command=="восток" ) {
				command = "запад";
			} else 
			
			if (command=="вверх" ) {
				command = "вниз";
			} else 
			
			if (command=="вниз" ) {
				command = "вверх";
			}
			
			jmc.send(command);
			seekstep--;
		} else {
			// кончилось, вырубаем
			this.onEndZone();
		}
	}
	
	this.lookLoreMob = function(mobLookName,numInRoom)
	{
		jmc.send("look "+numInRoom+".");
		newMob = new Mob("");
		newMob.nameInLook = mobLookName;
		this.mobsWaitLook.push(mobLookName);
		mobs[newMob.nameInLook] = newMob;
	}
	
	// получения осмотра моба
	this.onLookMob = function ( sTextLine, lookLineType, rxresult )
	{
		//sTextLine += " ["+lookLineType+"]";
		// конец описания
		if (!this.enableRecord) return sTextLine;
		
		gagflag = (this.mobsWaitLook.length>0);
		
		if (gagflag) {
			
			// первая строка
			if (lookLineType==0) {
					//jmc.showme(">"+this.mobsWaitLook[0]);
					mobs[this.mobsWaitLook[0]].name = rxresult[1];
					mobs[this.mobsWaitLook[0]].level = rxresult[2];
					mobs[this.mobsWaitLook[0]].prof = rxresult[3];
			}
			
			// хиты моба
			if (lookLineType==2) {
					//jmc.showme(">"+this.mobsWaitLook[0]);
					mobs[this.mobsWaitLook[0]].hp = rxresult[1];
					mobs[this.mobsWaitLook[0]].maxhp = rxresult[2];
					mobs[this.mobsWaitLook[0]].mp = rxresult[3];
					mobs[this.mobsWaitLook[0]].maxmp = rxresult[4];
			}
			// Навыки
			if (lookLineType==3) {
				mobs[this.mobsWaitLook[0]].skills = rxresult[1];
			}
					
			//Особенности: 
			if (lookLineType==7) {
				mobs[this.mobsWaitLook[0]].flags = rxresult[1];
			}
			
			// раса
			if (lookLineType==4) {
				mobs[this.mobsWaitLook[0]].race = rxresult[1];
			}
			
			//конец
			if (lookLineType==1) { 		
				this.mobsWaitLook.shift();
				//jmc.showme("Осталось:"+this.mobsWaitLook.length);
			}
		
		}
		if (gagflag) return GAG_EVENT;
		return sTextLine;
	}
	
	
	this.onEndZone =function()
	{
		this.enableBot = false;
		if (typeof ClaudeLog != "undefined") ClaudeLog.note("ZONE_END zone=" + zonename + " steps=" + zons.length); jmc.showme ( color(1,36)+"[Бот: зона '"+zonename+"' закончена]"+color(0,0));
		jmc.parse("СтатСтоп "+zonename);
		if (this.zoneRepopList.length!=0) {
		
			if (this.zoneRepopHasMobs) {
				//this.zoneRepopCurTimerList[this.zoneRepopNum] = this.zoneRepopTimerList[this.zoneRepopNum];
			} else {
				this.zoneRepopCurTimerList[this.zoneRepopNum] = 10;
			}
			// обработчик репопов
			for(var i=0;i<this.zoneRepopCurTimerList.length;i++){
				if (this.zoneRepopCurTimerList[i]<=0) {
					if (!this.enableBot) {
						//идем зону
						if (this.loadZone(this.zoneRepopList[i])) 
						{
							this.zoneRepopHasMobs = false;
							this.zoneRepopNum = i;
							jmc.showme( color(1,36)+"[Репоп: иду '"+this.zoneRepopList[i]+"']"+color(0,0));
							jmc.parse("СтатСтарт "+this.zoneRepopList[i]);
							this.zoneRepopCurTimerList[i]=this.zoneRepopTimerList[i];
							this.enableBot = true;
							jmc.send("look краткий");
						}
					}
				}
			}
			
			return;
		}
		
		if (this.zoneLoopList.length!=0){		
			this.zoneLoopNum++;
			this.zoneLoopNum=this.zoneLoopNum%this.zoneLoopList.length;
			jmc.showme ( color(1,36)+"[Круг: иду '"+this.zoneLoopList[this.zoneLoopNum]+"']"+color(0,0));
			if (this.loadZone(this.zoneLoopList[this.zoneLoopNum])) 
			{
				this.enableBot = true;
				jmc.send("look краткий");
			}
		}
		
	}
	
	this.saveZone = function(filename)
	{
		var	file;
		var wLine = "";
		//  запись путей
		file = fso.CreateTextFile("areas/"+filename+".botp",true);
		while(zons.length>0){	
			file.WriteLine(zons.shift());
		}
		file.Close();
		
		// запись мобов
		file = fso.CreateTextFile("areas/"+filename+"_mob.csv",true);
		
// шапка таблицы
		wLine = '"Имя моба"';
		wLine = wLine+";"+'"Описание в комнате"';
		wLine = wLine+";"+'"Hp"';
		wLine = wLine+";"+'"MaxHp"';
		wLine = wLine+";"+'"Mp"';
		wLine = wLine+";"+'"MaxMp"';
		wLine = wLine+";"+'"Опыт"';
		wLine = wLine+";"+'"Деньги"';
		wLine = wLine+";"+'"Уровень"';
		wLine = wLine+";"+'"Агрессивность"';
		wLine = wLine+";"+'"Ассистит?"';
		wLine = wLine+";"+'"Умения"';
		wLine = wLine+";"+'"Профессия"';
		wLine = wLine+";"+'"Раса"';
		wLine = wLine+";"+'"Флаги NPC"';
		file.WriteLine(wLine); 
		
// сохранение записей		
		for(var i in mobs){	
			if (!mobs.hasOwnProperty(i)) continue;
			wLine = '"'+mobs[i].name+'"';
			wLine = wLine+";"+'"'+mobs[i].nameInLook+'"';
			wLine = wLine+";"+'"'+mobs[i].hp+'"';
			wLine = wLine+";"+'"'+mobs[i].mp+'"';
			wLine = wLine+";"+'"'+mobs[i].maxhp+'"';
			wLine = wLine+";"+'"'+mobs[i].maxmp+'"';
			wLine = wLine+";"+'"'+mobs[i].exp+'"';
			wLine = wLine+";"+'"'+mobs[i].gold+'"';
			wLine = wLine+";"+'"'+mobs[i].level+'"';
			wLine = wLine+";"+'"'+mobs[i].isAgro+'"';
			wLine = wLine+";"+'"'+mobs[i].isAssist+'"';
			wLine = wLine+";"+'"'+mobs[i].skill+'"';
			wLine = wLine+";"+'"'+mobs[i].prof+'"';
			wLine = wLine+";"+'"'+mobs[i].race+'"';
			wLine = wLine+";"+'"'+mobs[i].flags+'"';
			file.WriteLine(wLine); 
		}
		file.Close();
	}
	
	this.loadZone = function(filename)
	{
		var	file;
		var rLine = "";
		var rArray;
		if(!fso.fileExists("areas/"+filename+".botp") ||
           !fso.fileExists("areas/"+filename+"_mob.csv")) {
		
			jmc.showme ( color(1,31)+"[Ошибка: зоны с таким именем не найденно]"+color(0,0));
			return false;
		}
		
		if (!this.enableBot)
		{
			zons = new Array();
			mobs = new Array();
			seekstep = 0;
			mobcount = 0;
		}
		
		
		zonename = filename;
		
		//  загрузка путей
		file = fso.OpenTextFile("areas/"+filename+".botp");
		while(!file.AtEndOfStream){
			zons.push(file.ReadLine());
		}
		file.Close();
		
		// загрузка мобов
		file = fso.OpenTextFile("areas/"+filename+"_mob.csv");
		
		rLine = file.ReadLine();
		
		while(!file.AtEndOfStream){
			var newMob = new Mob("");
			rLine = file.ReadLine();
			rLine = rLine.replace(/"/g,'');
			rArray = rLine.split(";");
			newMob.name = rArray[0];
			newMob.nameInLook = rArray[1].replace(/\s+$/,"");   // Claude: в csv описание с пробелом на конце, а строка комнаты приходит без него
			newMob.hp = rArray[2];
			newMob.mp = rArray[3];
			newMob.maxhp = rArray[4];
			newMob.maxmp = rArray[5];
			newMob.exp = rArray[6];
			newMob.gold = rArray[7];
			newMob.level = rArray[8];
			newMob.isAgro = rArray[9];
			newMob.isAssist = rArray[10];
			newMob.skill = rArray[11];
			newMob.prof = rArray[12];
			newMob.race = rArray[13];
			newMob.flags = rArray[14];

			mobs[newMob.nameInLook] = newMob;	
		
			//jmc.showme(newMob.name+" loaded.");
		}
		file.Close();
	
		return true;
	}
		
	this.wait = function(sec){
		this.waitFlag=true;
		jmc.setTimer(100,sec);
		wTimerCount = sec;
		//jmc.showme("battle_lock");
	}
	
	this.onTimer = function( idTimer ) {
		idTimer = jmc.event;
		if (idTimer == 152) { this.chaseTick(); return; }
		//jmc.showme(idTimer);
		if (wTimerCount >1) {
			wTimerCount = wTimerCount - 1;
			jmc.parse("#stat 1 Пауза: "+wTimerCount/10+" сек.");
			// jmc.showme(wTimerCount);
			}
		
		if (idTimer==100) {
			
			// обработчик команды wait
			this.waitFlag=false;
			jmc.killTimer(100);
			jmc.parse("#stat 1 - - - - - -");
			this.lastStatusInBattle =  player.isBattle;
			if (!player.isBattle) jmc.send("look краткий");
			//jmc.showme("battle_unlock");
		}
		
		if (idTimer==102) {
			// обработчик репопов
			for(var i=0;i<this.zoneRepopCurTimerList.length;i++){
				this.zoneRepopCurTimerList[i]--;
				if (this.zoneRepopCurTimerList[i]<=0) {
					if (this.zoneRepopCurTimerList[i]==0)
						jmc.showme("repop: "+this.zoneRepopList[i]);
					if (!this.enableBot && !this.waitFlag) { // ДОПИСАТЬ ВЕЙТ
						//идем зону
						if (this.loadZone(this.zoneRepopList[i])) 
						{
							this.zoneRepopHasMobs = false;
							this.zoneRepopNum = i;
							jmc.showme( color(1,36)+"[Репоп: иду '"+this.zoneRepopList[i]+"']"+color(0,0));
							jmc.parse("СтатСтарт "+this.zoneRepopList[i]);
							this.zoneRepopCurTimerList[i]=this.zoneRepopTimerList[i];
							this.enableBot = true;
							jmc.send("look краткий");
						}
					}
				}
			}
		}
	}
}

var botCore = new BotModule();
modules.push(botCore);