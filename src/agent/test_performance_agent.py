import asyncio

from dotenv import load_dotenv

load_dotenv()

from google.adk.runners import InMemoryRunner
from google.genai import types

from src.agent.performance_agent import performance_agent


async def main():

    runner = InMemoryRunner(
        agent=performance_agent,
        app_name="performance_test"
    )

    user_message = """
Predict the historical performance of a restaurant
with the following information:

Location: Koramangala, Bengaluru
Business Type: Japanese Restaurant
Primary Cuisine: Japanese
Cuisine Count: 3
Approximate Cost for Two: 1800
Cost Band: High
Online Order: 1
Table Booking: 1
Restaurant Type: Casual Dining

Historical Location Features:
Historical Restaurant Count: 23
Location Median Cost: 350
Location Online Order Rate: 0.8261
Location Table Booking Rate: 0.0
Location Cuisine Diversity: 5
Location Business Type Diversity: 1
"""

    content = types.Content(
        role="user",
        parts=[
            types.Part(text=user_message)
        ]
    )

    session = await runner.session_service.create_session(
        app_name="performance_test",
        user_id="test_user"
    )

    async for event in runner.run_async(
        user_id="test_user",
        session_id=session.id,
        new_message=content
    ):
        if event.is_final_response() and event.content:
            print("\n===== PERFORMANCE AGENT RESPONSE =====")
            print(event.content.parts[0].text)


if __name__ == "__main__":
    asyncio.run(main())