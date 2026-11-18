// сброс цветов
function rmcolor( sLine ) {
	sLine  = sLine.replace(/\[\d+;\d+m/g,"");
	sLine = sLine.replace(/\[\d+m/g,"");
	return sLine;
}

// регул€рные выражени€
var result;
function rx(str,regexp) 
{
	if (regexp.test(str)) {
		result = regexp.exec(str);
		return true;
	}
	return false;
}