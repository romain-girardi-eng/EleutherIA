# EleutherIA Examples

Usage examples for the EleutherIA API and Python packages.

## Quick Start Examples

- [Python](python/) - Python package examples
- [curl](curl/) - Command-line API examples
- [Postman](postman/) - Postman collection for API testing

## Python Examples

```python
# Install packages
pip install eleutheria-database eleutheria-kg eleutheria-graphrag[llm]

# Run example
python docs/examples/python/basic_query.py
```

## curl Examples

```bash
# Search for passages
curl "http://localhost:8000/api/search?q=fate&limit=10"

# GraphRAG query
curl -X POST "http://localhost:8000/api/graphrag/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Stoic fate?"}'
```

## Postman

Import `docs/examples/postman/eleutheria.postman_collection.json` into Postman.
