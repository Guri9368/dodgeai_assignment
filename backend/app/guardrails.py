import re

# Topics that are clearly off-domain
OFF_TOPIC_PATTERNS = [
    r'\b(poem|poetry|story|fiction|novel|essay|creative writing)\b',
    r'\b(world cup|olympics|sports|football|soccer|cricket|basketball)\b',
    r'\b(recipe|cooking|food|restaurant)\b',
    r'\b(weather|forecast|temperature|climate)\b',
    r'\b(movie|film|actor|actress|celebrity|entertainment)\b',
    r'\b(politics|president|election|government|war)\b',
    r'\b(joke|funny|humor|laugh)\b',
    r'\b(dating|relationship advice|love|romance)\b',
    r'\b(medical|doctor|health|disease|symptoms)\b',
    r'\b(stock market|crypto|bitcoin|investment advice)\b',
    r'\b(translate|translation|language learning)\b',
    r'\b(code|programming|python|javascript|debug)\b(?!.*\b(order|delivery|invoice|payment|billing|customer|product|material|sales|purchase)\b)',
    r'\b(who (is|was|are)|what (is|was) the|when (did|was))\b(?!.*\b(order|delivery|invoice|payment|billing|customer|product|material|sales|purchase|document|flow|broken|incomplete)\b)',
    r'\b(tell me about yourself|who are you|what can you do)\b',
    r'\b(write|compose|create|generate)\b.*\b(poem|song|story|email|letter|code)\b',
    r'\b(capital of|population of|geography|history of)\b',
    r'\b(math|calculate|equation|integral|derivative)\b(?!.*\b(order|total|sum|count|average|amount)\b)',
]

# Topics that are on-domain
ON_TOPIC_PATTERNS = [
    r'\b(order|orders|sales order|purchase order)\b',
    r'\b(delivery|deliveries|shipped|shipping)\b',
    r'\b(invoice|invoices|billing|billed|bill)\b',
    r'\b(payment|payments|paid|pay)\b',
    r'\b(customer|customers|client)\b',
    r'\b(product|products|material|item|items)\b',
    r'\b(plant|warehouse|address|location)\b',
    r'\b(document|documents|doc|journal|entry)\b',
    r'\b(flow|trace|track|path|connection)\b',
    r'\b(broken|incomplete|missing|pending|status)\b',
    r'\b(highest|lowest|most|least|top|bottom|count|total|sum|average)\b',
    r'\b(which|how many|list|show|find|get|display|what)\b',
    r'\b(vendor|supplier|company)\b',
    r'\b(quantity|amount|price|value|cost)\b',
    r'\b(date|period|month|year|recent|latest)\b',
    r'\b(table|tables|data|dataset|schema|database)\b',
    r'\b(graph|nodes|edges|relationship|connected)\b',
]

REJECTION_MESSAGE = (
    "I'm sorry, but this system is designed to answer questions related to the business dataset only. "
    "I can help you with queries about orders, deliveries, invoices, payments, customers, products, "
    "and their relationships. Please ask a question related to the dataset."
)

def check_guardrails(query: str) -> dict:
    """
    Check if a query is within the domain of the system.
    Returns: {'allowed': bool, 'reason': str}
    """
    query_lower = query.lower().strip()

    # Very short queries - let through (might be entity IDs)
    if len(query_lower) < 3:
        return {'allowed': False, 'reason': 'Query too short. Please provide a more detailed question.'}

    # Check for on-topic patterns first
    on_topic_score = sum(1 for pattern in ON_TOPIC_PATTERNS if re.search(pattern, query_lower))

    # Check for off-topic patterns
    off_topic_score = sum(1 for pattern in OFF_TOPIC_PATTERNS if re.search(pattern, query_lower))

    # If clearly on-topic, allow
    if on_topic_score >= 2:
        return {'allowed': True, 'reason': 'on_topic'}

    # If clearly off-topic and not on-topic, reject
    if off_topic_score >= 1 and on_topic_score == 0:
        return {'allowed': False, 'reason': REJECTION_MESSAGE}

    # If has some on-topic indicators, allow
    if on_topic_score >= 1:
        return {'allowed': True, 'reason': 'partially_on_topic'}

    # Default: allow and let the LLM handle classification
    # This is the secondary guardrail - the LLM will also check
    return {'allowed': True, 'reason': 'uncertain_allowing_llm_check'}


def get_llm_guardrail_prompt() -> str:
    """Returns a system prompt component for LLM-level guardrails."""
    return """
IMPORTANT GUARDRAIL RULES:
1. You ONLY answer questions related to the business dataset containing orders, deliveries, invoices, payments, customers, products, and materials.
2. If the user asks something unrelated (general knowledge, creative writing, personal advice, etc.), respond with:
   "This system is designed to answer questions related to the business dataset only. I can help you with queries about orders, deliveries, invoices, payments, customers, products, and their relationships."
3. Do NOT make up data. Only use information from query results.
4. If the query results are empty, say so honestly.
"""