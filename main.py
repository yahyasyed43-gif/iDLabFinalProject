import asyncio
import traceback
from uuid import uuid4

from agent import initialize_chat_backend, run_chat_turn
from table_renderer import render_comparison


async def main() -> None:
    thread_id = str(uuid4())

    print("Connecting to Morningstar MCP...")
    await initialize_chat_backend()
    print("ETF comparison chatbot is ready.")
    print(f"Conversation thread: {thread_id}")
    print("Example: Compare VOO and QQQ")
    print("Follow-up: Which one is more concentrated?")
    print("Type quit to stop.\n")

    while True:
        question = input("You: ").strip()
        if question.lower() in {"quit", "exit"}:
            break
        if not question:
            continue

        response = await run_chat_turn(question, thread_id)
        print("\nAssistant:\n")
        if response.response_type == "comparison" and response.comparison:
            print(render_comparison(response.comparison))
        else:
            print(response.message)
        print("\n" + "=" * 90 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped.")
    except BaseException as error:
        print(f"\nError: {type(error).__name__}: {error}")
        traceback.print_exception(error)