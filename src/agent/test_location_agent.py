import asyncio
from dotenv import load_dotenv

load_dotenv()
from google.adk.runners import InMemoryRunner
from google.genai import types

from src.agent.location_agent import location_agent


async def main():

    runner = InMemoryRunner(
        agent=location_agent,
        app_name="location_test"
    )

    user_message = """
Analyze the historical restaurant context of
Koramangala, Bengaluru.
"""

    content = types.Content(
        role="user",
        parts=[
            types.Part(text=user_message)
        ]
    )

    session = await runner.session_service.create_session(
        app_name="location_test",
        user_id="test_user"
    )

    async for event in runner.run_async(
        user_id="test_user",
        session_id=session.id,
        new_message=content
    ):
        if event.is_final_response():
            print("\n===== LOCATION AGENT RESPONSE =====")
            print(event.content.parts[0].text)


if __name__ == "__main__":
    asyncio.run(main())