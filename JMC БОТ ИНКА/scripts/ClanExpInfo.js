/*
	ClanExpInfo
*/
function ClanExpInfoModule(){

	this.moduleName 		= "ClanExpInfoModule";

	this.clanExpCount 		= new Array();
	this.clanMemberCount	= new Array();
	
	this.nextIsLine			= false;
	this.dbIsEmpty			= true;
	// обработка исходящих сообщений из jmc ( alias )
	this.onInput = function( sTextLine )
	{
		if (!sTextLine) return sTextLine;
		
		sCommands = sTextLine.split(" ");
		if (sCommands[0] == ".инфо" )
		{	
			jmc.showme ( color(1,36)+"[Информация]"+color(0,0));
			return;
		}
		return sTextLine;
	}
	
	// обработка входящих в jmc строк ( action )
	this.onIncoming = function( sTextLine )
	{
		sLine=rmcolor(sTextLine); // убираем цвет
		//sLine=sTextLine;
		
		if (rx(sLine,/^     Название клана      Опыт   Численность$/))
		{
			sTextLine += "   +Опыт  +Игроки";
			this.nextIsLine=true;
			return sTextLine;
		}
		
		if (this.nextIsLine && rx(sLine,/^--------------------------------------------$/))
		{
			sTextLine += "-----------------";
			return sTextLine;
		}
		
		// строка таблицы
		//  21. Гвардия Света      20298MX     12
		if (/*this.nextIsLine &&*/ rx(sLine,/^[ 0-9]{3}. ([А-Яа-я ]+)([0-9]+)(|k|M)X ([ 0-9]+)$/)){
			this.nextIsLine=true;
			var tab1="",tab2="";
			
			var addexp = (result[2]-this.clanExpCount[result[1]]);
			var addmem = (result[4]-this.clanMemberCount[result[1]]);
			
			if (this.dbIsEmpty) {
				this.load();
			//	addexp = 0;
			//	addmem = 0;
			}
			
			if (addexp>0) addexp="+"+addexp;
			if (addmem>0) addmem="+"+addmem;
			
			while((tab1.length+addexp.toString().length)-11<0) tab1+=" ";
			while((tab2.length+addmem.toString().length)-6<0) tab2+=" ";
			
			sTextLine += " "+tab1+((result[3]=="")?" ":"")+((addexp>0)?color(1,32):((addexp<0)?color(1,31):""))+addexp+result[3]+"X"+color(0,0)+
					     " "+tab2+((addmem>0)?color(1,32):((addmem<0)?color(1,31):""))+addmem+color(0,0);
			
			this.clanExpCount[result[1]] = result[2];
			this.clanMemberCount[result[1]] = result[4];
			//return ; // при раскоменте, мессаги не выводяться в основном окне! %)		

			return sTextLine;			
		}
		
		if (this.nextIsLine && rx(sLine,/^\[<Enter> - показать следующую страницу, <к> - закончить показ\]$/))
		{
			this.nextIsLine = false;
			//jmc.showme("END");
			this.save();
			return sTextLine;
		}
		
		if (this.nextIsLine)
		{
			this.dbIsEmpty =false;
			this.nextIsLine= false;
			//jmc.showme("END");
			this.save();
			return sTextLine;
		}
		
		return sTextLine;
	}
	
	
	this.save = function()
	{
		var	file;
		var wLine = "";
		// запись мобов
		file = fso.CreateTextFile("ClanExp.csv",true);
		
		// шапка таблицы
		wLine = '"Клан"';
		wLine = wLine+";"+'"Опыт"';
		wLine = wLine+";"+'"Игроки"';
		file.WriteLine(wLine); 
		
		// сохранение записей		
		for(var clanName in this.clanExpCount){	
			if (!this.clanExpCount.hasOwnProperty(clanName)) continue;
			wLine = '"'+clanName+'"';
			wLine = wLine+";"+'"'+this.clanExpCount[clanName]+'"';
			wLine = wLine+";"+'"'+this.clanMemberCount[clanName]+'"';
			file.WriteLine(wLine); 
		}
		file.Close();
	}
	
	this.load = function()
	{
		var	file;
		var rLine = "";
		var rArray;
		if(!fso.fileExists("ClanExp.csv")) {
			this.dbIsEmpty=true;
		}
		this.dbIsEmpty=false;
	
		// загрузка записей
		file = fso.OpenTextFile("ClanExp.csv");
		
		rLine = file.ReadLine();
		
		while(!file.AtEndOfStream){
			rLine = file.ReadLine();
			rLine = rLine.replace(/"/g,'');
			rArray = rLine.split(";");
			this.clanExpCount[rArray[0]]=rArray[1];
			this.clanMemberCount[rArray[0]]=rArray[2];
		}
		file.Close();
	}
	
}

modules.push(new ClanExpInfoModule());