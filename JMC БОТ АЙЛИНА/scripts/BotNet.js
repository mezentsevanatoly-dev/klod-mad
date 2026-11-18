/*
	вывод в оутпуты
*/
function BotNetModule(){
	
	this.moduleName 		= "BotNetModule(local)";
	this.lastString			= "";
	
	var	file;
	//if (!fso.FileExists("stream.log")){
		fso.CreateTextFile("stream.log",true);
	//}
	
	file = fso.GetFile("stream.log");

	var sout;// = file.OpenAsTextStream(1)
	var sin;// = file.OpenAsTextStream(2)
	
	this.send = function(text)
	{
		sin = file.OpenAsTextStream(2);
		sin.WriteLine(	(new Date()).getTime()+ text);
		sin.Close();
	}
	
	// обработка исходящих сообщений из jmc ( alias )
	this.onInput = function( sTextLine )
	{
		if (!sTextLine) return sTextLine;
		
		sCommands = sTextLine.split(" ");
		if (sCommands[0] == ".бб" && sCommands[1] )
		{	
			this.send(sTextLine.substr(4));
			return;
		}
		return sTextLine;
	}
	
	jmc.setTimer(101,1);
	this.onTimer = function( idTimer ) {
		idTimer = jmc.event;
		var text;
		if (idTimer==101) {
			sout = file.OpenAsTextStream(1);
			if (!sout.AtEndOfStream) {
				text = sout.ReadLine();
				if (this.lastString!=text){
					jmc.showme ( color(1,36)+"[БотНет]: "+ color(0,0)+ text.substring(13));
					if (jmc.profile=="Kler") jmc.parse(text.substring(13));
					this.lastString=text;
				}
			}
			sout.Close();
			return false;
		}
			
	}
	
	//var objConn = ActiveXObject("winmgmts:NetDiagnostics") 
	//Winsock.SendData("Привет, сервер!")
}

var BotNet = new BotNetModule();
modules.push(BotNet);