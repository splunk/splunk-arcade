import json
import os
from random import uniform
from typing import Any

import openai
import yaml

from src.cache import get_redis_conn

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


class _OpenAiClient:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self):
        try:
            self.client = openai.OpenAI(api_key=OPENAI_API_KEY)
        except Exception as e:
            print(f"failed to setup openai client, exc: {e}")
            self.client = None


def _generate_similar_choices(value: Any) -> Any:
    similar_values = [value * uniform(0.1, 10) for _ in range(3)]

    if isinstance(value, int):
        similar_values = [round(v) for v in similar_values]
    elif isinstance(value, float):
        decimal_places = len(str(value).split(".")[1])
        similar_values = [round(v, decimal_places) for v in similar_values]

        similar_values = [v if v != value else v + (10**-decimal_places) for v in similar_values]

    return similar_values


def _handle_splunk_webhook_content(app, payload: dict[str, Any]) -> None:
    payload_question_content = payload.get("messageBody", "")

    if not payload_question_content:
        print("failed to get question content...")
        return

    game_title = payload.get("dimensions", {}).get("title")
    if not game_title:
        print("failed to get game title...")
        return

    question_title = payload.get("detector")
    if not question_title:
        print("failed to get question title...")
        return

    player_name = payload.get("dimensions", {}).get("player_name")
    if not player_name:
        print(
            "failed to get player name for question...",
        )
        return

    question_data = yaml.safe_load(payload_question_content)

    question = {
        "question": question_data["question"],
        "link": "",
        "link_text": "",
        "choices": [
            {
                "prompt": question_data["answer"],
                "is_correct": True,
            }
        ],
    }

    question["choices"].extend(
        [
            {
                "prompt": similar_value,
                "is_correct": False,
            }
            for similar_value in _generate_similar_choices(question_data["answer"])
        ]
    )

    question["choices"] = json.dumps(question["choices"])

    with app.app_context():
        redis = get_redis_conn()

        key = f"content:quiz:{game_title}:{player_name}:{question_title}"
        redis.hmset(key, question)
        redis.expire(key, 360)


def _handle_splunk_webhook_content_openai(app, payload: dict[str, Any]) -> None:
    client = _OpenAiClient()

    if client.client is None:
        # we dont have an openapi client, nothing to do
        return

    game_title = payload.get("dimensions", {}).get("title")
    if not game_title:
        print("failed to get game title... OPENAI")
        return

    description = payload.get("description", "No description provided.")
    detector_name = payload.get("detector", "Unknown Detector")
    severity = payload.get("severity", "Unknown Severity")
    metric_name = payload.get("originatingMetric", "Unknown Metric")
    status = payload.get("status", "Unknown Status")
    dimensions = payload.get("dimensions", {})

    player_name = dimensions.get("player_name", "Unknown Player")

    score = dimensions.get("score", "N/A")
    condition = payload.get("detectOnCondition", "No condition provided.")

    prompt = f"""
    A critical alert was triggered in the Splunk Observability system with the following details:
    
    - **Detector Name:** {detector_name}
    - **Description:** {description}
    - **Severity:** {severity}
    - **Status:** {status}
    - **Metric Name:** {metric_name}
    - **Condition:** {condition}
    - **Player:** {player_name} with score {score}

    Generate  QTY 100 **multiple-choice quiz questions** related to observability and troubleshooting based on this alert. Can you print the player name value in the question body..   
    Provide the output in JSON format occasionally can you use the player_name dimension and provide links back to the originating chart with player name in the filter. Dont always include player Name in there.  If the Alert comes from APM Ask Questions about APM And traces:
    {{
        "question": "Generated quiz question?",
        "choices": ["Option A", "Option B", "Option C", "Option D"],
        "correct_answer": "Correct option",
        "Click Link to Investigate in Splunk Observability", "https://app.us1.signalfx.com/#/dashboard/GZnl1qiA0AA?groupId=GZnlvm8AwAA&configId=GZnmm_8A4AI&sources%5B%5D=player_name:{player_name}",
        "content": "generate a 3 paragraph related learning text related to the Associated Splunk Observability topic"
    }}
    """

    # Make request to OpenAI API (new format)
    response = client.client.chat.completions.create(
        model="chatgpt-4o-latest", messages=[{"role": "user", "content": prompt}]
    )

    print(response.choices[0].message.content)
