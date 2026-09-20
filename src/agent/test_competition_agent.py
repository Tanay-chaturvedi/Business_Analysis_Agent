import asyncio

from google.adk.runners import InMemoryRunner
from google.genai import types

from src.agent.competition_agent import competition_agent


async def main():

    runner = InMemoryRunner(
        agent=competition_agent,
        app_name="competition_test"
    )

    user_message = """
Call competition_analysis_tool directly.

Use exactly these arguments:
latitude = 12.935240300000002
longitude = 77.624532
search_query = "restaurants in Koramangala, Bengaluru"
business_type = "restaurant"

Do not ask questions.
Do not modify these values.
"""

    content = types.Content(
        role="user",
        parts=[
            types.Part(text=user_message)
        ]
    )

    session = await runner.session_service.create_session(
        app_name="competition_test",
        user_id="test_user"
    )

    async for event in runner.run_async(
        user_id="test_user",
        session_id=session.id,
        new_message=content
    ):
        if event.is_final_response():

            print("\n===== COMPETITION AGENT RESPONSE =====")

            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        print(part.text)
            else:
                print("Final event contains no text.")


if __name__ == "__main__":
    asyncio.run(main())