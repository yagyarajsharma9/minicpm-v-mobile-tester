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

$engineFile = Join-Path $androidProject "app\src\main\java\com\example\minicpm_v_demo\LlamaEngine.kt"
$policyFile = Join-Path $androidProject "app\src\main\java\com\example\minicpm_v_demo\ResponsePromptPolicy.kt"
$nativeFile = Join-Path $androidProject "app\src\main\cpp\llama_jni.cpp"

$engineText = Get-Content -LiteralPath $engineFile -Raw
$policyText = Get-Content -LiteralPath $policyFile -Raw
$nativeText = Get-Content -LiteralPath $nativeFile -Raw

if ($engineText -notmatch "DEFAULT_PREDICT_LENGTH\s*=\s*(\d+)") {
  throw "Could not find DEFAULT_PREDICT_LENGTH in LlamaEngine.kt"
}

$predictLength = [int]$Matches[1]
if ($predictLength -lt 1024) {
  throw "DEFAULT_PREDICT_LENGTH is $predictLength. It should be at least 1024 to reduce half answers."
}

if ($engineText -notmatch "MAX_RESPONSE_TOKENS\s*=\s*(\d+)") {
  throw "Could not find MAX_RESPONSE_TOKENS in LlamaEngine.kt"
}

$maxResponseTokens = [int]$Matches[1]
if ($maxResponseTokens -lt $predictLength) {
  throw "MAX_RESPONSE_TOKENS is lower than DEFAULT_PREDICT_LENGTH."
}

if ($nativeText -notmatch "V46_CONTEXT_SIZE\s*=\s*(\d+)") {
  throw "Could not find V46_CONTEXT_SIZE in llama_jni.cpp"
}

$v46ContextSize = [int]$Matches[1]
if ($v46ContextSize -lt 8192) {
  throw "V46_CONTEXT_SIZE is $v46ContextSize. It should be 8192 for the safer mobile long context build."
}
if ($v46ContextSize -gt 8192) {
  throw "V46_CONTEXT_SIZE is $v46ContextSize. Do not push this mobile APK above 8192 without real device RAM testing."
}

foreach ($required in @("Complete the answer", "full formula", "standard LaTeX", '\[...\]', "final result")) {
  if (-not $policyText.Contains($required)) {
    throw "ResponsePromptPolicy.kt is missing required rule: $required"
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

Write-Host "Response quality self test passed. Predict length: $predictLength. V46 context: $v46ContextSize"
