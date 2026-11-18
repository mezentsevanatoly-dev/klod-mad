/*
	StatZones
    v.1.0: + StatZones(), .onInput(), .Log()
    v.1.1: ~ .Log() - Date()
    v.1.2.: ~ .onInput() - showme, Н1+К2, счетчик простоя
    v.1.3.: ~ .onInput() - добавил возможность установки имеющихся с собой денег через команду .стат установить монеты
*/
// Глобальные пермеменые

var Exp_Per_Sec = 0;
var Gold_Per_Sec = 0;

function StatZones()
{
	this.moduleName 		= "StatZones";
    this.moduleVersion      = "1.1";
    this.moduleColor        = 36;
    
    var date;
    var time;
    var timeZZZ = 0;
    var zone = "";
    var money;
    var temp_exp;
	// player.xexp
    this.onInput = function( sTextLine )
	{
        if( !sTextLine ) return sTextLine;
		sCommands = sTextLine.split(" ");
        // jmc.showme("-:- 0:" + sCommands[0] + ", 1:" + sCommands[1] + ", 2:" + sCommands[2] + ", 3:" + sCommands[3]);
        if( sCommands[0] == ".стат" )
		{
            if( sCommands[1] == "?" || sCommands[1] == null )
			{
                jmc.showme( color(1,this.moduleColor) + "[Справка " + this.moduleName + " v." + this.moduleVersion + "]"+ color(0,0) );
                jmc.showme( color(1,this.moduleColor) + ".стат стартзон ЗОНА" + color(0,0) );
                jmc.showme( color(1,this.moduleColor) + ".стат стопзон ЗОНА" + color(0,0) );
                jmc.showme( color(1,this.moduleColor) + ".стат установить монеты - для ручной установки отсчета монет" + color(0,0) );
            }
            if( sCommands[1] == "стартзон" && sCommands[2] == null )
			{
                jmc.showme( color(1,this.moduleColor)+"-:- Статистику для какой зоны вы хотите начать?"+ color(0,0) );
                jmc.showme( color(1,this.moduleColor)+"-:- Использование: .стат старт ЗОНА"+ color(0,0) );
            }
            if( sCommands[1] == "стартзон" && sCommands[2] != null )
			{
                if( zone != "" ) // "НН+К"
                {
                    money = player.gold - money;
					temp_exp =  temp_exp - player.xexp;
                    jmc.showme( color(1,this.moduleColor)+ "-:-  Зона <" + zone + "> не пройдена! "+  " (+" + money + "монет)" + color(0,0) );
					jmc.showme( color(1,this.moduleColor)+ "-:-  Зона <" + zone + "> не пройдена! "+  " (+" + temp_exp + "Экспы)" + color(0,0) );
                    this.Log( zone, -1, money, temp_exp );
                }
                zone = sCommands[2];
                money = player.gold;
				temp_exp = player.xexp;
                date = new Date();
                jmc.showme( color(1,this.moduleColor)+"-:- " + date + ": Начато прохождение зоны <" + zone + ">" + color(0,0) );
                // счетчик простоя
                if( timeZZZ )
                {
                    timeZZZ = (new Date() - timeZZZ) / 1000;
                    this.Log( "ПРОСТОЙ", timeZZZ, 0 );
                    timeZZZ = 0;
                }
            }
            if( sCommands[1] == "стопзон" && sCommands[2] == null )
			{
                jmc.showme( color(1,this.moduleColor)+"-:- Статистику для какой зоны вы хотите остановить?"+ color(0,0) );
                jmc.showme( color(1,this.moduleColor)+"-:- Использование: .стат стоп ЗОНА"+ color(0,0) );
            }
            if( sCommands[1] == "стопзон" && sCommands[2] != null )
			{
                if( zone == "" ) // защита от некорректного использования - "К"
                {
                    jmc.showme( color(1,this.moduleColor)+"-:- " + new Date() + ": Но зона <" + zone + "> не была начата!"+  color(0,0) );
                    return -1;
                }
                if( sCommands[2] != zone ) // защита от некорректного использования - "Н1+К2"
                {
                    //jmc.showme( color(1,this.moduleColor)+"-:- " + new Date() + ": Начата зона <" + zone + ">, а закончена другая зона - <"+ sCommands[2] + "> " + color(0,0) );
                    jmc.showme( color(1,this.moduleColor)+"-:- Начата зона <" + zone + ">, а закончена другая зона - <"+ sCommands[2] + "> " + color(0,0) );

					zone = "Н1+К2"; // для обработки "Н1+К2+К1", теоретически возможной при ручном использовании
                    return -1
                }
                time = (new Date() - date) / 1000;
                money = player.gold - money;
				temp_exp =  temp_exp - player.xexp;
				Gold_Per_Sec = Math.round(money/time);
				Exp_Per_Sec = Math.round(temp_exp/time);
				
                //jmc.showme( color(1,this.moduleColor)+"-:- " + new Date() + "<" + sCommands[2] + "> -> "+ time + " (+" + money + " с)"+" (ГПС:"+ Gold_Per_Sec+")"+ color(0,0) );
                jmc.showme( color(1,this.moduleColor)+"-:- Конец зоны <" + sCommands[2] + "> -> "+ time + " (+" + money + " с)"+" (ГПС:"+ Gold_Per_Sec+")"+ color(0,0) );
				jmc.showme( color(1,this.moduleColor)+"-:- Конец зоны <" + sCommands[2] + "> -> "+ time + " (+" + temp_exp + " М)"+" (ЭПС:"+ Exp_Per_Sec+")"+ color(0,0) );

                this.Log( zone, time, money, temp_exp );
                zone = "";
                // счетчик простоя
                timeZZZ = new Date();
            }
            // Установка имеющихся денег через ввод - .триг ск раилданэль Вышел_в_Зону -> #act {^Вы сказали Раилданэль: "Вышел_в_Зону"} {.стат установить монеты}
            if( sCommands[1] == "установить" && sCommands[2] == "монеты" )
            {
				money = player.gold;
				temp_exp = player.xexp;
				jmc.showme("-:- Установлено значение монет: "+money);
				jmc.showme("-:- Установлено значение Эхкспы: "+temp_exp);
            }            
        }
        
        return sTextLine;
    }
    
    this.Log = function( zone, time, money, temp_exp)
    {
        var	file;
        file = fso.OpenTextFile( "StatZonesLog.csv", 8 );
        
        var wLine = '';

        var date = new Date();
        wLine = '"' + date.getFullYear();
        wLine += '";"' + ( date.getMonth() + 1 );
        wLine += '";"' + date.getDate();
        wLine += '";"' + date.getHours();
        wLine += ':' + date.getMinutes();
        wLine += ':' + date.getSeconds();

        wLine += '";"' + zone;
        if( time < 0 )
        {
            wLine += '";"Ошибка"';
        } else {
			Gold_Per_Sec = Math.round(money/time);
			Exp_Per_Sec = Math.round(temp_exp/time);
            wLine += '";"' + time + '";"' + money + '";"' + Gold_Per_Sec + '";"' + temp_exp + '";"' + Exp_Per_Sec + '"';
        }
        
        file.WriteLine( wLine );
        file.Close();
        //OutMoney = player.gold-1000;
		//jmc.send("дать "+OutMoney+" раилданэль");

    }
}
var Stat = new StatZones();
modules.push(Stat);
jmc.showme ("-:- [StatZones] scripts(v1.3)...  Done!");