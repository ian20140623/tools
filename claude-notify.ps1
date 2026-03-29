$input_json = [Console]::In.ReadToEnd()
$data = $input_json | ConvertFrom-Json

$cwd = $data.cwd
$project = if ($cwd) { Split-Path $cwd -Leaf } else { "Unknown" }
$type = $data.notification_type

$title = switch ($type) {
    "permission_prompt" { "$project - Allow?" }
    "idle_prompt"       { "$project - Done" }
    default             { "$project - Attention" }
}

$body = switch ($type) {
    "permission_prompt" { "Waiting for permission" }
    "idle_prompt"       { "Ready for next instruction" }
    default             { "Needs your attention" }
}

Add-Type -AssemblyName System.Windows.Forms
$balloon = New-Object System.Windows.Forms.NotifyIcon
$balloon.Icon = [System.Drawing.SystemIcons]::Information
$balloon.BalloonTipTitle = $title
$balloon.BalloonTipText = $body
$balloon.Visible = $true
$balloon.ShowBalloonTip(5000)
Start-Sleep -Milliseconds 5500
$balloon.Dispose()
