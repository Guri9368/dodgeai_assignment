from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from ..graph_builder import graph_builder
from ..database import get_all_tables, get_table_data

router = APIRouter(prefix="/api/graph", tags=["graph"])


@router.get("/")
async def get_graph(limit: int = Query(default=200, le=2000)):
    """Get graph data for visualization."""
    data = graph_builder.get_graph_data_for_visualization(limit=limit)
    return data


@router.get("/stats")
async def get_graph_stats():
    """Get graph statistics."""
    return graph_builder.get_graph_stats()


@router.get("/node/{node_id}")
async def get_node_neighbors(node_id: str, depth: int = Query(default=1, le=3)):
    """Get a node and its neighbors."""
    data = graph_builder.get_node_neighbors(node_id, depth=depth)
    if not data['nodes']:
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
    return data


@router.get("/search")
async def search_nodes(q: str = Query(..., min_length=1), limit: int = Query(default=20, le=100)):
    """Search for nodes by text."""
    results = graph_builder.search_nodes(q, limit=limit)
    return {"results": results, "count": len(results)}


@router.get("/tables")
async def list_tables():
    """List all available tables."""
    tables = get_all_tables()
    return {"tables": tables}


@router.get("/table/{table_name}")
async def get_table(table_name: str, limit: int = Query(default=50, le=500)):
    """Get data from a specific table."""
    data = get_table_data(table_name, limit=limit)
    return {"table": table_name, "data": data, "count": len(data)}


@router.get("/flow/{entity_id}")
async def trace_flow(entity_id: str, entity_type: Optional[str] = None):
    """Trace the full flow of an entity."""
    data = graph_builder.get_flow_trace(entity_id, entity_type)
    return data


@router.get("/types")
async def get_node_types():
    """Get all node types (tables) with counts."""
    stats = graph_builder.get_graph_stats()
    return {"types": stats['node_types']}