$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$drive = "M:"
$existing = cmd /c "subst" | Select-String -Pattern "^$([regex]::Escape($drive))\\"
if (-not $existing) {
  cmd /c "subst $drive `"$root`""
}

$shortRoot = "$drive\"
$androidProject = Join-Path $shortRoot "vendor\MiniCPM-V-Apps\MiniCPM-V-demo-Android"

$env:JAVA_HOME = Join-Path $shortRoot "tools\jdk-21"
$env:ANDROID_HOME = Join-Path $shortRoot "tools\android-sdk"
$env:ANDROID_SDK_ROOT = $env:ANDROID_HOME
$env:GRADLE_USER_HOME = Join-Path $shortRoot "tools\gradle-home"
$env:PATH = "$env:JAVA_HOME\bin;$env:ANDROID_HOME\platform-tools;$env:ANDROID_HOME\cmdline-tools\latest\bin;$env:PATH"

Push-Location $androidProject
try {
  .\gradlew.bat assembleDebug --no-daemon
} finally {
  Pop-Location
}
