function AutoReconnect()
{
	var ReconTimerCount = 0;
	this.moduleName = "AutoReconnect";
	this.TimerSleepID = 10;
	this.TimerSleep = 120;			// время между проверками соединения с сервером, в секундах
	this.TimerWaitAnswerID = 11;
	this.TimerWaitAnswer = 10;		// время ожидания ответа от сервера, в секундах

	this.onIncoming = function( sTextLine )
	{
		sLine=rmcolor(sTextLine);
		jmc.parse( "#stat 5 " + this.TimerSleep);
		//if( rx( sLine, /Вых:/ ) )
		//if( rx( sLine, /абыр/ ) )
		if ( (rx(sTextLine,/^\[1;36m([А-Яа-я \"\.\-]+)/) ||
			  rx(sTextLine,/^\[36m([А-Яа-я \"\.\-]+)/) ) && !this.roomLook)

		{
			jmc.killTimer( this.TimerSleepID );
			jmc.setTimer( this.TimerSleepID, this.TimerSleep*10 );
			ReconTimerCount = this.TimerSleep*10
			jmc.killTimer( this.TimerWaitAnswerID );
			//jmc.showme( "-:- Процедура проверки связи с сервером запущена." );
		}
		
		return sTextLine;
    }
	
	this.onTimer = function( idTimer )
		
	{
		idTimer = jmc.event;
		
		ReconTimerCount = ReconTimerCount - 1;
		jmc.parse("#stat 5 Р: "+ReconTimerCount/10+" сек.");
			// jmc.showme(wTimerCount);
		
		if( idTimer == this.TimerSleepID ){
			jmc.killTimer( this.TimerSleepID );
			jmc.setTimer( this.TimerSleepID, this.TimerSleep*10 );
			jmc.killTimer( this.TimerWaitAnswerID );
			jmc.setTimer( this.TimerWaitAnswerID, this.TimerWaitAnswer*10 );
			jmc.showme( "-:- Проверка связи с сервером." );
			jmc.parse( "look краткий" );
		}
		
		if( idTimer == this.TimerWaitAnswerID ){
			jmc.killTimer( this.TimerWaitAnswerID );
			jmc.showme( "-:- Нет ответа от сервера... Переподключение." );
			jmc.parse( "рекон" );
		}
		if (ReconTimerCount <-600) {
		jmc.showme( "-:- Нет ответа от сервера... Переподключение." );
		jmc.parse("рекон");
		ReconTimerCount = -550
		// jmc.showme(wTimerCount);
		}
	}
}	

var Test = new AutoReconnect();
modules.push(Test);
jmc.showme ("-:- AutoReconnect scripts(v1.0)...  Done! [Timers ID: 10, 11]");