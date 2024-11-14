# KG-network

Mock Knowledge Graph Generator for NLP Conversations.

### Rest Endpoint
```
python src/api_wrapper.py 
```
open browser http://<ip_address>/docs/

### Manual steps
To run mock generator manually
```
python src/mock_generator.py
```

To build RDF ontology  manually
```
python src/network_processor.py
```

Open data/output/relationships.html in browser to see relationship


### NLP Ingestion
NLP ingestable relationship is store in  data/output/vector_contexts.jsonl

### System prompt.
Use the sample prompt.md content for better formatted results. Tune them as required.

### Models Tested.
Ollama : llama3.2:3b


### Development in Progress. 
* Building docker-compose for portability
* exposing relationships.html on a web endpoint
* exposing vector_context.jsonl and llm prompt as API
 
