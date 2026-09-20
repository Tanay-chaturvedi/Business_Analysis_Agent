import asyncio

from google.adk.runners import InMemoryRunner
from google.genai import types

from src.agent.coordinator_agent import coordinator_agent


async def main():

    runner = InMemoryRunner(
        agent=coordinator_agent,
        app_name="coordinator_test"
    )

    user_message = """
I want to open a premium Japanese restaurant
in Koramangala, Bengaluru.

Business type: restaurant
Primary cuisine: Japanese
Approx cost for two people: 1800
Online order: Yes
Table booking: Yes
Cuisine count: 3
Restaurant type: Casual Dining
Location: Koramangala, Bengaluru

Please give me a complete business analysis including:
1. Historical location context
2. Expected business performance
3. Competitor analysis
4. Overall business opportunity
"""

    content = types.Content(
        role="user",
        parts=[
            types.Part(text=user_message)
        ]
    )

    session = await runner.session_service.create_session(
        app_name="coordinator_test",
        user_id="test_user"
    )

    async for event in runner.run_async(
        user_id="test_user",
        session_id=session.id,
        new_message=content
    ):

        print("\n--- EVENT ---")
        print("Author:", event.author)
        print("Final:", event.is_final_response())

        if event.content and event.content.parts:

            for part in event.content.parts:

                if part.text:
                    print("\nTEXT:")
                    print(part.text)

                if part.function_call:
                    print("\nFUNCTION CALL:")
                    print(part.function_call)

                if part.function_response:
                    print("\nFUNCTION RESPONSE:")
                    print(part.function_response)


if __name__ == "__main__":
    asyncio.run(main())