from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from .database import init_database, get_all_tables
from .graph_builder import graph_builder
from .routes.chat import router as chat_router
from .routes.graph import router as graph_router
from .config import settings

app = FastAPI(
    title="Graph-Based Business Data Query System",
    description="LLM-powered natural language interface for business data",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://*.vercel.app",   # covers all your Vercel preview URLs
        # add your specific vercel URL here once deployed e.g.:
        # "https://your-app.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(graph_router)


@app.on_event("startup")
async def startup():
    print("=" * 60)
    print("Starting Graph-Based Business Data Query System")
    print("=" * 60)

    data_path = settings.DATA_FILE_PATH
    db_path = settings.DATABASE_PATH

    # Try multiple possible data locations
    possible_paths = [
        data_path,
        "../data/sap-o2c-data",
        "../data",
        "data/sap-o2c-data",
        os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'sap-o2c-data'),
        os.path.join(os.path.dirname(__file__), '..', '..', 'data'),
    ]

    # ALWAYS rebuild database to make sure all tables are loaded
    loaded = False
    for path in possible_paths:
        abs_path = os.path.abspath(path)
        print(f"Trying data path: {abs_path}")
        if os.path.exists(path):
            print(f"  FOUND! Loading from: {abs_path}")
            # Delete old db to force fresh load
            if os.path.exists(db_path):
                os.remove(db_path)
            loaded = init_database(path)
            if loaded:
                break
            else:
                print(f"  Failed to load from {path}")
        else:
            print(f"  Not found")

    if not loaded:
        # Check if db already exists with data
        if os.path.exists(db_path):
            tables = get_all_tables()
            if len(tables) > 5:
                print(f"Using existing database with {len(tables)} tables")
                loaded = True

    if not loaded:
        print("\n" + "!" * 60)
        print("WARNING: Could not load data!")
        print("Make sure sap-o2c-data folder is inside the data/ directory")
        print("!" * 60)
    else:
        tables = get_all_tables()
        print(f"\nAll tables loaded: {tables}")

    # Build graph
    print("\nBuilding graph...")
    graph_builder.build_graph()
    stats = graph_builder.get_graph_stats()
    print(f"Graph stats: {stats}")
    print("=" * 60)
    print("System ready!")
    print("=" * 60)


@app.get("/")
async def root():
    return {
        "message": "Graph-Based Business Data Query System API",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    tables = get_all_tables()
    return {"status": "healthy", "tables": len(tables)}