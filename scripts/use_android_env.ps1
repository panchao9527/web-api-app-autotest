<#
.SYNOPSIS
只为当前 PowerShell 终端启用 Android 工具链，不修改用户级/系统级环境变量。
.EXAMPLE
. .\scripts\use_android_env.ps1
.NOTES
自定义安装目录时传 -SdkRoot 和 -JdkHome；关闭终端即可撤销此次环境切换。
#>
[CmdletBinding()]
param(
    [string]$SdkRoot = "$env:LOCALAPPDATA\Android\Sdk",
    [string]$JdkHome = "$env:LOCALAPPDATA\Programs\Microsoft\OpenJDK\jdk-21.0.12.1+1"
)

if (-not (Test-Path -LiteralPath (Join-Path $JdkHome "bin\java.exe"))) {
    throw "JDK 不存在，请先运行 setup_android_emulator.ps1 或传入正确的 -JdkHome。"
}
if (-not (Test-Path -LiteralPath $SdkRoot -PathType Container)) {
    throw "Android SDK 不存在，请先安装或传入正确的 -SdkRoot。"
}
$env:JAVA_HOME = $JdkHome
$env:ANDROID_HOME = $SdkRoot
$env:ANDROID_SDK_ROOT = $SdkRoot
$androidToolPaths = @(
    (Join-Path $JdkHome "bin"),
    (Join-Path $SdkRoot "platform-tools"),
    (Join-Path $SdkRoot "emulator"),
    (Join-Path $SdkRoot "cmdline-tools\latest\bin")
)
# 重复执行不重复追加；不移除用户原有的其它路径。
$androidExistingPaths = @($env:Path -split ";" | Where-Object { $_ -and $_ -notin $androidToolPaths })
$env:Path = (($androidToolPaths + $androidExistingPaths) -join ";")
Write-Host "已为当前终端启用 Android 工具链，关闭终端后不再生效。"
