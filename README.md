# Stateful Morningstar ETF Chatbot

This project compares two or three ETFs with Morningstar MCP and Azure OpenAI. It remembers the latest comparison, so later questions can be answered conversationally.

## Simple architecture

```text
understand_request
  ├─ new comparison or add research
  │    → collect_data → create_comparison
  └─ normal follow-up
       → answer_follow_up
```

There is one graph, not multiple agents:

- `understand_request` finds tickers and decides which path to use.
- `collect_data` asks Morningstar for IDs, values, and holdings. Data and holdings run together to reduce waiting time.
- `create_comparison` returns validated table data.
- `answer_follow_up` answers from the saved comparison without calling Morningstar again.

The local `InMemorySaver` keeps each conversation separate by `thread_id`. Reusing an ID preserves context; a new ID starts fresh.

## Files

- `config.py`: reads environment settings.
- `schemas.py`: defines comparison and chat response shapes.
- `morningstar_tools.py`: handles Morningstar calls and response parsing.
- `agent.py`: contains the small conversation graph.
- `main.py`: command-line chatbot.
- `table_renderer.py`: renders comparisons only; natural replies print directly.
- `test_workflow.py`: mocked tests that do not require API access.

## Setup and run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python .\main.py
```

Required `.env` variables:

```dotenv
MORNINGSTAR_MCP_URL=https://mcp.morningstar.com/mcp
MORNINGSTAR_ACCESS_TOKEN=your-token
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=your-deployment
AZURE_OPENAI_API_VERSION=your-supported-api-version
```

Never commit `.env` or print its secrets.

## Run the Streamlit UI

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open `http://localhost:8501`. Comparisons appear as a responsive table with one row per ETF. Holdings and analyst summaries appear in expandable sections. Natural follow-up answers appear as regular chat messages.
## Example

```text
You: Compare VOO and QQQ
Assistant: <comparison table>

You: Which is more concentrated?
Assistant: <short conversational answer>

You: Summarize it in 4 lines
Assistant: <exactly four lines based on the saved comparison>

You: Now add analyst research
Assistant: <updated comparison table with research>
```

## Streamlit use

```python
result = await run_chat_turn(
    message=user_message,
    thread_id=session_id,
    include_research=research_checkbox,
)

if result.response_type == "comparison":
    rows = [row.model_dump() for row in result.comparison.compared_etfs]
else:
    st.write(result.message)
```

Structured comparison data makes tables predictable. Natural follow-ups use `message`, so the UI is not forced to render every answer as a table.

## Checks

```powershell
.\.venv\Scripts\python.exe -m unittest -v test_workflow.py
.\.venv\Scripts\python.exe -m py_compile main.py agent.py config.py morningstar_tools.py schemas.py table_renderer.py test_workflow.py
```