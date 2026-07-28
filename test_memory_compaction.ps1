$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$drive = "M:"
$existing = cmd /c "subst" | Select-String -Pattern "^$([regex]::Escape($drive))\\"
if (-not $existing) {
  cmd /c "subst $drive `"$root`""
}

$androidProject = "$drive\vendor\MiniCPM-V-Apps\MiniCPM-V-demo-Android"

$env:JAVA_HOME = "$drive\tools\jdk-21"
$env:ANDROID_HOME = "$drive\tools\android-sdk"
$env:ANDROID_SDK_ROOT = $env:ANDROID_HOME
$env:GRADLE_USER_HOME = "$drive\tools\gradle-home"
$env:PATH = "$env:JAVA_HOME\bin;$env:ANDROID_HOME\platform-tools;$env:ANDROID_HOME\cmdline-tools\latest\bin;$env:PATH"

$memoryFile = Join-Path $androidProject "app\src\main\java\com\example\minicpm_v_demo\ConversationMemoryManager.kt"
$mainFile = Join-Path $androidProject "app\src\main\java\com\example\minicpm_v_demo\MainActivity.kt"

$memoryText = Get-Content -LiteralPath $memoryFile -Raw
$mainText = Get-Content -LiteralPath $mainFile -Raw

foreach ($required in @(
  "compact_summary",
  "compacted_message_count",
  "buildSummaryPrompt",
  "buildPromptWithMemory",
  "RECENT_MESSAGE_COUNT",
  "COMPACT_NEW_MESSAGE_COUNT"
)) {
  if (-not $memoryText.Contains($required)) {
    throw "ConversationMemoryManager.kt is missing required implementation marker: $required"
  }
}

foreach ($required in @(
  "maybeCompactConversationMemory",
  "ConversationMemoryManager(applicationContext)",
  "memoryManager.buildPromptWithMemory",
  "memoryManager.clear()",
  "MEMORY_SUMMARY_TOKENS"
)) {
  if (-not $mainText.Contains($required)) {
    throw "MainActivity.kt is missing memory compaction wiring: $required"
  }
}

Push-Location $androidProject
try {
  .\gradlew.bat testDebugUnitTest --no-daemon --no-build-cache --rerun-tasks
  if ($LASTEXITCODE -ne 0) {
    throw "Gradle testDebugUnitTest failed with exit code $LASTEXITCODE"
  }
} finally {
  Pop-Location
}

Write-Host "Memory compaction self test passed."
