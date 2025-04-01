import openai
from typing import List, Optional, Dict, Any
from models.issue import Message


class OpenAIService:
    def __init__(self, api_key: str):
        openai.api_key = api_key

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI's embedding model"""
        # Remove await as the OpenAI client already returns the response directly
        response = openai.embeddings.create(input=text, model="text-embedding-ada-002")
        return response.data[0].embedding

    async def generate_response(
        self,
        messages: List[Message],
        faq_context: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Generate a response using OpenAI's GPT model"""
        system_message = {
            "role": "system",
            "content": "You are a helpful customer support assistant. Be concise and friendly in your responses.",
        }

        if faq_context:
            faq_text = "\n\n".join(
                [f"Q: {item['question']}\nA: {item['answer']}" for item in faq_context]
            )
            system_message[
                "content"
            ] += f"\n\nHere is some relevant information from our FAQ that might help answer the user's question:\n{faq_text}"

        formatted_messages = [system_message]
        for msg in messages:
            formatted_messages.append(
                {
                    "role": "user" if msg.from_user != "GPT" else "assistant",
                    "content": msg.text,
                }
            )

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=formatted_messages,
            max_tokens=500,
            temperature=0.7,
        )

        return response.choices[0].message.content
