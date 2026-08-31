$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$SupabaseVersion = '2.101.0'
$ScriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$PayloadDirectory = Join-Path $ScriptDirectory 'payload'
if (Test-Path $PayloadDirectory) {
    $SourceDirectory = $PayloadDirectory
} else {
    $SourceDirectory = [System.IO.Path]::GetFullPath((Join-Path $ScriptDirectory '..\..'))
}

function Write-Step([string]$Message) {
    Write-Host "`n$Message" -ForegroundColor Cyan
}

Write-Host 'Cipherboard installer for Windows' -ForegroundColor Green
Write-Host 'This installs the GUI, CLI, local database, Redis cache, and local authentication.'
Write-Host 'Docker Desktop is the only system-level dependency.'
if ($Env:PROCESSOR_ARCHITECTURE -ne 'AMD64') {
    throw "This installer currently supports 64-bit Intel/AMD Windows. Detected: $Env:PROCESSOR_ARCHITECTURE"
}

$defaultLocation = Join-Path $Env:LOCALAPPDATA 'Programs\Cipherboard'
$InstallDirectory = Read-Host "Install location [$defaultLocation]"
if ([string]::IsNullOrWhiteSpace($InstallDirectory)) { $InstallDirectory = $defaultLocation }
$InstallDirectory = [System.IO.Path]::GetFullPath([Environment]::ExpandEnvironmentVariables($InstallDirectory))
$driveRoot = [System.IO.Path]::GetPathRoot($InstallDirectory)
if ($InstallDirectory -eq $driveRoot -or $InstallDirectory -eq $Env:USERPROFILE) {
    throw 'Choose a dedicated Cipherboard folder.'
}

$marker = Join-Path $InstallDirectory '.cipherboard-installation'
if ((Test-Path $InstallDirectory) -and -not (Test-Path $marker)) {
    if (Get-ChildItem -Force $InstallDirectory | Select-Object -First 1) {
        throw "The selected folder is not empty and is not a Cipherboard installation: $InstallDirectory"
    }
}

function Find-Docker {
    $candidates = @(
        (Join-Path $Env:ProgramFiles 'Docker\Docker\resources\bin\docker.exe'),
        (Join-Path $Env:LOCALAPPDATA 'Programs\DockerDesktop\resources\bin\docker.exe')
    )
    $command = Get-Command docker.exe -ErrorAction SilentlyContinue
    if ($command) { $candidates += $command.Source }
    return $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
}

function Find-DockerDesktop {
    return @(
        (Join-Path $Env:ProgramFiles 'Docker\Docker\Docker Desktop.exe'),
        (Join-Path $Env:LOCALAPPDATA 'Programs\DockerDesktop\Docker Desktop.exe')
    ) | Where-Object { Test-Path $_ } | Select-Object -First 1
}

function Install-DockerDesktop {
    $answer = Read-Host 'Docker Desktop is required but was not found. Install it now? [Y/n]'
    if ($answer -match '^[Nn]') { throw 'Docker Desktop is required to install Cipherboard.' }
    $dockerInstaller = Join-Path ([System.IO.Path]::GetTempPath()) 'Docker Desktop Installer.exe'
    Write-Step 'Downloading Docker Desktop from docker.com...'
    Invoke-WebRequest -UseBasicParsing -Uri 'https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe' -OutFile $dockerInstaller
    $signature = Get-AuthenticodeSignature $dockerInstaller
    if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'Docker Inc') {
        Remove-Item -Force $dockerInstaller
        throw 'The downloaded Docker Desktop installer has an invalid or unexpected signature.'
    }
    Write-Step 'Installing Docker Desktop for the current user...'
    $process = Start-Process $dockerInstaller -Wait -PassThru -ArgumentList 'install', '--user'
    Remove-Item -Force $dockerInstaller
    if ($process.ExitCode -ne 0) { throw "Docker Desktop installer exited with code $($process.ExitCode)." }
}

$Docker = Find-Docker
$dockerReady = $false
if ($Docker) {
    & $Docker info *> $null
    $dockerReady = $LASTEXITCODE -eq 0
}
$DockerDesktop = Find-DockerDesktop
if (-not $dockerReady -and -not $DockerDesktop) {
    Install-DockerDesktop
    $Docker = Find-Docker
    $DockerDesktop = Find-DockerDesktop
}
if (-not $Docker -or (-not $dockerReady -and -not $DockerDesktop)) {
    throw 'Docker Desktop was installed but its executable files could not be found.'
}

if (-not $dockerReady) {
    Write-Step 'Starting Docker Desktop. Accept its license and finish any first-run prompts if shown.'
    Start-Process $DockerDesktop
    for ($attempt = 0; $attempt -lt 150; $attempt++) {
        Start-Sleep -Seconds 2
        & $Docker info *> $null
        if ($LASTEXITCODE -eq 0) { break }
    }
}
& $Docker info *> $null
if ($LASTEXITCODE -ne 0) { throw 'Docker Desktop did not become ready. Finish its setup and run this installer again.' }
& $Docker compose version *> $null
if ($LASTEXITCODE -ne 0) { throw 'Docker Compose is unavailable in Docker Desktop.' }

