# anthropic SDK cheatsheet

## Simple message

```python
from anthropic import Anthropic

client = Anthropic()                      # reads ANTHROPIC_API_KEY
msg = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    system="You are concise.",
    messages=[{"role": "user", "content": "Summarise the file system in 1 sentence."}],
)
print(msg.content[0].text)
```

## Prompt caching (big system prompt)

```python
msg = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    system=[
        {
            "type": "text",
            "text": LONG_SYSTEM_PROMPT,   # bigger than ~1024 tokens
            "cache_control": {"type": "ephemeral"},
        }
    ],
    messages=[{"role": "user", "content": user_input}],
)
```

## Streaming

```python
with client.messages.stream(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Tell me a haiku."}],
) as stream:
    for chunk in stream.text_stream:
        print(chunk, end="", flush=True)
```

## Tool use (round-trip)

```python
tools = [
    {
        "name": "get_weather",
        "description": "Get current weather.",
        "input_schema": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    }
]
msg = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    tools=tools,
    messages=[{"role": "user", "content": "What's the weather in Madison?"}],
)

# If msg.stop_reason == "tool_use", build a tool_result and call again with the assistant
# turn echoed back plus the tool_result block.
```

## Async

```python
from anthropic import AsyncAnthropic

async def go():
    client = AsyncAnthropic()
    msg = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        messages=[{"role": "user", "content": "ping"}],
    )
    return msg.content[0].text
```

## Batch (cost saving for offline workloads)

```python
batch = client.messages.batches.create(requests=[
    {
        "custom_id": "row-1",
        "params": {
            "model": "claude-sonnet-4-6",
            "max_tokens": 256,
            "messages": [{"role": "user", "content": "ping 1"}],
        },
    },
    # ...
])
```
