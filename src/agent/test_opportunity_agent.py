import asyncio

from dotenv import load_dotenv

load_dotenv()

from google.adk.runners import InMemoryRunner
from google.genai import types

from src.agent.opportunity_agent import opportunity_agent


async def main():

    runner = InMemoryRunner(
        agent=opportunity_agent,
        app_name="opportunity_test"
    )

    user_message = """
Calculate the business opportunity assessment using these exact inputs.

probabilities:
[0.5151, 0.0567, 0.4283]

model_classes:
["High", "Low", "Medium"]

competition_summary:
{
    "competitor_count_retrieved": 16,
    "avg_competitor_rating": 4.15,
    "median_competitor_rating": 4.3,
    "avg_competitor_reviews": 5140.75,
    "median_competitor_reviews": 3104.5,
    "high_rating_competitors": 8,
    "high_review_competitors": 11
}
"""

    content = types.Content(
        role="user",
        parts=[
            types.Part(text=user_message)
        ]
    )

    session = await runner.session_service.create_session(
        app_name="opportunity_test",
        user_id="test_user"
    )

    async for event in runner.run_async(
        user_id="test_user",
        session_id=session.id,
        new_message=content
    ):
        if event.is_final_response() and event.content:
            print("\n===== OPPORTUNITY AGENT RESPONSE =====")
            print(event.content.parts[0].text)


if __name__ == "__main__":
    asyncio.run(main())
