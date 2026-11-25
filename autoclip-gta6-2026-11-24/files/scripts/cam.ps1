param([string]$Stop='WORKDIR\source\stop.flag',[int]$Max=7000,[int]$Test=0)
# Moves the 0 A.D. observer camera by clicking random points on the minimap every 15-40 s.
$code=@'
using System; using System.Runtime.InteropServices;
public class W { [DllImport("user32.dll")] public static extern bool ClientToScreen(IntPtr h, ref POINT p);
 [DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y);
 [DllImport("user32.dll")] public static extern void mouse_event(uint f,int dx,int dy,uint d,UIntPtr e);
 [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
 public struct POINT{public int X,Y;} }
'@
Add-Type $code; [W]::SetProcessDPIAware() | Out-Null
$rnd = New-Object Random 11
$t0 = Get-Date; $log = 'WORKDIR\source\camera_clicks.log'
while (((Get-Date)-$t0).TotalSeconds -lt $Max -and -not (Test-Path $Stop)) {
  $p = Get-Process pyrogenesis -ErrorAction SilentlyContinue | Select -First 1
  if (-not $p) { break }
  $pt = New-Object W+POINT
  $ang = $rnd.NextDouble()*6.2832; $rad = 50*[Math]::Sqrt($rnd.NextDouble())
  $pt.X = [int](127 + $rad*[Math]::Cos($ang)); $pt.Y = [int](600 + $rad*[Math]::Sin($ang))
  [W]::ClientToScreen($p.MainWindowHandle, [ref]$pt) | Out-Null
  [W]::SetCursorPos($pt.X,$pt.Y) | Out-Null
  [W]::mouse_event(2,0,0,0,[UIntPtr]::Zero); Start-Sleep -Milliseconds 80; [W]::mouse_event(4,0,0,0,[UIntPtr]::Zero)
  "$([int]((Get-Date)-$t0).TotalSeconds) $($pt.X) $($pt.Y)" | Add-Content $log
  if ($Test) { break }
  Start-Sleep -Seconds ($rnd.Next(15,40))
}

