import networkx as nx
import json
from .database import get_connection, get_all_tables, get_table_data


class GraphBuilder:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.node_data = {}

    def build_graph(self):
        """Build graph from the SAP O2C database tables."""
        conn = get_connection()
        cursor = conn.cursor()

        tables = get_all_tables()
        print(f"Building graph from {len(tables)} tables: {tables}")

        if not tables:
            print("No tables found in database!")
            return self.graph

        # Get schema info for each table
        table_columns = {}
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table});")
            columns = [row['name'] for row in cursor.fetchall()]
            table_columns[table] = columns

        # Load nodes from each table (limit per table for visualization)
        table_row_ids = {}
        for table in tables:
            rows = get_table_data(table, limit=500)
            table_row_ids[table] = []
            for i, row in enumerate(rows):
                node_id = self._get_node_id(table, row, i)
                table_row_ids[table].append(node_id)

                label = self._get_display_label(table, row, node_id)

                clean_data = {}
                for k, v in row.items():
                    if v is not None:
                        clean_data[k] = str(v)

                self.graph.add_node(
                    node_id,
                    table=table,
                    label=label,
                    **clean_data
                )

        # Build relationships based on SAP O2C domain knowledge
        self._build_sap_relationships(table_columns, conn)

        conn.close()
        print(f"Graph built: {self.graph.number_of_nodes()} nodes, "
              f"{self.graph.number_of_edges()} edges")
        return self.graph

    def _get_node_id(self, table, row, index):
        """Create a meaningful node ID based on table and key columns."""
        key_mappings = {
            'sales_order_headers': 'salesOrder',
            'sales_order_items': ['salesOrder', 'salesOrderItem'],
            'sales_order_schedule_lines': ['salesOrder', 'salesOrderItem'],
            'outbound_delivery_headers': 'deliveryDocument',
            'outbound_delivery_items': ['deliveryDocument', 'deliveryDocumentItem'],
            'billing_document_headers': 'billingDocument',
            'billing_document_items': ['billingDocument', 'billingDocumentItem'],
            'billing_document_cancellations': 'billingDocument',
            'business_partners': 'businessPartner',
            'business_partner_addresses': 'businessPartner',
            'customer_company_assignments': 'customer',
            'customer_sales_area_assignments': 'customer',
            'products': 'product',
            'product_descriptions': 'product',
            'product_plants': ['product', 'plant'],
            'product_storage_locations': 'product',
            'plants': 'plant',
            'payments_accounts_receivable': 'accountingDocument',
            'journal_entry_items_accounts_receivable': 'accountingDocument',
        }

        key_cols = key_mappings.get(table)
        if key_cols:
            if isinstance(key_cols, list):
                parts = []
                for col in key_cols:
                    val = row.get(col, '')
                    if val:
                        parts.append(str(val))
                if parts:
                    return f"{table}_{'_'.join(parts)}"
            else:
                val = row.get(key_cols, '')
                if val:
                    return f"{table}_{val}"

        return f"{table}_{index}"

    def _get_display_label(self, table, row, node_id):
        """Create a human-readable label for a node."""
        label_mappings = {
            'sales_order_headers': 'salesOrder',
            'outbound_delivery_headers': 'deliveryDocument',
            'billing_document_headers': 'billingDocument',
            'business_partners': 'businessPartnerName',
            'products': 'product',
            'plants': 'plantName',
            'payments_accounts_receivable': 'accountingDocument',
        }

        col = label_mappings.get(table)
        if col and col in row and row[col]:
            return str(row[col])[:40]

        for v in row.values():
            if v is not None and str(v).strip():
                return str(v)[:40]

        return node_id.split('_', 1)[-1] if '_' in node_id else node_id

    def _build_sap_relationships(self, table_columns, conn):
        """Build edges based on SAP Order-to-Cash domain knowledge."""
        cursor = conn.cursor()

        # Build lookup index: table -> col -> value -> node_id
        print("  Building node lookup index...")
        node_index = {}

        for node_id, data in self.graph.nodes(data=True):
            table = data.get('table')
            if not table:
                continue
            if table not in node_index:
                node_index[table] = {}
            for col, val in data.items():
                if col in ('table', 'label') or not val:
                    continue
                if col not in node_index[table]:
                    node_index[table][col] = {}
                node_index[table][col][str(val)] = node_id

        relationships = [
            {
                'source': 'sales_order_headers',
                'target': 'sales_order_items',
                'on': 'salesOrder',
                'type': 'HAS_ITEM'
            },
            {
                'source': 'sales_order_items',
                'target': 'sales_order_schedule_lines',
                'on': 'salesOrder',
                'type': 'HAS_SCHEDULE'
            },
            {
                'source': 'sales_order_items',
                'target': 'products',
                'source_col': 'material',
                'target_col': 'product',
                'type': 'CONTAINS_PRODUCT'
            },
            {
                'source': 'sales_order_headers',
                'target': 'business_partners',
                'source_col': 'soldToParty',
                'target_col': 'businessPartner',
                'type': 'ORDERED_BY'
            },
            {
                'source': 'outbound_delivery_items',
                'target': 'sales_order_items',
                'source_col': 'referenceSDDocument',
                'target_col': 'salesOrder',
                'type': 'DELIVERS'
            },
            {
                'source': 'outbound_delivery_headers',
                'target': 'outbound_delivery_items',
                'on': 'deliveryDocument',
                'type': 'HAS_ITEM'
            },
            {
                'source': 'billing_document_headers',
                'target': 'billing_document_items',
                'on': 'billingDocument',
                'type': 'HAS_ITEM'
            },
            {
                'source': 'billing_document_items',
                'target': 'sales_order_items',
                'source_col': 'salesDocument',
                'target_col': 'salesOrder',
                'type': 'BILLS'
            },
            {
                'source': 'billing_document_headers',
                'target': 'business_partners',
                'source_col': 'soldToParty',
                'target_col': 'businessPartner',
                'type': 'BILLED_TO'
            },
            {
                'source': 'billing_document_headers',
                'target': 'billing_document_cancellations',
                'on': 'billingDocument',
                'type': 'CANCELLED_BY'
            },
            {
                'source': 'business_partners',
                'target': 'business_partner_addresses',
                'on': 'businessPartner',
                'type': 'HAS_ADDRESS'
            },
            {
                'source': 'business_partners',
                'target': 'customer_company_assignments',
                'source_col': 'businessPartner',
                'target_col': 'customer',
                'type': 'ASSIGNED_TO_COMPANY'
            },
            {
                'source': 'business_partners',
                'target': 'customer_sales_area_assignments',
                'source_col': 'businessPartner',
                'target_col': 'customer',
                'type': 'IN_SALES_AREA'
            },
            {
                'source': 'products',
                'target': 'product_descriptions',
                'on': 'product',
                'type': 'DESCRIBED_BY'
            },
            {
                'source': 'products',
                'target': 'product_plants',
                'on': 'product',
                'type': 'AVAILABLE_AT'
            },
            {
                'source': 'products',
                'target': 'product_storage_locations',
                'on': 'product',
                'type': 'STORED_AT'
            },
            {
                'source': 'billing_document_headers',
                'target': 'journal_entry_items_accounts_receivable',
                'source_col': 'accountingDocument',
                'target_col': 'accountingDocument',
                'type': 'GENERATES_ENTRY'
            },
            {
                'source': 'journal_entry_items_accounts_receivable',
                'target': 'payments_accounts_receivable',
                'on': 'accountingDocument',
                'type': 'PAID_BY'
            },
            {
                'source': 'outbound_delivery_items',
                'target': 'products',
                'source_col': 'material',
                'target_col': 'product',
                'type': 'DELIVERS_PRODUCT'
            },
        ]

        for rel in relationships:
            source_table = rel['source']
            target_table = rel['target']

            if source_table not in table_columns or target_table not in table_columns:
                continue

            if source_table not in node_index or target_table not in node_index:
                continue

            try:
                if 'on' in rel:
                    s_col = t_col = rel['on']
                else:
                    s_col = rel['source_col']
                    t_col = rel['target_col']

                if s_col not in node_index[source_table]:
                    continue
                if t_col not in node_index[target_table]:
                    continue

                source_lookup = node_index[source_table][s_col]
                target_lookup = node_index[target_table][t_col]

                edge_count = 0
                for val, s_node_id in source_lookup.items():
                    t_node_id = target_lookup.get(val)
                    if t_node_id and s_node_id != t_node_id:
                        if not self.graph.has_edge(s_node_id, t_node_id):
                            self.graph.add_edge(
                                s_node_id, t_node_id,
                                relationship=rel['type']
                            )
                            edge_count += 1

                if edge_count > 0:
                    print(f"  Edge: {source_table} -[{rel['type']}]-> "
                          f"{target_table} ({edge_count} edges)")

            except Exception as e:
                print(f"  Skip {source_table}->{target_table}: {e}")

    def get_graph_data_for_visualization(self, limit=200):
        """Convert graph to frontend format."""
        nodes = []
        edges = []

        all_nodes = list(self.graph.nodes(data=True))[:limit]
        node_ids_in_view = set()

        for node_id, data in all_nodes:
            node_ids_in_view.add(node_id)
            table = data.get('table', 'unknown')
            label = data.get('label', node_id)

            nodes.append({
                'id': node_id,
                'label': label,
                'type': table,
                'data': {k: v for k, v in data.items()
                         if k not in ('table', 'label')}
            })

        for source, target, data in self.graph.edges(data=True):
            if source in node_ids_in_view and target in node_ids_in_view:
                edges.append({
                    'source': source,
                    'target': target,
                    'relationship': data.get('relationship', 'RELATED_TO')
                })

        return {'nodes': nodes, 'edges': edges}

    def get_node_neighbors(self, node_id, depth=1):
        if not self.graph.has_node(node_id):
            return {'nodes': [], 'edges': []}

        visited = {node_id}
        current_level = {node_id}
        all_edges = set()

        for d in range(depth):
            next_level = set()
            for node in current_level:
                for nb in self.graph.successors(node):
                    if nb not in visited:
                        visited.add(nb)
                        next_level.add(nb)
                    all_edges.add((node, nb))
                for nb in self.graph.predecessors(node):
                    if nb not in visited:
                        visited.add(nb)
                        next_level.add(nb)
                    all_edges.add((nb, node))
            current_level = next_level

        nodes = []
        for nid in visited:
            data = self.graph.nodes[nid]
            nodes.append({
                'id': nid,
                'label': data.get('label', nid),
                'type': data.get('table', 'unknown'),
                'data': {k: v for k, v in data.items()
                         if k not in ('table', 'label')}
            })

        edges = []
        for s, t in all_edges:
            ed = self.graph.get_edge_data(s, t, {})
            edges.append({
                'source': s,
                'target': t,
                'relationship': ed.get('relationship', 'RELATED_TO')
            })

        return {'nodes': nodes, 'edges': edges}

    def search_nodes(self, query, limit=20):
        query_lower = query.lower()
        results = []
        for node_id, data in self.graph.nodes(data=True):
            searchable = (node_id + " " +
                          " ".join(str(v) for v in data.values())).lower()
            if query_lower in searchable:
                results.append({
                    'id': node_id,
                    'label': data.get('label', node_id),
                    'type': data.get('table', 'unknown'),
                    'data': {k: v for k, v in data.items()
                             if k not in ('table', 'label')}
                })
                if len(results) >= limit:
                    break
        return results

    def get_flow_trace(self, entity_id, entity_type=None):
        entity_str = str(entity_id).lower()
        matching = []
        for nid, data in self.graph.nodes(data=True):
            vals = [str(v).lower() for v in data.values()]
            if entity_str in nid.lower() or entity_str in ' '.join(vals):
                if entity_type is None or data.get('table', '').lower() == entity_type.lower():
                    matching.append(nid)

        if not matching:
            return {'nodes': [], 'edges': [], 'flow': []}

        all_connected = set()
        for node in matching:
            all_connected.update(nx.descendants(self.graph, node))
            all_connected.update(nx.ancestors(self.graph, node))
            all_connected.add(node)

        return self._get_subgraph(list(all_connected))

    def _get_subgraph(self, node_ids):
        nodes = []
        edges = []
        node_set = set(node_ids)

        for nid in node_ids:
            if not self.graph.has_node(nid):
                continue
            data = self.graph.nodes[nid]
            nodes.append({
                'id': nid,
                'label': data.get('label', nid),
                'type': data.get('table', 'unknown'),
                'data': {k: v for k, v in data.items()
                         if k not in ('table', 'label')}
            })

        for s, t, data in self.graph.edges(data=True):
            if s in node_set and t in node_set:
                edges.append({
                    'source': s,
                    'target': t,
                    'relationship': data.get('relationship', 'RELATED_TO')
                })

        return {'nodes': nodes, 'edges': edges}

    def get_graph_stats(self):
        tables = {}
        for nid, data in self.graph.nodes(data=True):
            table = data.get('table', 'unknown')
            tables[table] = tables.get(table, 0) + 1

        return {
            'total_nodes': self.graph.number_of_nodes(),
            'total_edges': self.graph.number_of_edges(),
            'node_types': tables,
            'is_connected': (nx.is_weakly_connected(self.graph)
                             if self.graph.number_of_nodes() > 0 else False)
        }


# Singleton
graph_builder = GraphBuilder()