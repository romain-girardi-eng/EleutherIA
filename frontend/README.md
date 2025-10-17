# EleutherIA Frontend - Ancient Free Will Database

React + TypeScript frontend for the Ancient Free Will Database, providing interactive visualization and exploration of 465 knowledge graph nodes, 289 ancient texts, and GraphRAG-powered question answering.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm
- Backend API running on port 8000 (see `../backend/README.md`)
- PostgreSQL database with 289 texts
- Qdrant vector database with embeddings

### Installation

```bash
cd frontend
npm install
```

### Configuration

Create `.env` file:
```bash
VITE_API_URL=http://localhost:8000
```

### Development

```bash
npm run dev
```

Frontend will be available at: http://localhost:5173

### Production Build

```bash
npm run build
npm run preview
```

## 📊 Features

### 1. Knowledge Graph Visualizer (`/visualizer`)
- **Interactive Cytoscape.js network visualization**
- 465 nodes (persons, works, concepts, arguments, debates)
- 740 edges (relationships, influences, critiques)
- Color-coded by node type
- Click nodes to see details
- Pan, zoom, fit controls
- COSE layout algorithm

**Node Types:**
- 🔵 Person (philosophers, theologians) - `#0284c7`
- 🔵 Work (treatises, dialogues) - `#7dd3fc`
- 🟡 Concept (philosophical terms) - `#fbbf24`
- 🔴 Argument (specific arguments) - `#f87171`
- 🟣 Debate (philosophical debates) - `#a78bfa`

### 2. Hybrid Search (`/search`)
- **Three search modes combined with Reciprocal Rank Fusion (RRF)**
  - Full-text (PostgreSQL ts_rank)
  - Lemmatic (109 lemmatized texts)
  - Semantic (Qdrant vector similarity)
- Toggle each mode on/off
- Tabbed results view (Combined, Full-text, Lemmatic, Semantic)
- Result cards with metadata, snippets, scores
- Supports Greek, Latin, and English queries

**Example queries:**
- Greek: `ἐφ' ἡμῖν`, `ἑκούσιον`, `προαίρεσις`
- Latin: `liberum arbitrium`, `in nostra potestate`, `voluntarium`
- English: `voluntary action`, `free will`, `moral responsibility`

### 3. GraphRAG Question Answering (`/graphrag`)
- **6-step GraphRAG pipeline with streaming responses**
  1. Semantic search on KG (find relevant nodes)
  2. Graph traversal via BFS (expand context)
  3. Context assembly (gather node data)
  4. Citation extraction (ancient sources + modern scholarship)
  5. LLM answer generation (Gemini 2.5 Pro)
  6. Real-time streaming to UI

**Features:**
- Chat-style interface with message history
- Server-Sent Events (SSE) for real-time progress
- Advanced settings panel:
  - `semantic_k`: Starting nodes from search (default: 10)
  - `graph_depth`: BFS traversal depth (default: 2)
  - `max_context`: Nodes in LLM context (default: 15)
- Citation display (ancient sources + modern scholarship)
- Markdown rendering of answers
- Stop button to cancel streaming
- Statistics sidebar

### 4. Ancient Texts Explorer (`/texts`)
- **Browse 289 ancient philosophical texts**
- Filter by category (New Testament, Origen, Tertullian, Original Works, etc.)
- Filter by author and language
- Pagination (20 texts per page)
- Text detail modal with:
  - Full metadata
  - Raw text content (Greek/Latin/English)
  - Lemmas for 109 lemmatized texts
  - Source citations
- Statistics: 289 total texts, 109 lemmatized

## 🏗️ Architecture

### Project Structure

```
frontend/
├── src/
│   ├── api/
│   │   └── client.ts           # API client (all backend endpoints)
│   ├── components/
│   │   └── CytoscapeVisualizer.tsx  # Graph visualization component
│   ├── pages/
│   │   ├── HomePage.tsx        # Landing page
│   │   ├── KGVisualizerPage.tsx  # Graph visualizer page
│   │   ├── SearchPage.tsx      # Hybrid search page
│   │   ├── GraphRAGPage.tsx    # Q&A page with streaming
│   │   └── TextExplorerPage.tsx  # Text browser page
│   ├── types/
│   │   └── index.ts            # TypeScript definitions
│   ├── App.tsx                 # Main app with routing
│   ├── index.css               # Academic styling theme
│   └── main.tsx                # Entry point
├── .env                        # Environment configuration
├── package.json
├── tailwind.config.js          # Tailwind theme (academic colors)
├── postcss.config.js
├── tsconfig.json
├── vite.config.ts
└── README.md
```

