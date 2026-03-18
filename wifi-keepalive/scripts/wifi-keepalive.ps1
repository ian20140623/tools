# wifi-keepalive.ps1
# iPhone 個人熱點 keep-alive + auto-reconnect
# 用法: powershell -ExecutionPolicy Bypass -File wifi-keepalive.ps1

# ── 設定 ──────────────────────────────────────────
$SSIDs            = @("Kyle’s iPhone (2)")  # iPhone 熱點 SSID，可放多個
$PingIntervalSec  = 10               # 每次檢查間隔（秒）
$PingTimeoutMs    = 2000             # ping 逾時（毫秒）
$FailThreshold    = 3                # 連續 ping 失敗幾次判定斷線
$LogDir           = Join-Path $PSScriptRoot "..\logs"
# ── 設定結束 ──────────────────────────────────────

# 確保 log 目錄存在
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }

# Log 檔：每天一個
function Get-LogPath {
    Join-Path $LogDir "disconnect_$(Get-Date -Format 'yyyy-MM-dd').csv"
}

function Write-Log {
    param([string]$Event, [string]$Detail)
    $logPath = Get-LogPath
    $needHeader = -not (Test-Path $logPath)
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss'),$Event,$Detail"
    if ($needHeader) {
        "timestamp,event,detail" | Out-File -FilePath $logPath -Encoding utf8
    }
    $line | Out-File -FilePath $logPath -Encoding utf8 -Append
}

function Get-WifiSSID {
    $output = netsh wlan show interfaces
    foreach ($line in $output) {
        if ($line -match '^\s*SSID\s*:\s*(.+)$') {
            return $Matches[1].Trim()
        }
    }
    return $null
}

function Test-TargetSSID {
    param([string]$CurrentSSID)
    return $SSIDs -contains $CurrentSSID
}

function Get-Gateway {
    $route = Get-NetRoute -DestinationPrefix "0.0.0.0/0" -ErrorAction SilentlyContinue |
             Sort-Object -Property RouteMetric |
             Select-Object -First 1
    if ($route) { return $route.NextHop }
    return $null
}

function Invoke-Reconnect {
    param([string]$TargetSSID)
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 斷線偵測，正在重連 $TargetSSID ..."
    $start = Get-Date
    netsh wlan connect name="$TargetSSID" | Out-Null

    # 等待重連，最多 30 秒
    $connected = $false
    for ($i = 0; $i -lt 15; $i++) {
        Start-Sleep -Seconds 2
        if (Test-TargetSSID (Get-WifiSSID)) {
            $connected = $true
            break
        }
    }

    $elapsed = [math]::Round(((Get-Date) - $start).TotalSeconds, 1)
    if ($connected) {
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 重連成功（${elapsed}s）"
        Write-Log "reconnect_ok" "${elapsed}s ssid=$TargetSSID"
    } else {
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 重連失敗（${elapsed}s）"
        Write-Log "reconnect_fail" "${elapsed}s ssid=$TargetSSID"
    }
    return $connected
}

# ── 主迴圈 ────────────────────────────────────────

$ssidList = $SSIDs -join ", "
Write-Host "wifi-keepalive 啟動"
Write-Host "  SSID: $ssidList"
Write-Host "  間隔: ${PingIntervalSec}s / 逾時: ${PingTimeoutMs}ms / 門檻: ${FailThreshold}次"
Write-Host "  Log:  $LogDir"
Write-Host "  Ctrl+C 停止"
Write-Host ""

Write-Log "start" "SSIDs=$ssidList interval=${PingIntervalSec}s threshold=$FailThreshold"

$failCount = 0
$lastSSID = $SSIDs[0]  # 斷線時優先重連最近用過的

while ($true) {
    $currentSSID = Get-WifiSSID

    if (-not (Test-TargetSSID $currentSSID)) {
        # 沒連到任何目標 SSID
        if ($currentSSID) {
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 目前連到 $currentSSID，非目標 SSID"
        } else {
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Wi-Fi 未連線"
        }
        Write-Log "disconnect" "currentSSID=$currentSSID"
        $failCount = 0
        Invoke-Reconnect -TargetSSID $lastSSID | Out-Null
    } else {
        $lastSSID = $currentSSID
        # 已連到目標 SSID，ping 閘道
        $gw = Get-Gateway
        if (-not $gw) {
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 找不到閘道，跳過本輪"
            $failCount++
        } else {
            $ping = Test-Connection -ComputerName $gw -Count 1 -TimeoutSeconds ([math]::Ceiling($PingTimeoutMs / 1000)) -ErrorAction SilentlyContinue
            if ($ping) {
                # ping 成功，重置計數
                if ($failCount -gt 0) {
                    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ping $gw OK（恢復）"
                }
                $failCount = 0
            } else {
                $failCount++
                Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ping $gw 失敗（$failCount/$FailThreshold）"
                if ($failCount -ge $FailThreshold) {
                    Write-Log "disconnect" "ping_fail_${FailThreshold}x gateway=$gw ssid=$currentSSID"
                    $failCount = 0
                    Invoke-Reconnect -TargetSSID $currentSSID | Out-Null
                }
            }
        }
    }

    Start-Sleep -Seconds $PingIntervalSec
}
