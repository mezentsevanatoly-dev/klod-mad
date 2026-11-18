Set-Location 'C:\Users\User\Desktop\Клод мад\mudbot'
$env:MUD_VIA='bot'
for($i=0;$i -lt 100;$i++){ Start-Sleep 5; $r = python -X utf8 tools/cmd.py "где|2" 2>&1 | Select-String "cur"; if("$r" -match "Геолант"){ break } }
python -X utf8 tools/trip.py в:гео_склад
python -X utf8 tools/inc_run.py привы1 14 --here --seq
