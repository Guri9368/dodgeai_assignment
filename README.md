# Graph-Based Data Modeling and Query System

A production-grade prototype that converts tabular business data into an interactive graph with an LLM-powered natural language query interface.

![Architecture](https://img.shields.io/badge/Architecture-FastAPI%20%2B%20React-blue)
![Database](https://img.shields.io/badge/Database-SQLite%20%2B%20NetworkX-green)
![LLM](https://img.shields.io/badge/LLM-Groq%20%7C%20Gemini%20%7C%20OpenRouter-purple)

## 🎯 Features

- **Graph Construction**: Automatically converts tabular business data into a graph of interconnected entities
- **Interactive Visualization**: Cytoscape.js-powered graph with node expansion, search, and highlighting
- **Natural Language Queries**: Ask questions in plain English, get data-backed answers
- **NL → SQL Translation**: LLM dynamically generates SQL queries from natural language
- **Guardrails**: Multi-layer system to reject off-topic queries
- **Query Result Highlighting**: Nodes referenced in query results are highlighted in the graph
- **Conversation Memory**: Maintains context across multiple queries

## 📐 Architecture
Frontend (React + Vite + Cytoscape.js)
↕ REST API
Backend (Python FastAPI)
├── Query Engine (NL → SQL pipeline)
├── Graph Builder (NetworkX)
├── LLM Integration (Groq/Gemini/OpenRouter)
├── Guardrails (Regex + LLM classification)
└── SQLite Database

text


### Architecture Decisions

1. **SQLite + NetworkX** over PostgreSQL or Neo4j:
   - Zero infrastructure setup
   - SQL for structured queries (LLM generates SQL easily)
   - NetworkX for graph traversals (path finding, flow tracing)
   - Single-file database, deployable anywhere
   - Perfect for prototype timeline

2. **FastAPI** over Express:
   - Async support for LLM API calls
   - Automatic OpenAPI docs
   - Pydantic for request/response validation
   - Python ecosystem (pandas, networkx)

3. **Cytoscape.js** over React Flow:
   - Better suited for large graph visualization
   - Built-in layout algorithms (cose, concentric, etc.)
   - Rich styling and interaction API
   - No need for manual node positioning

### Graph Modeling Strategy

The system automatically discovers relationships between tables by:
1. Scanning column names for common ID patterns (order_id, customer_id, etc.)
2. Matching columns across tables based on naming conventions
3. Creating edges where foreign key relationships are found via JOINs
4. Supporting manual relationship configuration

Node types correspond to database tables (orders, deliveries, invoices, etc.)
Edge types describe the relationship (HAS_ORDER, FULFILLED_BY, etc.)

### LLM Prompting Strategy

**Two-stage pipeline:**
1. **SQL Generation**: System prompt with full schema, column types, and sample data → generates precise SQL
2. **Response Formatting**: Takes SQL results and formats into natural language with data references

**Key prompt engineering techniques:**
- Include full schema with sample data for grounding
- Explicit rules (only SELECT, use LIMIT, handle NULLs)
- Conversation history for context
- Error recovery with automatic retry on SQL failures

### Guardrail Strategy

**Multi-layer approach:**
1. **Rule-based (fast)**: Regex patterns catch obvious off-topic queries (poems, sports, weather)
2. **LLM Classification**: Query classified as DATA_QUERY, FLOW_TRACE, BROKEN_FLOW, or OFF_TOPIC
3. **SQL Validation**: Only SELECT queries allowed, dangerous keywords blocked
4. **Response Grounding**: LLM instructed to only use actual query results

## 🚀 Setup & Run Locally

### Prerequisites
- Python 3.9+
- Node.js 18+
- An API key from Groq, Gemini, or OpenRouter (free tier)

### 1. Clone the repository
```bash
git clone <repo-url>
cd graph-query-system
2. Download the dataset
Download from Google Drive
and place it as data/dataset.xlsx

3. Setup Backend
Bash

cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your API key
Edit backend/.env:

env

GROQ_API_KEY=your_key_here    # Get from https://console.groq.com
LLM_PROVIDER=groq
DATA_FILE_PATH=../data/dataset.xlsx
4. Start Backend
Bash

cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
The API will be available at http://localhost:8000
API docs at http://localhost:8000/docs

5. Setup & Start Frontend
Bash

cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
The app will be available at http://localhost:5173

🧪 Example Queries
Query	What It Does
"Which products are associated with the highest number of billing documents?"	Aggregation query with GROUP BY
"Trace the full flow of billing document 12345"	Multi-table JOIN traversal
"Show me sales orders that were delivered but not billed"	LEFT JOIN with NULL check for broken flows
"How many orders does each customer have?"	Customer-order aggregation
"What tables are available?"	Schema exploration
"Write a poem"	Rejected - off-topic guardrail
"Who won the world cup?"	Rejected - off-topic guardrail
🚢 Deployment
Frontend → Vercel
Bash

cd frontend
npm run build
# Deploy dist/ to Vercel
# Set VITE_API_URL environment variable to backend URL
Backend → Render / Railway
Bash

# Dockerfile or use Render's Python environment
# Set environment variables:
#   GROQ_API_KEY, LLM_PROVIDER, DATA_FILE_PATH
# Start command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
Environment Variables for Deployment
Backend:

GROQ_API_KEY / GEMINI_API_KEY / OPENROUTER_API_KEY
LLM_PROVIDER (groq/gemini/openrouter)
DATA_FILE_PATH (path to dataset.xlsx)
Frontend:

VITE_API_URL (backend URL, e.g., https://your-backend.onrender.com)
📁 Project Structure
text

project-root/
├── frontend/           # React + Vite app
│   ├── src/
│   │   ├── components/ # UI components
│   │   ├── services/   # API client
│   │   └── App.jsx     # Main app
│   └── package.json
├── backend/            # Python FastAPI server
│   ├── app/
│   │   ├── main.py           # App entry point
│   │   ├── database.py       # SQLite operations
│   │   ├── graph_builder.py  # NetworkX graph
│   │   ├── query_engine.py   # NL→SQL pipeline
│   │   ├── llm_service.py    # LLM API integration
│   │   ├── guardrails.py     # Query filtering
│   │   ├── prompt_templates.py
│   │   └── routes/           # API endpoints
│   └── requirements.txt
├── data/               # Dataset files
├── sessions/           # AI coding logs
└── README.md
🔧 Tech Stack
Component	Technology
Frontend	React 18, Vite, Cytoscape.js
Backend	Python, FastAPI, Uvicorn
Database	SQLite
Graph Engine	NetworkX
LLM	Groq (Llama 3.3 70B) / Gemini / OpenRouter
Deployment	Vercel + Render
text


---

## Setup Instructions (Step-by-Step)

Here's exactly what you need to do to get this running:

### Step 1: Create the project structure

```bash
mkdir graph-query-system
cd graph-query-system
mkdir -p frontend/src/components frontend/src/services frontend/public
mkdir -p backend/app/routes
mkdir -p data sessions
Step 2: Copy all the files above into their respective locations
Step 3: Download the dataset
Download from: https://drive.google.com/file/d/1UqaLbFaveV-3MEuiUrzKydhKmkeC1iAL/view

Save as data/dataset.xlsx

Step 4: Get a free LLM API key
Groq (recommended - fastest):

Go to https://console.groq.com
Sign up (free)
Go to API Keys → Create API Key
Copy the key
OR Gemini:

Go to https://ai.google.dev
Get API key from Google AI Studio
OR OpenRouter:

Go to https://openrouter.ai
Sign up and get free credits
Step 5: Setup Backend
Bash

cd backend

# Create virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
Edit backend/.env:

text

GROQ_API_KEY=gsk_your_actual_key_here
LLM_PROVIDER=groq
DATA_FILE_PATH=../data/dataset.xlsx
Step 6: Start Backend
Bash

cd backend
uvicorn app.main:app --reload --port 8000
You should see:

text

Starting Graph-Based Business Data Query System
Found data file at: ../data/dataset.xlsx
Loaded sheet 'Orders' as table 'orders' with X rows
...
Building graph...
Graph stats: {'total_nodes': ..., 'total_edges': ...}
System ready!
Verify at: http://localhost:8000/docs

Step 7: Setup Frontend
Open a new terminal:

Bash

cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
Step 8: Open the app
Go to http://localhost:5173

You should see:

Graph visualization on the left
Chat interface on the right
Example queries to click on
Step 9: Test it!
Try these queries:

Click "How many orders are there in total?"
Type "Which products are associated with the highest number of billing documents?"
Type "Write a poem" (should be rejected)
Try "Show me broken flows where delivery exists but no invoice"
Troubleshooting
"Data file not found": Make sure data/dataset.xlsx exists

"LLM call error": Check your API key in backend/.env

"CORS error": Make sure you're accessing frontend at localhost:5173 (Vite proxy handles CORS)

Graph is empty: Check backend logs for database loading errors. Run python data/preprocess.py to analyze the dataset.

Backend won't start: Make sure you activated the virtual environment and installed all requirements.