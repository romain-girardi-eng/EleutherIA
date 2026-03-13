# LLM Runtime Validation - 2026-03-12T18:42:37Z

## Reasoning Probe

- OK: True
- Provider: openrouter
- Model: openai/gpt-oss-120b:nitro

## Prompt Cache Probe

- OK: False
- Provider: gemini
- Model: gemini-3.1-pro-preview
- Cached content created: None
- Cache entries after first call: None
- Cache entries after second call: None
- Error: HTTPStatusError: Client error '400 Bad Request' for url 'https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-pro-preview:generateContent?key=AIzaSyD3481rvvINY6h56S77ZZCDc_6uwLlFraY'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/400
