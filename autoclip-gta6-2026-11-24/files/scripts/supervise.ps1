param([int]$GoalSec=3900,[int]$MaxHours=3,[int]$StartSeg=1)
# Relaunches the 0 A.D. bot match when the window dies and records every try as its own segment.
$root='WORKDIR'; $log="$root\source\supervisor.log"; $ff='ffmpeg'; $fp='ffprobe'
$t0=Get-Date; $seg=$StartSeg
function Log($m){ "$((Get-Date).ToString('s')) $m" | Add-Content $log }
while (((Get-Date)-$t0).TotalHours -lt $MaxHours) {
  $a='-writableRoot','-autostart=random/mainland',"-autostart-seed=$(6+$seg)",'-autostart-players=6','-autostart-size=256','-autostart-victory=endless','-autostart-player=-1','-nosound','-xres=1280','-yres=720','-conf=windowed:true','-conf=vsync:false'
  1..6 | %{ $a += "-autostart-ai=$($_):petra" }
  $g=Start-Process "$root\0ad\binaries\system\pyrogenesis.exe" -ArgumentList $a -WorkingDirectory "$root\0ad\binaries\system" -PassThru
  Start-Sleep 30
  if ($g.HasExited) { Log "seg$seg game died before recording"; $seg++; continue }
  $out="$root\source\seg$seg.mp4"
  $rec=Start-Process $ff -ArgumentList '-y','-loglevel','error','-f','gdigrab','-framerate','30','-i','"title=0 A.D."','-t','7000','-c:v','libx264','-preset','veryfast','-crf','26','-g','60','-pix_fmt','yuv420p',$out -PassThru -WindowStyle Hidden
  $cam=Start-Process powershell -ArgumentList '-NoProfile','-File',"$root\scripts\cam.ps1",'-Max','7100' -PassThru -WindowStyle Hidden
  Log "seg$seg start game pid $($g.Id) rec pid $($rec.Id) seed $(6+$seg)"
  while (-not $g.HasExited -and -not $rec.HasExited) { Start-Sleep 5 }
  $why = if ($g.HasExited) {'game exited'} else {'recorder ended'}
  Start-Sleep 3
  if (-not $g.HasExited) { Stop-Process -Id $g.Id }
  if (-not $rec.HasExited) { Stop-Process -Id $rec.Id }
  Start-Sleep 2
  if (-not $cam.HasExited) { Stop-Process -Id $cam.Id }
  if (Test-Path "$root\source\camera_clicks.log") { Move-Item "$root\source\camera_clicks.log" "$root\source\seg${seg}_camera_clicks.log" -Force }
  $d = & $fp -v error -show_entries format=duration -of csv=p=0 $out 2>$null
  Log "seg$seg ended ($why) duration $d s"
  if ([double]$d -ge $GoalSec) { Log "GOAL reached with seg$seg"; break }
  $seg++
}
Log "supervisor done"
