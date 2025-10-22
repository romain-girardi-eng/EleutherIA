#!/usr/bin/env python3
"""
GraphRAG API Routes
Endpoints for question answering using Graph RAG
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, AsyncGenerator
import logging
import json

from services.graphrag_service import GraphRAGService
from services.auth_service import check_rate_limit
from api.auth import get_current_user_dependency, User

logger = logging.getLogger(__name__)

router = APIRouter()


class GraphRAGQuery(BaseModel):
    """GraphRAG query model"""
    query: str
    semantic_k: Optional[int] = 10
    graph_depth: Optional[int] = 2
    max_context: Optional[int] = 15
    temperature: Optional[float] = 0.7
    deep_mode: Optional[bool] = False  # Include PostgreSQL full-text results


@router.post("/query")
async def graphrag_query(
    graphrag_query: GraphRAGQuery, 
    request: Request,
    current_user: User = Depends(get_current_user_dependency)
):
    """
    Answer questions using GraphRAG (Graph-based Retrieval-Augmented Generation):
    1. Semantic search (Qdrant) - find relevant starting nodes via vector similarity
    2. Graph traversal (BFS) - expand to connected nodes using graph relationships
    3. Context building - create rich context with citations from retrieved nodes
    4. LLM synthesis - generate grounded answer using knowledge graph context
    5. Citation extraction - track ancient sources and modern scholarship
    6. Reasoning path - visualize which nodes and edges were used
    """
    try:
        # Rate limiting check
        client_ip = request.client.host
        identifier = f"{current_user.username}:{client_ip}"
        
        if not check_rate_limit(identifier, limit=30, window_minutes=15):
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please wait before making another request.",
                headers={"Retry-After": "900"}  # 15 minutes
            )
        
        # Get services from app state
        db = request.app.state.db
        qdrant = request.app.state.qdrant
        llm = getattr(request.app.state, "llm", None)

        # Create GraphRAG service
        graphrag_service = GraphRAGService(qdrant, db, llm)

        # Execute complete pipeline
        result = await graphrag_service.answer_question(
            query=graphrag_query.query,
            semantic_k=graphrag_query.semantic_k,
            graph_depth=graphrag_query.graph_depth,
            max_context=graphrag_query.max_context,
            temperature=graphrag_query.temperature,
            deep_mode=graphrag_query.deep_mode
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in GraphRAG query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/stream")
async def graphrag_query_stream(
    graphrag_query: GraphRAGQuery, 
    request: Request,
    current_user: User = Depends(get_current_user_dependency)
):
    """
    Answer questions using GraphRAG with real-time streaming updates.
    Uses Server-Sent Events (SSE) to stream progress and final answer.

    Event types:
    - status: Progress updates (semantic_search, graph_traversal, etc.)
    - nodes: Nodes found during search/traversal
    - answer: Partial answer text (streamed token by token)
    - citations: Final citations
    - complete: Final complete result
    - error: Error occurred
    """

    async def generate_stream() -> AsyncGenerator[str, None]:
        """Generate SSE stream with progress updates"""
        try:
            # Rate limiting check
            client_ip = request.client.host
            identifier = f"{current_user.username}:{client_ip}"
            
            if not check_rate_limit(identifier, limit=30, window_minutes=15):
                yield f"data: {json.dumps({'type': 'error', 'message': 'Rate limit exceeded. Please wait before making another request.'})}\n\n"
                return
            
            # Get services from app state
            db = request.app.state.db
            qdrant = request.app.state.qdrant
            llm = getattr(request.app.state, "llm", None)

            # Create GraphRAG service
            graphrag_service = GraphRAGService(qdrant, db, llm)

            # Step 1: Semantic search
            yield f"data: {json.dumps({'type': 'status', 'message': 'Performing semantic search...', 'step': 1, 'total_steps': 6})}\n\n"

            starting_nodes = await graphrag_service.semantic_search_nodes(
                query=graphrag_query.query,
                limit=graphrag_query.semantic_k
            )

            yield f"data: {json.dumps({'type': 'nodes', 'data': {'starting_nodes': [n['id'] for n in starting_nodes]}, 'count': len(starting_nodes)})}\n\n"

            # Step 2: Graph traversal
            yield f"data: {json.dumps({'type': 'status', 'message': 'Traversing knowledge graph...', 'step': 2, 'total_steps': 6})}\n\n"

            expanded_nodes, traversed_edges = graphrag_service.graph_traversal_bfs(
                starting_nodes=starting_nodes,
                max_depth=graphrag_query.graph_depth,
                max_nodes=50
            )

            yield f"data: {json.dumps({'type': 'nodes', 'data': {'expanded_nodes': len(expanded_nodes), 'edges_traversed': len(traversed_edges)}})}\n\n"

            # Step 3: Extract citations
            yield f"data: {json.dumps({'type': 'status', 'message': 'Extracting citations...', 'step': 3, 'total_steps': 6})}\n\n"

            citations = graphrag_service.extract_citations(expanded_nodes)

            yield f"data: {json.dumps({'type': 'citations', 'data': citations})}\n\n"

            # Step 4: Build context
            yield f"data: {json.dumps({'type': 'status', 'message': 'Building context...', 'step': 4, 'total_steps': 6})}\n\n"

            context = graphrag_service.build_context(
                nodes=expanded_nodes,
                max_context_length=graphrag_query.max_context
            )

            # Step 5: Generate answer
            yield f"data: {json.dumps({'type': 'status', 'message': 'Generating answer with LLM...', 'step': 5, 'total_steps': 6})}\n\n"

            answer = await graphrag_service.synthesize_answer(
                query=graphrag_query.query,
                context=context,
                temperature=graphrag_query.temperature
            )

            # Stream answer (simulate token-by-token for now)
            words = answer.split()
            for i, word in enumerate(words):
                yield f"data: {json.dumps({'type': 'answer_chunk', 'data': word + ' ', 'progress': (i + 1) / len(words)})}\n\n"

            # Step 6: Create reasoning path
            yield f"data: {json.dumps({'type': 'status', 'message': 'Creating reasoning path...', 'step': 6, 'total_steps': 6})}\n\n"

            reasoning_path = graphrag_service.create_reasoning_path(
                starting_nodes=starting_nodes,
                expanded_nodes=expanded_nodes,
                traversed_edges=traversed_edges
            )

            # Send complete result
            final_result = {
                'type': 'complete',
                'data': {
                    'query': graphrag_query.query,
                    'answer': answer,
                    'citations': citations,
                    'reasoning_path': reasoning_path,
                    'nodes_used': len(expanded_nodes),
                    'edges_traversed': len(traversed_edges),
                    'success': True
                }
            }

            yield f"data: {json.dumps(final_result)}\n\n"

        except Exception as e:
            logger.error(f"Error in streaming GraphRAG query: {e}", exc_info=True)
            error_event = {
                'type': 'error',
                'message': str(e)
            }
            yield f"data: {json.dumps(error_event)}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable buffering in nginx
        }
    )


@router.get("/status")
async def graphrag_status():
    """Get GraphRAG service status"""
    return {
        'status': 'available',
        'features': [
            'Semantic search via Qdrant vector database',
            'Graph traversal via breadth-first search',
            'Automatic citation extraction',
            'LLM-powered answer synthesis',
            'Deep mode (includes PostgreSQL full-text search)',
            'Real-time streaming responses (SSE)'
        ],
        'endpoints': {
            '/query': 'Standard query (returns complete result)',
            '/query/stream': 'Streaming query (real-time progress via SSE)',
            '/status': 'Service status and capabilities'
        }
    }