### Tech Stack

**Core:**
- React 18.3.1
- TypeScript 5.5+
- Vite 5.4.1

**UI & Styling:**
- Tailwind CSS 3.4.1 (custom academic theme)
- Serif fonts (Georgia, Palatino) for scholarly aesthetic
- Custom color palette (primary blues, academic grays)
- Greek/Latin text support

**Visualization:**
- Cytoscape.js 3.30+ (network graphs)
- COSE layout algorithm

**Routing:**
- React Router DOM 6.26.2

**HTTP & Streaming:**
- Axios 1.7.7 (REST API calls)
- EventSource API (Server-Sent Events)

**Content Rendering:**
- React Markdown 9.0.1 (LLM responses)

### Type System

Complete TypeScript interfaces in `src/types/index.ts`:

```typescript
// Knowledge Graph
export interface KGNode {
  id: string;
  label: string;
  type: string;
  category: string;
  description: string;
  period?: string;
  school?: string;
  // ... more fields
}

// Search
export interface HybridSearchResponse {
  combined_results: SearchResult[];
  fulltext_results: SearchResult[];
  lemmatic_results: SearchResult[];
  semantic_results: SearchResult[];
  total_found: number;
}

// GraphRAG
export interface GraphRAGResponse {
  query: string;
  answer: string;
  citations: {
    ancient_sources: string[];
    modern_scholarship: string[];
  };
  reasoning_path: {
    starting_nodes: Array<{ id: string; label: string; type: string; reason: string; }>;
    expanded_nodes: Array<{ id: string; label: string; type: string; reason: string; }>;
    // ...
  };
  nodes_used: number;
  edges_traversed: number;
}

// Streaming
export interface GraphRAGStreamEvent {
  type: 'status' | 'answer_chunk' | 'complete' | 'error';
  message?: string;
  data?: any;
}

// Texts
export interface AncientText {
  id: string;
  title: string;
  author: string;
  category: string;
  language: string;
  raw_text: string;
  lemmas?: string[];
  source?: string;
  notes?: string;
}
```

### API Client

Singleton instance in `src/api/client.ts` with all backend endpoints:

```typescript
class ApiClient {
  // Knowledge Graph
  async getNodes(filters?: { type?: string; period?: string; school?: string })
  async getCytoscapeData(): Promise<CytoscapeData>
  async getKGStats()

  // Search
  async hybridSearch(query: SearchQuery): Promise<HybridSearchResponse>
  async fulltextSearch(query: string, limit: number)
  async lemmaticSearch(query: string, limit: number)
  async semanticSearch(query: string, limit: number, collection: string)
  async searchKG(query: string, limit: number)

  // GraphRAG
  async graphragQuery(query: GraphRAGQuery): Promise<GraphRAGResponse>
  graphragQueryStream(query: GraphRAGQuery): EventSource

  // Texts
  async listTexts(filters?: { category?: string; author?: string; language?: string; offset?: number; limit?: number; })
  async getText(id: string): Promise<AncientText>
  async getTextStats()

  // Authentication (Semativerse)
  async checkSemativersePermission(request: SemativersePermissionRequest)
}

export const apiClient = new ApiClient();
```

### Styling Theme

Academic theme in `tailwind.config.js`:

```javascript
theme: {
  extend: {
    colors: {
      primary: {
        50: '#f0f9ff',
        100: '#e0f2fe',
        200: '#bae6fd',
        300: '#7dd3fc',
        400: '#38bdf8',
        500: '#0ea5e9',
        600: '#0284c7',
        700: '#0369a1',
        800: '#075985',
        900: '#0c4a6e',
      },
      academic: {
        bg: '#fafaf9',
        paper: '#ffffff',
        text: '#1c1917',
        muted: '#78716c',
        border: '#e7e5e4',
      }
    },
    fontFamily: {
      serif: ['Georgia', 'Palatino', 'Times New Roman', 'serif'],
    },
  },
}
```

Custom utility classes in `index.css`:

```css
.academic-card { /* paper-style card */ }
.academic-button { /* primary button */ }
.academic-button-outline { /* outline button */ }
.greek-text { /* Greek text styling */ }
.latin-text { /* Latin text styling */ }
.citation { /* citation block */ }
.markdown-content { /* prose styling for LLM responses */ }
```

## 🔌 API Integration

All API calls go through the singleton `apiClient` instance.

### Backend Endpoints Used

**Knowledge Graph:**
- `GET /api/kg/nodes` - Fetch KG nodes with filters
- `GET /api/kg/node/{id}` - Get single node
- `GET /api/kg/viz/cytoscape` - Get Cytoscape-formatted data
- `GET /api/kg/stats` - Get KG statistics

**Search:**
- `POST /api/search/hybrid` - Hybrid search with RRF
- `POST /api/search/fulltext` - Full-text search
- `POST /api/search/lemmatic` - Lemmatic search
- `POST /api/search/semantic` - Semantic vector search

**GraphRAG:**
- `POST /api/graphrag/query` - Standard GraphRAG query
- `GET /api/graphrag/query/stream` - Streaming GraphRAG with SSE
- `GET /api/graphrag/status` - Check GraphRAG service status

**Texts:**
- `GET /api/texts/list` - List texts with filters and pagination
- `GET /api/texts/{id}` - Get full text by ID
- `GET /api/texts/stats/overview` - Get text statistics

**Health:**
- `GET /api/health` - Backend health check

### Streaming with Server-Sent Events

GraphRAG streaming uses EventSource API:

```typescript
const eventSource = new EventSource(
  `${API_URL}/api/graphrag/query/stream?query=${query}&semantic_k=10&graph_depth=2`
);

eventSource.onmessage = (event) => {
  const data: GraphRAGStreamEvent = JSON.parse(event.data);

  switch (data.type) {
    case 'status':
      // Update status message
      break;
    case 'answer_chunk':
      // Append to answer
      break;
    case 'complete':
      // Final response with citations
      break;
    case 'error':
      // Handle error
      break;
  }
};

eventSource.onerror = () => {
  eventSource.close();
  // Handle completion
};
```

## 🧪 Testing

### Manual Testing Checklist

**Knowledge Graph:**
- [ ] Graph loads with 465 nodes, 740 edges
- [ ] Click node to see details in inspector panel
- [ ] Pan, zoom, fit controls work
- [ ] Colors match node types

**Search:**
- [ ] Full-text search works for English terms
- [ ] Lemmatic search finds inflected forms
- [ ] Semantic search returns conceptually similar results
- [ ] Combined (RRF) ranks results appropriately
- [ ] Tabs show different result sets

**GraphRAG:**
- [ ] Question answering works with citations
- [ ] Streaming shows real-time progress
- [ ] Status updates reflect pipeline steps
- [ ] Citations display correctly (ancient + modern)
- [ ] Stop button cancels streaming
- [ ] Advanced settings affect results

**Texts:**
- [ ] List shows 289 texts
- [ ] Filters work (category, author, language)
- [ ] Pagination works (20 per page)
- [ ] Click text opens detail modal
- [ ] Greek/Latin text renders correctly
- [ ] Lemmas display for lemmatized texts

### Backend Health Check

```bash
curl http://localhost:8000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "qdrant": "connected"
}
```

## 📝 Development Notes

### State Management
- Uses React hooks (useState, useEffect, useRef)
- No external state management library
- API client is singleton for consistency

### Performance Considerations
- Cytoscape rendering is CPU-intensive for large graphs
- Text content truncated to 5000 chars in modal
- Pagination for texts (20 per page)

### Browser Compatibility
- Tested on Chrome 120+, Firefox 120+, Safari 17+
- Requires modern browser with ES6+ support
- EventSource API for streaming

## 🚢 Deployment

### Build for Production

```bash
npm run build
```

Output in `dist/` directory.

### Environment Variables

Production `.env`:
```bash
VITE_API_URL=https://api.yourdomain.com
```

## 📄 License

CC BY 4.0 - Same as parent project

## 👤 Author

**Romain Girardi**
- Email: romain.girardi@univ-cotedazur.fr
- ORCID: 0000-0002-5310-5346

## 🔗 Related Documentation

- Backend API: `../backend/README.md`
- Database schema: `../DATA_DICTIONARY.md`
- Project overview: `../README.md`