Write-Step "Copying Cipherboard to $InstallDirectory..."
$AppDirectory = Join-Path $InstallDirectory 'app'
@($InstallDirectory, $AppDirectory, (Join-Path $InstallDirectory 'bin'), (Join-Path $InstallDirectory 'tools'), (Join-Path $InstallDirectory 'data')) | ForEach-Object {
    New-Item -ItemType Directory -Force -Path $_ | Out-Null
}
$excludedDirectories = @('.git', '.mypy_cache', '.next', '.pytest_cache', '.ruff_cache', '.venv', 'coverage', 'dist', 'node_modules', 'output', 'playwright-report', 'test-results')
$robocopyArguments = @($SourceDirectory, $AppDirectory, '/MIR', '/R:2', '/W:1', '/NFL', '/NDL', '/NJH', '/NJS', '/NP', '/XD') + $excludedDirectories + @('/XF', '.env', '.env.*')
& robocopy.exe @robocopyArguments
if ($LASTEXITCODE -gt 7) { throw "Unable to copy the application (robocopy exit code $LASTEXITCODE)." }
Set-Content -Encoding UTF8 -Path $marker -Value 'Cipherboard desktop installation'

$toolsDirectory = Join-Path $InstallDirectory 'tools'
$supabaseArchive = "supabase_${SupabaseVersion}_windows_amd64.zip"
$supabaseZip = Join-Path ([System.IO.Path]::GetTempPath()) $supabaseArchive
Write-Step "Installing the pinned Supabase CLI ($SupabaseVersion)..."
Invoke-WebRequest -UseBasicParsing -Uri "https://github.com/supabase/cli/releases/download/v${SupabaseVersion}/${supabaseArchive}" -OutFile $supabaseZip
$expectedChecksum = 'be5ba26e4a2ee1d01e0bbf1d260e638d6d81c45ab374baa3b18bb557f9d08c61'
$actualChecksum = (Get-FileHash -Algorithm SHA256 $supabaseZip).Hash.ToLowerInvariant()
if ($actualChecksum -ne $expectedChecksum) {
    Remove-Item -Force $supabaseZip
    throw 'The Supabase CLI checksum did not match.'
}
$supabaseExtract = Join-Path ([System.IO.Path]::GetTempPath()) "cipherboard-supabase-$PID"
Remove-Item -Recurse -Force $supabaseExtract -ErrorAction SilentlyContinue
Expand-Archive -Path $supabaseZip -DestinationPath $supabaseExtract
Copy-Item -Force (Join-Path $supabaseExtract 'supabase.exe') (Join-Path $toolsDirectory 'supabase.exe')
Remove-Item -Recurse -Force $supabaseExtract
Remove-Item -Force $supabaseZip
$Supabase = Join-Path $toolsDirectory 'supabase.exe'

Write-Step 'Starting local authentication for first-time configuration...'
& $Supabase --workdir $AppDirectory start | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Local authentication failed to start.' }
$statusLines = & $Supabase --workdir $AppDirectory status -o env
if ($LASTEXITCODE -ne 0) { throw 'Unable to read local authentication configuration.' }
$supabaseValues = @{}
foreach ($line in $statusLines) {
    if ($line -match '^([A-Z_]+)=(.*)$') {
        $value = $Matches[2].Trim()
        if ($value.Length -ge 2 -and $value[0] -eq '"' -and $value[$value.Length - 1] -eq '"') {
            $value = $value.Substring(1, $value.Length - 2)
        }
        $supabaseValues[$Matches[1]] = $value
    }
}
$publishableKey = if ($supabaseValues.ContainsKey('PUBLISHABLE_KEY')) { $supabaseValues['PUBLISHABLE_KEY'] } else { $supabaseValues['ANON_KEY'] }
$serviceRoleKey = if ($supabaseValues.ContainsKey('SERVICE_ROLE_KEY')) { $supabaseValues['SERVICE_ROLE_KEY'] } else { $supabaseValues['SECRET_KEY'] }
if ([string]::IsNullOrWhiteSpace($publishableKey) -or [string]::IsNullOrWhiteSpace($serviceRoleKey)) {
    throw 'Supabase did not provide local API keys.'
}

function New-RandomHex([int]$Length) {
    $bytes = New-Object byte[] $Length
    $generator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try { $generator.GetBytes($bytes) } finally { $generator.Dispose() }
    return -join ($bytes | ForEach-Object { $_.ToString('x2') })
}

function New-RandomBase64([int]$Length) {
    $bytes = New-Object byte[] $Length
    $generator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try { $generator.GetBytes($bytes) } finally { $generator.Dispose() }
    return [Convert]::ToBase64String($bytes)
}

