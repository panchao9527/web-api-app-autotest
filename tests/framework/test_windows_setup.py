"""Windows 安装辅助脚本的离线验证；不下载、不安装、不修改用户环境变量。"""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows PowerShell 专项检查")


def test_windows_powershell_parses_scripts_and_rejects_native_failure():
    executable = shutil.which("powershell.exe")
    if not executable:
        pytest.skip("未安装 Windows PowerShell")
    root = Path(__file__).resolve().parents[2]
    command = r"""
$ErrorActionPreference = 'Stop'
$errors = $null
$tokens = $null
$setup = [System.Management.Automation.Language.Parser]::ParseFile(
    (Join-Path $pwd 'scripts/setup_android_emulator.ps1'), [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw 'Setup script parse failed' }
[System.Management.Automation.Language.Parser]::ParseFile(
    (Join-Path $pwd 'scripts/use_android_env.ps1'), [ref]$tokens, [ref]$errors) | Out-Null
if ($errors.Count) { throw 'Environment script parse failed' }
# Only load the exit-code checker, never execute the installer body.
$function = $setup.Find({param($node)
    $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
    $node.Name -eq 'Assert-NativeSuccess'
}, $true)
. ([ScriptBlock]::Create($function.Extent.Text))
Assert-NativeSuccess 'success' 0
& $env:ComSpec /d /c exit 7
try {
    Assert-NativeSuccess 'failure' $LASTEXITCODE
    exit 9
} catch {
    if ($_.Exception.Message -notmatch '7') { throw }
    Write-Output 'EXPECTED_FAILURE'
    exit 0
}
"""
    result = subprocess.run(
        [executable, "-NoProfile", "-NonInteractive", "-Command", command],
        cwd=root,
        capture_output=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr.decode(errors="replace")
    assert b"EXPECTED_FAILURE" in result.stdout
