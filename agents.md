# Agents

## Browser Automation

Use **browser-use** for all browser automation tasks. Do NOT use Playwright.

- **Library:** [`browser-use`](https://github.com/browser-use/browser-use) v0.11.9
- **Install:** `pip install browser-use`
- **LLM:** Claude (already the active session LLM — no extra cost)

### Basic usage

```python
from browser_use import Agent
from langchain_anthropic import ChatAnthropic

agent = Agent(
    task="your task description",
    llm=ChatAnthropic(model="claude-sonnet-4-6"),
)
await agent.run()
```