$environmentFile = Join-Path $AppDirectory '.installer.env'
if (-not (Test-Path $environmentFile)) {
    $postgresPassword = New-RandomHex 24
    $encryptionKey = New-RandomBase64 32
    $dailyKey = New-RandomHex 32
    $identifierKey = New-RandomHex 32
    $environment = @(
        "POSTGRES_PASSWORD=$postgresPassword",
        "SUPABASE_PUBLISHABLE_KEY=$publishableKey",
        "SUPABASE_SERVICE_ROLE_KEY=$serviceRoleKey",
        "MASTERMIND_SECRET_ENCRYPTION_KEYS={`"v1`":`"$encryptionKey`"}",
        "MASTERMIND_DAILY_HMAC_KEY=$dailyKey",
        "MASTERMIND_PUBLIC_IDENTIFIER_HMAC_KEY=$identifierKey",
        'MASTERMIND_RELEASE=desktop-1.0.0'
    )
    [System.IO.File]::WriteAllLines($environmentFile, $environment, (New-Object System.Text.UTF8Encoding($false)))
}
$currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().User
$fileSecurity = New-Object System.Security.AccessControl.FileSecurity
$fileSecurity.SetOwner($currentUser)
$fileSecurity.SetAccessRuleProtection($true, $false)
$accessRule = [System.Security.AccessControl.FileSystemAccessRule]::new(
    $currentUser,
    [System.Security.AccessControl.FileSystemRights]::FullControl,
    [System.Security.AccessControl.AccessControlType]::Allow
)
$fileSecurity.AddAccessRule($accessRule)
Set-Acl -Path $environmentFile -AclObject $fileSecurity

$ComposeFile = Join-Path $AppDirectory 'installer\docker-compose.yml'
Write-Step 'Building and starting the GUI, API, database, and cache. The first run may take several minutes...'
& $Docker compose --env-file $environmentFile -f $ComposeFile up -d --build
if ($LASTEXITCODE -ne 0) { throw 'Docker Compose could not start Cipherboard.' }

foreach ($endpoint in @('http://127.0.0.1:8000/health/ready', 'http://127.0.0.1:3000/en')) {
    $ready = $false
    for ($attempt = 0; $attempt -lt 90; $attempt++) {
        try {
            Invoke-WebRequest -UseBasicParsing -Uri $endpoint -TimeoutSec 2 | Out-Null
            $ready = $true
            break
        } catch { Start-Sleep -Seconds 2 }
    }
    if (-not $ready) { throw "A required service did not become ready: $endpoint" }
}

$runtimeDirectory = Join-Path $AppDirectory 'installer\runtime\windows'
$binDirectory = Join-Path $InstallDirectory 'bin'
Copy-Item -Force (Join-Path $runtimeDirectory '*') $binDirectory

$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
$pathEntries = @($userPath -split ';' | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
if ($pathEntries -notcontains $binDirectory) {
    [Environment]::SetEnvironmentVariable('Path', (($pathEntries + $binDirectory) -join ';'), 'User')
    $Env:Path = "$Env:Path;$binDirectory"
}

$shell = New-Object -ComObject WScript.Shell
$desktop = [Environment]::GetFolderPath('Desktop')
$shortcut = $shell.CreateShortcut((Join-Path $desktop 'Cipherboard.lnk'))
$shortcut.TargetPath = Join-Path $binDirectory 'cipherboard-gui.cmd'
$shortcut.WorkingDirectory = $InstallDirectory
$shortcut.Description = 'Start and open the Cipherboard GUI'
$shortcut.Save()
$startMenu = Join-Path ([Environment]::GetFolderPath('Programs')) 'Cipherboard'
New-Item -ItemType Directory -Force -Path $startMenu | Out-Null
Copy-Item -Force (Join-Path $desktop 'Cipherboard.lnk') (Join-Path $startMenu 'Cipherboard.lnk')

$guide = Join-Path $InstallDirectory 'INSTALLATION.txt'
$guideContent = @"
Cipherboard installation
========================

Installed in: $InstallDirectory

Installed components:
  - Cipherboard GUI at http://127.0.0.1:3000/en
  - Cipherboard interactive CLI
  - FastAPI game service
  - PostgreSQL game database
  - Redis real-time cache
  - Local Supabase authentication
  - Docker-managed, pinned application dependencies

Open the GUI:
  Use the Cipherboard Desktop/Start Menu shortcut, or run: cipherboard-services open

Use the CLI:
  Open a new Command Prompt or PowerShell window and run: cipherboard
  Direct launcher: $binDirectory\cipherboard.cmd

Manage services:
  cipherboard-services start | stop | restart | status | logs

Data locations:
  CLI scores: $InstallDirectory\data\high_scores.csv
  GUI data: Docker volumes named cipherboard-desktop_*
"@
[System.IO.File]::WriteAllText($guide, $guideContent, (New-Object System.Text.UTF8Encoding($false)))

Write-Host "`nInstallation complete." -ForegroundColor Green
Write-Host 'Installed: GUI, CLI, API, PostgreSQL, Redis, Supabase Auth, and all application dependencies.'
Write-Host "Installation report: $guide"
Write-Host "CLI: $binDirectory\cipherboard.cmd"
Write-Host 'GUI: Desktop and Start Menu shortcuts'
Start-Process notepad.exe $guide
Start-Process 'http://127.0.0.1:3000/en'
