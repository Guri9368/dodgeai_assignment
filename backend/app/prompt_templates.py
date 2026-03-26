def get_sql_generation_prompt(schema, user_query, conversation_history=""):
    return f"""You are a SQL generator for SQLite. Generate ONLY the SQL query, nothing else.

TABLES:
{schema}

KEY RELATIONSHIPS:
- sales_order_headers.salesOrder = sales_order_items.salesOrder
- sales_order_items.material = products.product
- sales_order_headers.soldToParty = business_partners.businessPartner
- outbound_delivery_items.referenceSDDocument links to salesOrder
- outbound_delivery_headers.deliveryDocument = outbound_delivery_items.deliveryDocument
- billing_document_headers.billingDocument = billing_document_items.billingDocument
- billing_document_items.salesDocument links to salesOrder
- billing_document_headers.soldToParty = business_partners.businessPartner
- billing_document_headers.accountingDocument = journal_entry_items_accounts_receivable.accountingDocument
- business_partners.businessPartner = business_partner_addresses.businessPartner

RULES:
1. Return ONLY valid SQLite SQL. No markdown. No explanation.
2. Use only tables/columns from schema above.
3. LIMIT 50 unless user specifies.
4. For broken flows use LEFT JOIN and check IS NULL.

{f"CONTEXT: {conversation_history}" if conversation_history else ""}

QUESTION: {user_query}

SQL:"""


def get_response_generation_prompt(user_query, sql_query, query_results, schema_context=""):
    return f"""Answer the question based on the data below. Be concise. Use bullet points for lists. Do NOT make up data.

QUESTION: {user_query}
SQL: {sql_query}
RESULTS: {query_results}

If results are empty say "No matching records found."
ANSWER:"""


def get_classification_prompt(user_query):
    return f"""Classify this query into ONE category:
- DATA_QUERY (questions about business data)
- FLOW_TRACE (trace document flow)
- BROKEN_FLOW (incomplete/broken flows)
- SCHEMA_QUERY (about tables/columns)
- OFF_TOPIC (unrelated to business data)

Query: "{user_query}"
Category:"""