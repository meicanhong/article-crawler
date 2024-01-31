import json

from factory import openai_client


def chat_response_dict(content: str, role: str = "user") -> dict:
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=[
            {"role": role, "content": content},
        ],
        response_format={"type": "json_object"},
        seed=42,
        temperature=0,
    )
    result: str = response.choices[0].message.content
    return json.loads(result)


def chat_response_str(content: str, role: str = "user") -> str:
    result = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": role, "content": content},
        ]
    )
    return result.choices[0].message.content
