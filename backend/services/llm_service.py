# backend/services/llm_service.py

import os
import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
_model = genai.GenerativeModel("gemini-2.5-flash")

PROMPT_TEMPLATE = """Answer the question using ONLY the context below.
If the context does not contain the answer, say "I don't know based on the provided documents."

Context:
{context}

Question: {question}

Answer:"""


def generate_answer(question: str, chunks: list[str]) -> str:
    if not chunks:
        return "I don't know based on the provided documents."

    context = "\n\n---\n\n".join(chunks)
    prompt = PROMPT_TEMPLATE.format(context=context, question=question)

    response = _model.generate_content(prompt)
    return response.text
