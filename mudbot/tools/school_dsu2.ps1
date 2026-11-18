Set-Location 'C:\Users\User\Desktop\Клод мад\mudbot'
while (Get-Process -Id 20024 -ErrorAction SilentlyContinue) {
  $t = Get-Content out.log -Tail 40 -Encoding UTF8 | Out-String
  $m = [regex]::Matches($t, 'X(\d+)X')
  if ($m.Count -gt 0 -and [int]$m[$m.Count-1].Groups[1].Value -le 60) { Stop-Process -Id 20024 -Force; 'stop dsu ' + $m[$m.Count-1].Groups[1].Value | Out-File tools\school_dsu.log; break }
  Start-Sleep 3
}
