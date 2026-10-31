# InOneLine operator auto-diagnostic, Windows PowerShell 5.1+
# Put this PS1 and Start_InOneLine_AutoTest.cmd next to InOneLine.exe.
# Makes no simulated events in the user's database. Reports contain no chat text.
param([switch]$SkipTwitch, [switch]$NoPrompt)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$desktop = [Environment]::GetFolderPath('Desktop')
if (-not $desktop -or -not (Test-Path $desktop)) { $desktop = $env:TEMP }
$reportRoot = Join-Path $desktop ('InOneLine_AutoTest_' + $stamp)
New-Item -ItemType Directory -Path $reportRoot -Force | Out-Null
$results = New-Object 'System.Collections.Generic.List[object]'
$exe = Join-Path $PSScriptRoot 'InOneLine.exe'
$scriptVersion = 'v1.2-csv'
$started = [DateTime]::UtcNow
$live = $null
$base = $null
$port = $null

function Record([string]$test, [string]$status, [string]$info) {
    $results.Add([pscustomobject]@{ test = $test; status = $status; info = $info })
    Write-Host ('[{0}] {1} - {2}' -f $status,$test,$info)
}
function Probe([string]$url) {
    try {
        $r = Invoke-WebRequest -Uri $url -TimeoutSec 4 -UseBasicParsing
        return ($r.StatusCode -eq 200)
    } catch { return $false }
}
function ApiJson([string]$url) {
    return Invoke-RestMethod -Uri $url -TimeoutSec 4
}
function WaitPidExit([int]$id,[int]$seconds) {
    $limit = [DateTime]::UtcNow.AddSeconds($seconds)
    while ([DateTime]::UtcNow -lt $limit) {
        if (-not (Get-Process -Id $id -ErrorAction SilentlyContinue)) { return $true }
        Start-Sleep -Milliseconds 500
    }
    return (-not (Get-Process -Id $id -ErrorAction SilentlyContinue))
}
try {
    if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) {
        Record 'installed_exe' 'FAIL' 'InOneLine.exe is missing beside this script'
        throw 'EXE is missing'
    }
    Record 'installed_exe' 'PASS' 'Installed executable found'

    $other = @(Get-Process -Name 'InOneLine' -ErrorAction SilentlyContinue)
    if ($other.Count -gt 0) {
        Record 'existing_instance_guard' 'FAIL' 'Close other InOneLine instances before this test'
        throw 'Existing InOneLine process detected'
    }
    Record 'existing_instance_guard' 'PASS' 'No existing instance'

    $sandboxPath = Join-Path $reportRoot 'sandbox_results.json'
    $argument = '--autotest-sandbox "' + $sandboxPath + '"'
    $helper = Start-Process -FilePath $exe -ArgumentList $argument -WorkingDirectory $PSScriptRoot -PassThru
    if (-not $helper.WaitForExit(90000)) {
        Stop-Process -Id $helper.Id -Force -ErrorAction SilentlyContinue
        Record 'frozen_sandbox_execution' 'FAIL' 'Sandbox helper timeout (90 seconds)'
    } elseif (-not (Test-Path $sandboxPath)) {
        Record 'frozen_sandbox_execution' 'FAIL' ('No sandbox JSON; helper exit code ' + $helper.ExitCode)
    } else {
        $sandbox = Get-Content -LiteralPath $sandboxPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($sandbox.schema -ne 'inone-autotest-sandbox-v1') { throw 'Unexpected sandbox report schema' }
        foreach ($t in @($sandbox.tests)) {
            $info = if ($t.status -eq 'PASS') { ('completed in ' + $t.duration_ms + ' ms') } else { [string]$t.error_type }
            Record ([string]$t.name) ([string]$t.status) $info
        }
        if ($helper.ExitCode -eq 0 -and $sandbox.summary.fail -eq 0) {
            Record 'frozen_sandbox_execution' 'PASS' 'Isolated tests completed'
        } else {
            Record 'frozen_sandbox_execution' 'FAIL' ('Sandbox failed, exit code ' + $helper.ExitCode)
        }
    }

    $t0 = [DateTime]::UtcNow
    $live = Start-Process -FilePath $exe -WorkingDirectory $PSScriptRoot -PassThru
    Record 'launch_process' 'PASS' ('Started PID ' + $live.Id)
    $deadline = [DateTime]::UtcNow.AddSeconds(35)
    while ([DateTime]::UtcNow -lt $deadline -and -not $base) {
        if ($live.HasExited) { break }
        try {
            # Match the local port to the PID we launched; do not use an
            # arbitrary service already bound to 8765 by someone else.
            $tcp = @(Get-NetTCPConnection -State Listen -OwningProcess $live.Id -ErrorAction Stop)
            foreach ($conn in $tcp) {
                $p = [int]$conn.LocalPort
                if ($p -lt 1) { continue }
                $candidate = 'http://127.0.0.1:' + $p
                if (Probe ($candidate + '/api/health')) {
                    $base = $candidate; $port = $p; break
                }
            }
        } catch { }
        if (-not $base) { Start-Sleep -Milliseconds 700 }
    }
    if ($base) {
        Record 'api_health' 'PASS' ('HTTP ready in ' + [int]([DateTime]::UtcNow-$t0).TotalMilliseconds + ' ms, local port ' + $port)
        foreach ($route in @(
            '/api/data', '/api/public', '/api/multichat',
            '/api/wheel', '/api/auction-lots', '/api/timer',
            '/api/rules', '/api/music-player',
            '/overlay', '/list-overlay', '/wheel-overlay',
            '/auction-lots-overlay', '/rules-overlay',
            '/timer-overlay', '/multichat-overlay'
        )) {
            $ok = Probe ($base+$route)
            Record ('route_'+$route) $(if($ok){'PASS'}else{'FAIL'}) $(if($ok){'HTTP 200'}else{'no HTTP 200'})
        }
    } else {
        Record 'api_health' 'FAIL' 'Could not associate a working health port with launched PID'
        Record 'twitch_message_live' 'SKIP' 'Health endpoint not available'
    }

    if ($base -and -not $SkipTwitch -and -not $NoPrompt) {
        Write-Host ''
        Write-Host 'TWITCH: optional real message test.'
        $choice = Read-Host 'Send a test message from your Twitch chat? (Y/N)'
        if ($choice -match '^[YyДд]') {
            $marker = 'IOLTEST-' + ([Guid]::NewGuid().ToString('N').Substring(0,8))
            Write-Host ('Send this EXACT message to Twitch chat: ' + $marker)
            Read-Host 'Press Enter AFTER sending the message' | Out-Null
            $seen = $false
            $until = [DateTime]::UtcNow.AddSeconds(65)
            while ([DateTime]::UtcNow -lt $until) {
                try {
                    $snap = ApiJson ($base + '/api/multichat')
                    foreach ($msg in @($snap.messages)) {
                        if ($null -ne $msg -and $msg.platform -eq 'twitch' -and $msg.text -eq $marker) {
                            $seen=$true; break
                        }
                    }
                } catch { }
                if ($seen) { break }
                Start-Sleep -Seconds 2
            }
            Record 'twitch_message_live' $(if($seen){'PASS'}else{'FAIL'}) $(if($seen){'Unique Twitch message received'}else{'No matching message via OBS multichat API in 65 seconds'})
        } else {
            Record 'twitch_message_live' 'SKIP' 'Operator declined optional live test'
        }
    } elseif ($base) {
        Record 'twitch_message_live' 'SKIP' 'Optional interactive step disabled'
    }
    Record 'twitch_channel_points_live' 'SKIP' 'Not available on this channel'
    Record 'donationalerts_live_donation' 'SKIP' 'No real test donation event; sandbox tests used'

    if ($live -and -not $live.HasExited) {
        if ($NoPrompt) {
            Record 'normal_window_close' 'SKIP' 'Non-interactive mode; not forcing real app close'
        } else {
            Write-Host ''
            Read-Host 'CLOSE InOneLine using its normal X button, then press Enter' | Out-Null
            if (WaitPidExit $live.Id 20) {
                Record 'normal_window_close' 'PASS' 'Original PID disappeared after GUI close'
                if ($base -and -not (Probe ($base + '/api/health'))) {
                    Record 'http_port_release' 'PASS' 'Local API no longer responds'
                } elseif ($base) {
                    Record 'http_port_release' 'FAIL' 'Local API is still responding'
                }
            } else {
                Record 'normal_window_close' 'FAIL' 'Original process still exists after 20 seconds'
            }
        }
    } else {
        Record 'normal_window_close' 'FAIL' 'Application exited before closing test'
    }
} catch {
    Record 'runner' 'FAIL' ('Runner error: ' + $_.Exception.GetType().Name)
} finally {
    $report = [ordered]@{
        schema = 'inone-operator-autotest-v1'
        script_version = $scriptVersion
        started_utc = $started.ToString('o')
        ended_utc = [DateTime]::UtcNow.ToString('o')
        exe_filename = 'InOneLine.exe'
        live_process_id = $(if($live){$live.Id}else{$null})
        summary = @{
            pass = @($results | Where-Object status -eq 'PASS').Count
            fail = @($results | Where-Object status -eq 'FAIL').Count
            skip = @($results | Where-Object status -eq 'SKIP').Count
        }
        results = @($results.ToArray())
        privacy = 'No Twitch chat message text, credentials, database or tokens are included'
    }
    $jsonFile = Join-Path $reportRoot 'report.json'
    $txtFile = Join-Path $reportRoot 'summary.txt'
    $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $jsonFile -Encoding UTF8
    @(
        ('InOneLine operator diagnostics '+$stamp)
        ('PASS '+$report.summary.pass+'  FAIL '+$report.summary.fail+'  SKIP '+$report.summary.skip)
        ''
        @($results | ForEach-Object { '['+$_.status+'] '+$_.test+' :: '+$_.info })
    ) | Set-Content -LiteralPath $txtFile -Encoding UTF8
    $zipPath = $reportRoot + '.zip'
    try {
        Compress-Archive -Path (Join-Path $reportRoot '*') -DestinationPath $zipPath -Force
        Write-Host ''
        Write-Host ('RESULT: ' + $zipPath)
        Write-Host 'Send this ZIP archive for review. No private chats or database files are included.'
    } catch {
        Write-Host ('Could not zip results; report directory: '+$reportRoot)
    }
    if (-not $NoPrompt) { Read-Host 'Press Enter to close the tester' | Out-Null }
}
