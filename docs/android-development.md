# Android Development Guide

## Project Structure

The Android project is at `vendor/MiniCPM-V-Apps/MiniCPM-V-demo-Android/`.

### Key Source Files

| File | Purpose |
|---|---|
| `MainActivity.kt` | Main screen and app controller |
| `LlamaEngine.kt` | JNI bridge for model loading and generation |
| `WebSearchClient.kt` | Web search with Tavily, TinyFish, Wikipedia, DuckDuckGo |
| `ModelInfo.kt` | Model list and selection configuration |
| `ResponsePromptPolicy.kt` | Prompt rules for complete answers and formula rendering |
| `ConversationMemoryManager.kt` | Compact chat memory for long conversations |
| `MathFormulaNormalizer.kt` | Converts LaTeX to readable Android text |
| `MathHtmlRenderer.kt` | KaTeX HTML rendering for formulas |
| `llama_jni.cpp` | Native C++ JNI bridge |
| `app/build.gradle.kts` | Gradle build configuration |

### Build Configuration

- minSdk = 24
- targetSdk = 36
- abiFilters = arm64-v8a
- Bundled model files in `app/src/main/assets/bundled_models/minicpm-v-4_6-instruct/`

## Build Steps

From the repository root:

```powershell
.\build_android.ps1
```

This script:
1. Creates the `M:` drive via `subst M: "<project root>"`
2. Sets `JAVA_HOME`, `ANDROID_HOME`, `ANDROID_SDK_ROOT`, `GRADLE_USER_HOME`
3. Updates `PATH` with Java and Android SDK binaries
4. Runs `.\gradlew.bat assembleDebug --no-daemon`

Output APK: `dist/EDAP-MINI-AI-final-debug.apk`

## Running Unit Tests

From the Android project directory:

```powershell
.\gradlew.bat testDebugUnitTest --no-daemon
```

From the repository root using the self-test scripts:

```powershell
.\test_response_quality.ps1
.\test_memory_compaction.ps1
```

## Self-Test Coverage

`test_response_quality.ps1` verifies:
- V46 context size is exactly 8192
- DEFAULT_PREDICT_LENGTH >= 1024
- MAX_RESPONSE_TOKENS >= DEFAULT_PREDICT_LENGTH
- ResponsePromptPolicy contains required rules

`test_memory_compaction.ps1` verifies:
- ConversationMemoryManager.kt contains required implementation markers
- MainActivity.kt wires memory manager correctly

## API Keys

API keys are stored in `local.properties` (gitignored):
- `TAVILY_API_KEY`
- `TINYFISH_API_KEY`

Read in Gradle build and exposed via `BuildConfig`.

**Do not hardcode API keys in source files.**