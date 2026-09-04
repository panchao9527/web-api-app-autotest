<#
.SYNOPSIS
为 Windows 安装本框架所需的 Android 14 模拟器与 Appium 3。

.DESCRIPTION
脚本只写入当前用户目录，不删除已有 SDK、JDK 或 AVD。重复执行时会复用
已经校验过的组件，适合新电脑首次初始化和环境修复。
#>

[CmdletBinding()]
param(
    [string]$AvdName = "Pixel_6_API_34",
    [string]$SdkRoot = "$env:LOCALAPPDATA\Android\Sdk"
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$JdkVersion = "21.0.12.1"
$JdkFolder = "jdk-21.0.12.1+1"
$JdkUrl = "https://aka.ms/download-jdk/microsoft-jdk-21-windows-x64.zip"
$JdkSha256 = "192441a9d27da813bada974bb88b4cf64d37a9589ed37f204374d411ca5ce07f"
$CommandToolsUrl = "https://dl.google.com/android/repository/commandlinetools-win-15859902_latest.zip"
$CommandToolsSha256 = "90ae805d20434428bffcb699c290860f19bb5f66a67e6b330067e3de801fb04a"
$AppiumVersion = "3.4.2"
$UiAutomator2Version = "8.5.2"
$AppiumLoggerVersion = "2.0.7"
$SystemImage = "system-images;android-34;google_apis;x86_64"
$DemoAppVersion = "6.0.17"
$DemoAppUrl = "https://github.com/appium/android-apidemos/releases/download/v$DemoAppVersion/ApiDemos-debug.apk"
$DemoAppSha256 = "90cc1041c063a7fb68889143250fefa3139ef0c81e4208f67dbaafe8f15c8be9"
$DownloadDir = Join-Path $env:TEMP "web-api-app-autotest-android"
$JdkParent = Join-Path $env:LOCALAPPDATA "Programs\Microsoft\OpenJDK"
$JdkHome = Join-Path $JdkParent $JdkFolder
$DemoAppDir = Join-Path $env:LOCALAPPDATA "Android\TestApps"
$DemoAppPath = Join-Path $DemoAppDir "ApiDemos-debug-v$DemoAppVersion.apk"
$ProjectRoot = Split-Path $PSScriptRoot -Parent

function Write-Step([string]$Message) {
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Get-VerifiedDownload {
    param(
        [Parameter(Mandatory)] [string]$Url,
        [Parameter(Mandatory)] [string]$Destination,
        [Parameter(Mandatory)] [string]$Sha256
    )

    if (-not (Test-Path -LiteralPath $Destination)) {
        curl.exe -L --fail --retry 3 --output $Destination $Url
    }
    $actual = (Get-FileHash -LiteralPath $Destination -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $Sha256) {
        throw "下载文件校验失败: $Destination`n期望: $Sha256`n实际: $actual"
    }
    Write-Host "SHA-256 校验通过: $Destination"
}

function Add-UserPath {
    param([Parameter(Mandatory)] [string[]]$Paths)

    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $existing = @($userPath -split ";" | Where-Object { $_ })
    foreach ($path in $Paths) {
        if ($existing -notcontains $path) {
            $existing = @($path) + $existing
        }
    }
    [Environment]::SetEnvironmentVariable("Path", ($existing -join ";"), "User")
}

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    throw "未找到 Node.js。请先从 https://nodejs.org 安装 Node.js LTS，再重新运行本脚本。"
}
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "未找到 npm，请修复 Node.js 安装后重试。"
}
if (-not (Get-Command curl.exe -ErrorAction SilentlyContinue)) {
    throw "未找到 Windows curl.exe，无法下载官方安装包。"
}

New-Item -ItemType Directory -Path $DownloadDir -Force | Out-Null

Write-Step "安装 Microsoft OpenJDK $JdkVersion"
if (-not (Test-Path -LiteralPath (Join-Path $JdkHome "bin\java.exe"))) {
    $jdkArchive = Join-Path $DownloadDir "microsoft-jdk-$JdkVersion-windows-x64.zip"
    Get-VerifiedDownload -Url $JdkUrl -Destination $jdkArchive -Sha256 $JdkSha256
    New-Item -ItemType Directory -Path $JdkParent -Force | Out-Null
    Expand-Archive -LiteralPath $jdkArchive -DestinationPath $JdkParent -Force
}
[Environment]::SetEnvironmentVariable("JAVA_HOME", $JdkHome, "User")
$env:JAVA_HOME = $JdkHome

Write-Step "安装 Android SDK 命令行工具"
$commandToolsBin = Join-Path $SdkRoot "cmdline-tools\latest\bin"
if (-not (Test-Path -LiteralPath (Join-Path $commandToolsBin "sdkmanager.bat"))) {
    $toolsArchive = Join-Path $DownloadDir "commandlinetools-win-15859902_latest.zip"
    $toolsExpanded = Join-Path $DownloadDir "commandlinetools-expanded"
    Get-VerifiedDownload -Url $CommandToolsUrl -Destination $toolsArchive -Sha256 $CommandToolsSha256
    New-Item -ItemType Directory -Path $toolsExpanded -Force | Out-Null
    Expand-Archive -LiteralPath $toolsArchive -DestinationPath $toolsExpanded -Force
    New-Item -ItemType Directory -Path $commandToolsBin -Force | Out-Null
    Copy-Item -Path (Join-Path $toolsExpanded "cmdline-tools\*") -Destination (Split-Path $commandToolsBin) -Recurse -Force
}

