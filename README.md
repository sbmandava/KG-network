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


### NLP Ingestion and response
In your ollama chat session.

* Set you model to llama3.2:3b

* Upload the following 2 files.
  -  data/output/vector_ingestion.json
  -  data/output/ontology.ttl

* Set your system prompt to content in prompt.md

### Sample questions 
* Share me site and namespace details

### System prompt.
Fine Tune the system prompt for better results.

### Models Tested.
Ollama : llama3.2:3b


### Development in Progress. 
* Building docker-compose for portability
* exposing relationships.html on a web endpoint
* exposing NLP chat interface which automates the ingestion and prompting and expose it as streaming API
 
