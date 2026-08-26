$PythonExe = "C:\Users\Omer\AppData\Local\Programs\Python\Python312\python.exe"
$RepoRoot = "C:\Users\Omer\Desktop\usmle-step1-daily-quiz"
$TaskName = "USMLE Daily Quiz Generator"

$Action = New-ScheduledTaskAction -Execute $PythonExe -Argument "generate.py" -WorkingDirectory $RepoRoot
$Trigger = New-ScheduledTaskTrigger -Daily -At "6:00AM"
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun -DontStopOnIdleEnd
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger `
  -Settings $Settings -Principal $Principal `
  -Description "Generates today's 30 USMLE Step 1 practice questions and pushes them to GitHub Pages." `
  -Force

Write-Host "Registered scheduled task '$TaskName'. Runs daily at 6:00 AM, catches up on next login if missed, wakes the PC if it's asleep (not off) and the hardware supports it."
