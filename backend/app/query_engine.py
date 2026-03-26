import json
from .database import get_schema_description, execute_query
from .llm_service import llm_service
from .guardrails import check_guardrails, REJECTION_MESSAGE
from .graph_builder import graph_builder


class QueryEngine:
    def __init__(self):
        self.conversation_history = []
        self._schema_cache = None

    def get_schema(self):
        if self._schema_cache is None:
            self._schema_cache = get_schema_description()
        return self._schema_cache

    def invalidate_schema_cache(self):
        self._schema_cache = None

    async def process_query(self, user_query: str) -> dict:
        """Process a natural language query end-to-end."""

        # Step 1: Guardrail check (fast, rule-based)
        guardrail_result = check_guardrails(user_query)
        if not guardrail_result['allowed']:
            return {
                'answer': guardrail_result['reason'],
                'sql_query': None,
                'results': [],
                'query_type': 'rejected',
                'highlighted_nodes': []
            }

        # Step 2: Classify query with LLM
        try:
            query_type = await llm_service.classify_query(user_query)
        except Exception as e:
            query_type = "DATA_QUERY"
            print(f"Classification error: {e}")

        # Step 3: Check if LLM classified as off-topic
        if "OFF_TOPIC" in query_type:
            return {
                'answer': REJECTION_MESSAGE,
                'sql_query': None,
                'results': [],
                'query_type': 'rejected',
                'highlighted_nodes': []
            }

        # Step 4: Get schema
        schema = self.get_schema()

        # Step 5: Build conversation context
        history_str = ""
        if self.conversation_history:
            recent = self.conversation_history[-3:]  # Last 3 exchanges
            history_parts = []
            for h in recent:
                history_parts.append(f"User: {h['query']}")
                if h.get('sql'):
                    history_parts.append(f"SQL: {h['sql']}")
            history_str = "\n".join(history_parts)

        # Step 6: Generate SQL
        try:
            sql_query = await llm_service.generate_sql(schema, user_query, history_str)
            print(f"Generated SQL: {sql_query}")
        except Exception as e:
            return {
                'answer': f"I encountered an error generating the query: {str(e)}. Please try rephrasing your question.",
                'sql_query': None,
                'results': [],
                'query_type': query_type,
                'highlighted_nodes': []
            }

        # Step 7: Check for CANNOT_ANSWER
        if 'CANNOT_ANSWER' in sql_query.upper():
            return {
                'answer': "I couldn't find a way to answer this question with the available data. Please try a different question about orders, deliveries, invoices, payments, customers, or products.",
                'sql_query': sql_query,
                'results': [],
                'query_type': query_type,
                'highlighted_nodes': []
            }

        # Step 8: Execute query
        query_result = execute_query(sql_query)

        if 'error' in query_result and query_result['error']:
            # Try to regenerate with error context
            print(f"SQL Error: {query_result['error']}, attempting retry...")
            try:
                retry_prompt = f"The previous SQL query failed with error: {query_result['error']}. Original question: {user_query}. Please generate a corrected SQL query."
                sql_query = await llm_service.generate_sql(schema, retry_prompt, "")
                print(f"Retry SQL: {sql_query}")
                query_result = execute_query(sql_query)
            except:
                pass

            if 'error' in query_result and query_result['error']:
                return {
                    'answer': f"I had trouble executing the query. Error: {query_result['error']}. Please try rephrasing your question.",
                    'sql_query': sql_query,
                    'results': [],
                    'query_type': query_type,
                    'highlighted_nodes': []
                }

        results = query_result.get('results', [])

        # Step 9: Generate natural language response
        try:
            answer = await llm_service.generate_response(user_query, sql_query, results, schema)
        except Exception as e:
            # Fallback: just format results
            if results:
                answer = f"Found {len(results)} results. Here's a summary:\n"
                for i, row in enumerate(results[:10]):
                    answer += f"{i+1}. {json.dumps(row, default=str)}\n"
            else:
                answer = "No results found for your query."

        # Step 10: Extract highlighted nodes
        highlighted_nodes = self._extract_node_references(results)

        # Step 11: Save to conversation history
        self.conversation_history.append({
            'query': user_query,
            'sql': sql_query,
            'result_count': len(results)
        })

        return {
            'answer': answer,
            'sql_query': sql_query,
            'results': results[:50],  # Limit results sent to frontend
            'query_type': query_type,
            'highlighted_nodes': highlighted_nodes
        }

    def _extract_node_references(self, results: list) -> list:
        """Extract node IDs from query results for graph highlighting."""
        node_ids = []
        id_columns = ['order_id', 'delivery_id', 'invoice_id', 'payment_id',
                       'customer_id', 'product_id', 'material_id', 'billing_doc',
                       'sales_order', 'purchase_order', 'document_number', 'id',
                       'Sales_Order', 'Delivery', 'Billing_Doc', 'Journal_Entry']

        for row in results[:20]:
            for col in id_columns:
                if col in row and row[col] is not None:
                    node_ids.append(str(row[col]))

        return list(set(node_ids))


# Singleton
query_engine = QueryEngine()