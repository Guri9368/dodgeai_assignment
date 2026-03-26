import httpx
import json
import re
import asyncio
from .config import settings
from .prompt_templates import (
    get_sql_generation_prompt,
    get_response_generation_prompt,
    get_classification_prompt,
)
from .guardrails import get_llm_guardrail_prompt


class LLMService:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.timeout = 30.0

    async def _call_groq(self, messages, temperature=0.1, max_tokens=2000):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(url, json=payload, headers=headers)
                    if resp.status_code == 429:
                        wait = 2 ** attempt + 1
                        print(f"Rate limited, waiting {wait}s...")
                        await asyncio.sleep(wait)
                        continue
                    resp.raise_for_status()
                    return resp.json()["choices"][0]["message"]["content"].strip()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429 and attempt < 2:
                    await asyncio.sleep(2 ** attempt + 1)
                    continue
                raise
        raise Exception("Rate limit exceeded after retries")

    async def _call_gemini(self, messages, temperature=0.1, max_tokens=2000):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={settings.GEMINI_API_KEY}"
        contents = []
        system_text = ""
        for msg in messages:
            if msg["role"] == "system":
                system_text = msg["content"]
            elif msg["role"] == "user":
                contents.append({"role": "user", "parts": [{"text": msg["content"]}]})
            elif msg["role"] == "assistant":
                contents.append({"role": "model", "parts": [{"text": msg["content"]}]})
        if system_text and contents:
            contents[0]["parts"][0]["text"] = system_text + "\n\n" + contents[0]["parts"][0]["text"]
        payload = {"contents": contents, "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens}}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

    async def _call_openrouter(self, messages, temperature=0.1, max_tokens=2000):
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {"Authorization": f"Bearer {settings.OPENROUTER_API_KEY}", "Content-Type": "application/json"}
        payload = {"model": "meta-llama/llama-3.3-70b-instruct:free", "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()

    async def call_llm(self, messages, temperature=0.1, max_tokens=2000):
        try:
            if self.provider == "groq":
                return await self._call_groq(messages, temperature, max_tokens)
            elif self.provider == "gemini":
                return await self._call_gemini(messages, temperature, max_tokens)
            elif self.provider == "openrouter":
                return await self._call_openrouter(messages, temperature, max_tokens)
            else:
                raise ValueError(f"Unknown provider: {self.provider}")
        except Exception as e:
            print(f"LLM error: {e}")
            raise

    async def classify_query(self, user_query):
        messages = [
            {"role": "system", "content": "Respond with ONLY the category."},
            {"role": "user", "content": get_classification_prompt(user_query)},
        ]
        result = await self.call_llm(messages, temperature=0.0, max_tokens=20)
        return result.strip().upper()

    async def generate_sql(self, schema, user_query, conversation_history=""):
        prompt = get_sql_generation_prompt(schema, user_query, conversation_history)
        messages = [
            {"role": "system", "content": "Return ONLY the SQL query. No markdown. No explanation."},
            {"role": "user", "content": prompt},
        ]
        result = await self.call_llm(messages, temperature=0.0, max_tokens=1000)
        result = re.sub(r'^```sql\s*', '', result.strip())
        result = re.sub(r'^```\s*', '', result)
        result = re.sub(r'\s*```$', '', result)
        return result.strip()

    async def generate_response(self, user_query, sql_query, query_results, schema_context=""):
        results_str = json.dumps(query_results[:20], indent=2, default=str)
        if len(query_results) > 20:
            results_str += f"\n... and {len(query_results) - 20} more"
        prompt = get_response_generation_prompt(user_query, sql_query, results_str, schema_context)
        guardrail = get_llm_guardrail_prompt()
        messages = [
            {"role": "system", "content": f"You are a business data analyst.{guardrail}"},
            {"role": "user", "content": prompt},
        ]
        return await self.call_llm(messages, temperature=0.3, max_tokens=1500)


llm_service = LLMService()