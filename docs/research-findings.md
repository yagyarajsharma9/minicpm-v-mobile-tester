# Research Findings & Design Decisions

## MiniCPM-V 4.6 Mobile Deployment

### Context Window Decision
The native context window for MiniCPM-V 4.6 is set to **8192 tokens** in `llama_jni.cpp`. This is a mobile-safe increase from the default 4096, while staying well below the full server-side capability. The context window must accommodate:
- User prompt text
- Chat history tokens
- Image token overhead
- Web search context strings
- Generated answer tokens

**Constraint:** Do not push above 8192 without real device RAM testing.

### Predict Length Fix
`DEFAULT_PREDICT_LENGTH` was raised from 192 to **1024** to fix the "half answer" problem where explanations and math formulas were cut off mid-generation.

### Response Token Range
The configurable response length uses:
- `MIN_RESPONSE_TOKENS = 256`
- `MAX_RESPONSE_TOKENS = 1536`
- Saved in SharedPreferences as `response_max_tokens`

## Web Search Architecture

### Provider Hierarchy
1. **Tavily** — primary search API for structured results
2. **TinyFish Fetch** — fetches clean page content from top Tavily result URLs
3. **Wikipedia** — fallback for factual queries
4. **DuckDuckGo** — HTML parsing fallback

### Search Context Injection
Search results are injected into the model prompt with explicit instructions to use web results for current facts instead of relying on training-time knowledge. Source URLs are included so answers can cite sources.

## Math Formula Rendering

### Problem
Android ICU regex is stricter than desktop JVM regex. Unescaped brackets or braces in math detection patterns caused `PatternSyntaxException` and app crashes immediately on launch.

### Solution
- Escape literal `]`, `{`, `}` in all regex patterns
- KaTeX WebView is created lazily only when an AI message actually contains math
- Normal messages use TextView Markdown rendering — no WebView startup during app launch

### Formula Normalization
`MathFormulaNormalizer.kt` converts common LaTeX commands to readable Android text:
Example: `x_{new} = x_{old} - \alpha \frac{\partial f}{\partial x}` → `x_new = x_old - α (∂ f) / (∂ x)`

## Model Asset Bundling
The APK includes the model GGUF files inside Android assets for offline testing:
- `MiniCPM-V-4_6-Q4_K_M.gguf` — model weights
- `mmproj-model-f16.gguf` — vision projector

This makes the APK very large but enables immediate offline use without downloading models after install.

## Image Processing Optimizations
- Large images are resized before model processing to reduce memory usage and prevent crashes
- Prefill image size optimized for faster mobile processing
- Native image context path guarded against context overflow
- Multiple image selection with preview before send

## Identity Response
Custom identity response for EDAP MINI AI:
> "I am EDAP MINI AI, made by EDAP Technology in March 2026."

## Limitations Discovered
- The bundled APK is very large due to model files (~1.6 GB debug APK)
- Performance depends heavily on device CPU, RAM, and storage speed
- arm64-v8a only — no x86 or armeabi-v7a support
- Image processing is slow on weak phones
- Voice input uses Android system speech-to-text, not native model audio
- Web search requires internet and valid API access
- API keys in APK acceptable for local testing only, not public production