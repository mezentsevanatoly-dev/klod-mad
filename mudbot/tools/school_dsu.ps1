# Мад школа: после 4 лвл (inc_run start2 4) продолжить охоту, пока ДСУ (поле X в приглашении) > 60, потом стоп своего процесса по PID.
$bot = "C:\Users\User\Desktop\Клод мад\mudbot"
Set-Location $bot
$env:MUD_VIA = 'bot'
$first = [int](Get-Content tools\run_lvl.pid)
while (Get-Process -Id $first -ErrorAction SilentlyContinue) { Start-Sleep 5 }
$p = Start-Process python -ArgumentList '-X','utf8','tools/inc_run.py','start2','5','--here','--noentry' -RedirectStandardOutput tools\run_start2b.log -RedirectStandardError tools\run_start2b.err -PassThru -WindowStyle Hidden
$p.Id | Out-File tools\run_lvl.pid
while (Get-Process -Id $p.Id -ErrorAction SilentlyContinue) {
    $tail = Get-Content out.log -Tail 40 -Encoding UTF8 | Out-String
    $m = [regex]::Matches($tail, 'X(\d+)X')
    if ($m.Count -gt 0 -and [int]$m[$m.Count - 1].Groups[1].Value -le 60) {
        Stop-Process -Id $p.Id -Force
        "стоп по ДСУ: " + $m[$m.Count - 1].Groups[1].Value | Out-File tools\school_dsu.log
        break
    }
    Start-Sleep 3
}
