param(
    [ValidateSet('start', 'open', 'stop', 'restart', 'status', 'logs', 'cli', 'help')]
    [string]$Command = 'help'
)

$ErrorActionPreference = 'Stop'
$HomeDirectory = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$AppDirectory = Join-Path $HomeDirectory 'app'
$ComposeFile = Join-Path $AppDirectory 'installer\docker-compose.yml'
$EnvironmentFile = Join-Path $AppDirectory '.installer.env'
$Supabase = Join-Path $HomeDirectory 'tools\supabase.exe'

$dockerCandidates = @(
    (Join-Path $Env:ProgramFiles 'Docker\Docker\resources\bin\docker.exe'),
    (Join-Path $Env:LOCALAPPDATA 'Programs\DockerDesktop\resources\bin\docker.exe'),
    'docker.exe'
)
$Docker = $dockerCandidates | Where-Object {
    if ([System.IO.Path]::IsPathRooted($_)) { Test-Path $_ } else { Get-Command $_ -ErrorAction SilentlyContinue }
} | Select-Object -First 1

function Assert-Docker {
    if (-not $Docker) {
        throw 'Docker Desktop is not installed. Run the Cipherboard installer again.'
    }
    & $Docker info *> $null
    if ($LASTEXITCODE -eq 0) { return }

    Write-Host 'Starting Docker Desktop...'
    $desktopCandidates = @(
        (Join-Path $Env:ProgramFiles 'Docker\Docker\Docker Desktop.exe'),
        (Join-Path $Env:LOCALAPPDATA 'Programs\DockerDesktop\Docker Desktop.exe')
    )
    $desktop = $desktopCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
    if (-not $desktop) { throw 'Docker Desktop could not be started.' }
    Start-Process $desktop
    for ($attempt = 0; $attempt -lt 120; $attempt++) {
        Start-Sleep -Seconds 2
        & $Docker info *> $null
        if ($LASTEXITCODE -eq 0) { return }
    }
    throw 'Docker Desktop did not become ready. Open it, finish setup, and retry.'
}

function Invoke-Compose {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
    & $Docker compose --env-file $EnvironmentFile -f $ComposeFile @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Docker Compose failed with exit code $LASTEXITCODE." }
}

function Wait-ForUrl {
    param([string]$Name, [string]$Url)
    for ($attempt = 0; $attempt -lt 90; $attempt++) {
        try {
            Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 2 | Out-Null
            return
        } catch {
            Start-Sleep -Seconds 2
        }
    }
    throw "$Name did not become ready. Run 'cipherboard-services logs' for details."
}

function Start-Cipherboard {
    Assert-Docker
    Write-Host 'Starting local authentication...'
    & $Supabase --workdir $AppDirectory start | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Local authentication failed to start.' }
    Write-Host 'Starting the database, API, and GUI...'
    Invoke-Compose up -d
    Wait-ForUrl 'Cipherboard API' 'http://127.0.0.1:8000/health/ready'
    Wait-ForUrl 'Cipherboard GUI' 'http://127.0.0.1:3000/en'
    Write-Host 'Cipherboard is ready at http://127.0.0.1:3000/en'
}

switch ($Command) {
    'start' { Start-Cipherboard }
    'open' {
        Start-Cipherboard
        Start-Process 'http://127.0.0.1:3000/en'
    }
    'stop' {
        Assert-Docker
        Invoke-Compose down
        & $Supabase --workdir $AppDirectory stop
        if ($LASTEXITCODE -ne 0) { throw 'Local authentication failed to stop.' }
        Write-Host 'Cipherboard services stopped. Saved games and CLI scores were preserved.'
    }
    'restart' {
        & $PSCommandPath stop
        & $PSCommandPath start
    }
    'status' {
        Assert-Docker
        Invoke-Compose ps
        & $Supabase --workdir $AppDirectory status *> $null
        if ($LASTEXITCODE -eq 0) { Write-Host 'Local authentication: running' }
        else { Write-Host 'Local authentication: stopped' }
    }
    'logs' {
        Assert-Docker
        Invoke-Compose logs --tail=150 -f api web postgres redis
    }
    'cli' {
        Assert-Docker
        Invoke-Compose run --rm --build cli
    }
    'help' {
        Write-Host @'
Cipherboard service manager

  cipherboard-services start    Start every GUI dependency
  cipherboard-services open     Start Cipherboard and open the GUI
  cipherboard-services stop     Stop services without deleting data
  cipherboard-services restart  Restart the complete local stack
  cipherboard-services status   Show service health
  cipherboard-services logs     Follow GUI and API logs
  cipherboard                   Start the interactive command-line game
'@
    }
}
