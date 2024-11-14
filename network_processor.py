from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS
import json
import os
import networkx as nx
from pathlib import Path
import matplotlib.pyplot as plt
import base64
from io import BytesIO
import textwrap
from datetime import datetime
from typing import Dict, List, Any, Tuple

class NetworkDataProcessor:
    def __init__(self):
        self.input_dir = "output"
        self.output_dir = "output"
        self.g = Graph()
        self.gtt = Namespace("http://gtt.com/ontology#")
        self.g.bind("gtt", self.gtt)
        self.relationships = []
        self.vector_contexts = []
        
    def setup_directories(self):
        """Create necessary directories"""
        Path(self.output_dir).mkdir(exist_ok=True)
        
    def load_json_file(self, filename: str) -> List[Dict]:
        """Load and parse JSON file"""
        file_path = os.path.join(self.input_dir, filename)
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        return []

    def create_uri(self, kind: str, namespace: str, name: str) -> URIRef:
        """Create URI for resource"""
        return URIRef(f"{self.gtt}{kind}_{namespace}_{name}")

    def generate_relationship_text(self, rel: Dict) -> str:
        """Generate human-readable text for relationship"""
        return f"{rel['from']} has {rel['label']} relationship with {rel['to']}"

    def generate_resource_context(self, resource: Dict) -> str:
        """Generate context description for a resource"""
        context_parts = []
        
        # Basic resource information
        context_parts.append(f"Resource Type: {resource.get('kind', 'Unknown')}")
        context_parts.append(f"Name: {resource.get('name', 'Unknown')}")
        context_parts.append(f"Namespace: {resource.get('namespace', 'Unknown')}")
        
        # Metadata information
        if 'metadata' in resource:
            metadata = resource['metadata']
            context_parts.append("\nMetadata:")
            for key, value in metadata.items():
                if isinstance(value, dict):
                    context_parts.append(f"  {key}:")
                    for k, v in value.items():
                        context_parts.append(f"    {k}: {v}")
                else:
                    context_parts.append(f"  {key}: {value}")
        
        # Specification information
        if 'spec' in resource:
            spec = resource['spec']
            context_parts.append("\nSpecification:")
            for key, value in spec.items():
                if isinstance(value, dict):
                    context_parts.append(f"  {key}:")
                    for k, v in value.items():
                        context_parts.append(f"    {k}: {v}")
                else:
                    context_parts.append(f"  {key}: {value}")
        
        return "\n".join(context_parts)

    def add_reference_relationship(self, subject_uri: URIRef, ref_field: str, ref_data: Dict):
        """Add reference relationship to graph and tracking"""
        if isinstance(ref_data, dict) and all(k in ref_data for k in ['kind', 'namespace', 'name']):
            obj_uri = self.create_uri(ref_data['kind'], ref_data['namespace'], ref_data['name'])
            self.g.add((subject_uri, self.gtt[ref_field], obj_uri))
            
            relationship = {
                'from': str(subject_uri).split('#')[1],
                'to': str(obj_uri).split('#')[1],
                'label': ref_field,
                'from_uri': str(subject_uri),
                'to_uri': str(obj_uri)
            }
            self.relationships.append(relationship)
            
            # Generate context for vector store
            context = {
                'text': self.generate_relationship_text(relationship),
                'metadata': {
                    'relationship_type': ref_field,
                    'source': str(subject_uri),
                    'target': str(obj_uri)
                }
            }
            self.vector_contexts.append(context)

    def process_spec(self, resource_uri: URIRef, spec_data: Dict, resource: Dict):
        """Process specification data"""
        if not isinstance(spec_data, dict):
            return

        # Process direct references
        for key, value in spec_data.items():
            if key.endswith('Ref'):
                self.add_reference_relationship(resource_uri, key, value)
            elif isinstance(value, dict):
                # Process nested references
                for nested_key, nested_value in value.items():
                    if nested_key.endswith('Ref'):
                        self.add_reference_relationship(resource_uri, f"{key}_{nested_key}", nested_value)

        # Generate context for the entire spec
        context = {
            'text': self.generate_resource_context(resource),
            'metadata': {
                'resource_type': str(resource_uri).split('#')[1].split('_')[0],
                'resource_uri': str(resource_uri)
            }
        }
        self.vector_contexts.append(context)

    def generate_ontology_and_vectors(self):
        """Generate ontology and vector contexts"""
        json_files = [f for f in os.listdir(self.input_dir) if f.endswith('.json')]
        
        for filename in json_files:
            data = self.load_json_file(filename)
            for resource in data:
                if all(k in resource for k in ['kind', 'namespace', 'name']):
                    resource_uri = self.create_uri(resource['kind'], resource['namespace'], resource['name'])
                    self.g.add((resource_uri, RDF.type, self.gtt[resource['kind']]))
                    
                    if 'spec' in resource:
                        self.process_spec(resource_uri, resource['spec'], resource)

        # Save ontology
        self.g.serialize(destination=os.path.join(self.output_dir, "ontology.ttl"), format="turtle")
        
        # Save vector contexts
        self.save_vector_contexts()
        
        return self.relationships

    def save_vector_contexts(self):
        """Save vector contexts for RAG ingestion"""
        vector_file = os.path.join(self.output_dir, "vector_contexts.jsonl")
        with open(vector_file, 'w') as f:
            for context in self.vector_contexts:
                json.dump(context, f)
                f.write('\n')

    def generate_html_visualization(self):
        """Generate HTML visualization of relationships"""
        G = nx.DiGraph()
        
        # Add nodes and edges
        for rel in self.relationships:
            G.add_edge(rel['from'], rel['to'], label=rel['label'])

        # Create visualization
        plt.figure(figsize=(20, 15))
        pos = nx.spring_layout(G, k=2, iterations=50)
        
        # Draw nodes
        nx.draw_networkx_nodes(G, pos, node_color='lightblue', node_size=3000, alpha=0.7)
        nx.draw_networkx_labels(G, pos, font_size=8)
        
        # Draw edges
        nx.draw_networkx_edges(G, pos, edge_color='gray', arrows=True, arrowsize=20)
        
        # Draw edge labels
        edge_labels = nx.get_edge_attributes(G, 'label')
        nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=6)

        # Save to buffer
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Convert to base64
        img_str = base64.b64encode(buf.getvalue()).decode()

        # Generate HTML
        html_content = self.generate_html_content(img_str)
        
        # Save HTML
        with open(os.path.join(self.output_dir, "relationships.html"), 'w') as f:
            f.write(html_content)

    def generate_html_content(self, img_str: str) -> str:
        """Generate HTML content"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Network Resource Relationships</title>
            <style>
                body {{ 
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    background-color: #f5f5f5;
                    color: #333;
                }}
                .container {{
                    max-width: 1600px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 0 20px rgba(0,0,0,0.1);
                }}
                h1, h2 {{ 
                    color: #2c3e50;
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .visualization {{
                    text-align: center;
                    margin: 40px 0;
                    padding: 20px;
                    background-color: white;
                    border-radius: 8px;
                    box-shadow: 0 0 10px rgba(0,0,0,0.05);
                }}
                .visualization img {{
                    max-width: 100%;
                    height: auto;
                }}
                .relationships {{
                    margin-top: 40px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                    background-color: white;
                }}
                th, td {{
                    padding: 12px 15px;
                    border: 1px solid #ddd;
                    text-align: left;
                }}
                th {{
                    background-color: #2c3e50;
                    color: white;
                }}
                tr:nth-child(even) {{
                    background-color: #f9f9f9;
                }}
                tr:hover {{
                    background-color: #f5f5f5;
                }}
                .stats {{
                    margin: 30px 0;
                    padding: 20px;
                    background-color: #f8f9fa;
                    border-radius: 8px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Network Resource Relationships</h1>
                
                <div class="stats">
                    <h2>Network Statistics</h2>
                    <ul>
                        <li>Total Resources: {len(set([r['from'] for r in self.relationships] + [r['to'] for r in self.relationships]))}</li>
                        <li>Total Relationships: {len(self.relationships)}</li>
                        <li>Resource Types: {len(set([r['from'].split('_')[0] for r in self.relationships] + [r['to'].split('_')[0] for r in self.relationships]))}</li>
                    </ul>
                </div>

                <div class="visualization">
                    <h2>Network Visualization</h2>
                    <img src="data:image/png;base64,{img_str}" alt="Resource Relationships Graph">
                </div>

                <div class="relationships">
                    <h2>Relationship Details</h2>
                    <table>
                        <tr>
                            <th>Source Resource</th>
                            <th>Relationship Type</th>
                            <th>Target Resource</th>
                        </tr>
                        {''.join(f"<tr><td>{r['from']}</td><td>{r['label']}</td><td>{r['to']}</td></tr>" for r in self.relationships)}
                    </table>
                </div>
            </div>
        </body>
        </html>
        """

def main():
    processor = NetworkDataProcessor()
    
    try:
        print("Setting up directories...")
        processor.setup_directories()
        
        print("Processing data and generating ontology...")
        processor.generate_ontology_and_vectors()
        
        print("Generating visualization...")
        processor.generate_html_visualization()
        
        print("\nGenerated files in 'output' directory:")
        print("- ontology.ttl (RDF ontology file)")
        print("- relationships.html (Interactive visualization)")
        print("- vector_contexts.jsonl (Vector store ingestion file)")
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main()