[Environment]::SetEnvironmentVariable("ANDROID_HOME", $SdkRoot, "User")
[Environment]::SetEnvironmentVariable("ANDROID_SDK_ROOT", $SdkRoot, "User")
$env:ANDROID_HOME = $SdkRoot
$env:ANDROID_SDK_ROOT = $SdkRoot
$toolPaths = @(
    (Join-Path $JdkHome "bin"),
    (Join-Path $SdkRoot "platform-tools"),
    (Join-Path $SdkRoot "emulator"),
    $commandToolsBin
)
Add-UserPath -Paths $toolPaths
$env:Path = (($toolPaths + @($env:Path)) -join ";")

$sdkManager = Join-Path $commandToolsBin "sdkmanager.bat"
$avdManager = Join-Path $commandToolsBin "avdmanager.bat"

Write-Step "接受 Android SDK 许可证并安装 API 34 组件"
(1..100 | ForEach-Object { "y" }) | & $sdkManager --licenses | Out-Null
& $sdkManager "platform-tools" "emulator" "platforms;android-34" "build-tools;34.0.0" $SystemImage

Write-Step "创建 Android 14 模拟器 $AvdName"
$installedAvds = @(& (Join-Path $SdkRoot "emulator\emulator.exe") -list-avds)
if ($installedAvds -notcontains $AvdName) {
    "no" | & $avdManager create avd --name $AvdName --package $SystemImage --device "pixel_6"
}
& (Join-Path $SdkRoot "emulator\emulator.exe") -accel-check

Write-Step "安装 Appium $AppiumVersion 与 UiAutomator2 $UiAutomator2Version"
$appiumCommand = Get-Command appium -ErrorAction SilentlyContinue
if (-not $appiumCommand) {
    npm install -g "appium@$AppiumVersion"
} else {
    $installedAppiumVersion = (& appium --version | Out-String).Trim()
    if ($installedAppiumVersion -ne $AppiumVersion) {
        throw "已安装 Appium $installedAppiumVersion，本脚本不会自动覆盖。请先确认团队版本策略。"
    }
}
$driverList = (& appium driver list --installed 2>&1 | Out-String)
if ($driverList -notmatch "uiautomator2") {
    & appium driver install "uiautomator2@$UiAutomator2Version"
} elseif ($driverList -notmatch "uiautomator2@$([regex]::Escape($UiAutomator2Version))") {
    throw "已安装其他版本的 UiAutomator2，本脚本不会自动覆盖。请先确认团队版本策略。"
}

# npm 在部分 Windows 环境会错误提升 io.appium.settings 的 ESM 依赖。
$doctorOutput = (& appium driver doctor uiautomator2 2>&1 | Out-String)
if ($doctorOutput -match "Cannot find package '@appium/logger'") {
    npm install --prefix (Join-Path $env:USERPROFILE ".appium") --save-dev "@appium/logger@$AppiumLoggerVersion"
}

Write-Step "下载官方 ApiDemos 示例安装包"
New-Item -ItemType Directory -Path $DemoAppDir -Force | Out-Null
Get-VerifiedDownload -Url $DemoAppUrl -Destination $DemoAppPath -Sha256 $DemoAppSha256

$envFile = Join-Path $ProjectRoot ".env"
if (-not (Test-Path -LiteralPath $envFile)) {
    @(
        "# 本机 Appium 验证配置；该文件已被 .gitignore 排除。",
        "ENV=uat",
        "APP_PATH=$DemoAppPath",
        "APPIUM_AVD=$AvdName",
        "APPIUM_PLATFORM_VERSION=14",
        "APPIUM_SERVER=http://127.0.0.1:4723",
        "APPIUM_MANAGE_SERVER=true",
        "ANDROID_HOME=$SdkRoot",
        "JAVA_HOME=$JdkHome"
    ) | Set-Content -LiteralPath $envFile -Encoding utf8
    Write-Host "已创建本地 .env；接入公司 App 时把 APP_PATH 改成真实 APK。"
} else {
    Write-Host ".env 已存在，未覆盖。请确认 APP_PATH、APPIUM_AVD、ANDROID_HOME 和 JAVA_HOME。"
}

Write-Step "安装完成"
Write-Host "JAVA_HOME=$JdkHome"
Write-Host "ANDROID_HOME=$SdkRoot"
Write-Host "AVD=$AvdName"
Write-Host "请关闭并重新打开终端，然后运行："
Write-Host "  java -version"
Write-Host "  adb version"
Write-Host "  emulator -list-avds"
Write-Host "  appium --version"
Write-Host "  appium driver list --installed"
Write-Host "  python scripts/automation.py doctor --env uat --type app"
Write-Host "  python scripts/automation.py app-smoke --env uat"
