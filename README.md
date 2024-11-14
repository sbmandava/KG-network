# KG-network

Mock Knowledge Graph Generator for NLP Conversations.

### to invoke API for rest calls.
python src/api_wrapper.py 

### ---- Manual steps---
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

Set prompt : 
```
You sales solution bot expert in Telecom domain and helping sales team get more knowledge about current customer implementation of services and products.
Ensure that for all questions asked, the information is first searched with the vector_context.jsonl. Your goal is to help the sales team upsell more services.

Don't Hallucinate. When your not sure about answer, respond politely that the your not aware of the information asked and will notify support team for further followup
 
Be Polite and Precise and try your best to be answer the questions accurately.
```

### Development in Progress. 
* Building docker-compose for portability
* exposing relationships.html on a web endpoint
* exposing vector_context.jsonl and llm prompt as API
 
