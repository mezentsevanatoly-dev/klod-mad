/*
	вывод в оутпуты
*/
function OutputModule(){
	
	this.moduleName 		= "OutputModule";
	
	// обработка исходящих сообщений из jmc ( alias )
	this.onInput = function( sTextLine )
	{
		if (!sTextLine) return sTextLine;
		
		sCommands = sTextLine.split(" ");
		if (sCommands[0] == "/?" && sCommands[1] == "OutputModule")
		{
			jmc.showme ( color(1,36)+"[Справка]: "+ color(0,0)+ "/? " + this.moduleName);
			return;
		}
		return sTextLine;
	}
	
	// обработка входящих в jmc строк ( action )
	this.onIncoming = function( sTextLine )
	{
		sLine=rmcolor(sTextLine); // убираем цвет
		//sLine=sTextLine;
		
		// клан мессаги
		// [      Союзники]: Арамир: чонить
		if (rx(sLine,/^\[([А-Яа-я ]{14})\]: ([А-Я][а-я]*): (.*)$/)){
			jmc.output( color(0,36) +"["+result[1]+"]: "+
						color(1,37)+result[2]+color(0,0)+": "+result[3] );
			//return ; // при раскоменте, мессаги не выводяться в основном окне! %)						
		}
		
		// груп мессаги
		// Вы сказали группе: "тест"
		//if (rx(sLine,/^([А-Яа-я]+|Кто-то) сказа(л|ла|ло|ли) группе: "(.*)"$/)){
		//	jmc.output( color(1,32) +"[        Группа]: "+
		//				color(1,37)+result[1]+color(0,0)+": "+result[3] );
		//}
		
		// приват мессаги
		// Сеймо сказал вам: "?"
		if (rx(sLine,/^([А-Я][а-я]+) сказа(л|ла|ло) (\*{0,1}[А-Я][а-я]+|вам): "(.*)"$/)){
			jmc.output( color(1,36) +result[1]+" сказа"+result[2]+" "+result[3]+": "+result[4] );
		}
		
		return sTextLine;
	}
}

modules.push(new OutputModule());