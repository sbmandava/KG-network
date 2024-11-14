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
from typing import Dict, List, Any, Tuple, Optional, Set
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NetworkDataProcessor:
    def __init__(self):
        self.input_dir = "data/output"
        self.output_dir = "data/output"
        self.g = Graph()
        self.lla = Namespace("http://lla.com/ontology#")
        self.g.bind("lla", self.lla)
        self.relationships = []
        self.resource_cache = {}

    def setup_directories(self) -> None:
        """Create necessary directories"""
        try:
            Path(self.output_dir).mkdir(parents=True, exist_ok=True)
            logger.info(f"Successfully set up directory: {self.output_dir}")
        except Exception as e:
            logger.error(f"Error creating directories: {str(e)}")
            raise

    def load_json_file(self, filename: str) -> List[Dict]:
        """Load and parse JSON file"""
        file_path = os.path.join(self.input_dir, filename)
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"Error loading JSON file {filename}: {str(e)}")
            raise

    def create_uri(self, kind: str, namespace: str, name: str) -> URIRef:
        """Create URI for resource"""
        return URIRef(f"{self.lla}{kind}_{namespace}_{name}")

    def get_resource_data(self, resource_id: str) -> Optional[Dict]:
        """Get resource data from cache or files"""
        if resource_id in self.resource_cache:
            return self.resource_cache[resource_id]

        for filename in os.listdir(self.input_dir):
            if filename.endswith('.json'):
                data = self.load_json_file(filename)
                for resource in data:
                    if all(k in resource for k in ['kind', 'namespace', 'name']):
                        current_id = f"{resource['kind']}_{resource['namespace']}_{resource['name']}"
                        self.resource_cache[current_id] = resource
                        if current_id == resource_id:
                            return resource
        return None

    def format_dict_value(self, value: Any, indent: int = 0) -> str:
        """Format dictionary values for text output"""
        if isinstance(value, dict):
            return '\n' + '\n'.join(f"{'  ' * (indent + 1)}{k}: {self.format_dict_value(v, indent + 1)}"
                                    for k, v in value.items())
        elif isinstance(value, list):
            if not value:
                return '[]'
            return '\n' + '\n'.join(f"{'  ' * (indent + 1)}- {self.format_dict_value(item, indent + 1)}"
                                    for item in value)
        return str(value)

    def generate_resource_context_enhanced(self, resource_id: str) -> str:
        """Generate enhanced context description for a resource"""
        resource_data = self.get_resource_data(resource_id)
        if not resource_data:
            return f"Resource {resource_id} information not found"

        context_parts = []

        # Basic information
        context_parts.append(f"Resource Description:")
        context_parts.append(f"Type: {resource_data['kind']}")
        context_parts.append(f"Name: {resource_data['name']}")
        context_parts.append(f"Namespace: {resource_data['namespace']}")

        # Detailed metadata
        if 'metadata' in resource_data:
            context_parts.append("\nMetadata Information:")
            for key, value in resource_data['metadata'].items():
                context_parts.append(f"{key}:{self.format_dict_value(value)}")

        # Specification details
        if 'spec' in resource_data:
            context_parts.append("\nResource Specification:")
            for key, value in resource_data['spec'].items():
                context_parts.append(f"{key}:{self.format_dict_value(value)}")

        # Related resources
        related_resources = [rel for rel in self.relationships
                             if rel['from'] == resource_id or rel['to'] == resource_id]

        if related_resources:
            context_parts.append("\nResource Relationships:")
            for rel in related_resources:
                if rel['from'] == resource_id:
                    context_parts.append(
                        f"- Has {rel['label']} relationship with {rel['to']}")
                else:
                    context_parts.append(
                        f"- Is {rel['label']} of {rel['from']}")

        return "\n".join(context_parts)

    def generate_vector_ingestion_data(self) -> List[Dict[str, Any]]:
        """Generate structured data for vector ingestion"""
        vector_documents = []
        processed_resources: Set[str] = set()

        def create_resource_description(resource_id: str) -> Dict[str, Any]:
            parts = resource_id.split('_')
            return {
                'resource_id': resource_id,
                'kind': parts[0],
                'namespace': parts[1],
                'name': '_'.join(parts[2:])
            }

        # Process all relationships
        for rel in self.relationships:
            source = create_resource_description(rel['from'])
            target = create_resource_description(rel['to'])

            # Create relationship document
            relationship_doc = {
                'id': f"rel_{rel['from']}_{rel['to']}",
                'type': 'relationship',
                'content': f"The {source['kind']} resource '{source['name']}' in namespace '{source['namespace']}' "
                f"has a {rel['label']} relationship with "
                f"the {target['kind']} resource '{target['name']}' in namespace '{target['namespace']}'.",
                'metadata': {
                    'relationship_type': rel['label'],
                    'source_resource': source,
                    'target_resource': target,
                    'source_uri': rel['from_uri'],
                    'target_uri': rel['to_uri'],
                    'timestamp': datetime.now().isoformat()
                }
            }
            vector_documents.append(relationship_doc)

            # Process source resource
            if rel['from'] not in processed_resources:
                source_doc = {
                    'id': rel['from'],
                    'type': 'resource',
                    'content': self.generate_resource_context_enhanced(rel['from']),
                    'metadata': {
                        'resource_type': source['kind'],
                        'namespace': source['namespace'],
                        'name': source['name'],
                        'uri': rel['from_uri'],
                        'timestamp': datetime.now().isoformat()
                    }
                }
                vector_documents.append(source_doc)
                processed_resources.add(rel['from'])

            # Process target resource
            if rel['to'] not in processed_resources:
                target_doc = {
                    'id': rel['to'],
                    'type': 'resource',
                    'content': self.generate_resource_context_enhanced(rel['to']),
                    'metadata': {
                        'resource_type': target['kind'],
                        'namespace': target['namespace'],
                        'name': target['name'],
                        'uri': rel['to_uri'],
                        'timestamp': datetime.now().isoformat()
                    }
                }
                vector_documents.append(target_doc)
                processed_resources.add(rel['to'])

        return vector_documents

    def add_reference_relationship(self, subject_uri: URIRef, ref_field: str, ref_data: Dict):
        """Add reference relationship to graph"""
        if isinstance(ref_data, dict) and all(k in ref_data for k in ['kind', 'namespace', 'name']):
            obj_uri = self.create_uri(
                ref_data['kind'], ref_data['namespace'], ref_data['name'])
            self.g.add((subject_uri, self.lla[ref_field], obj_uri))

            relationship = {
                'from': str(subject_uri).split('#')[1],
                'to': str(obj_uri).split('#')[1],
                'label': ref_field,
                'from_uri': str(subject_uri),
                'to_uri': str(obj_uri)
            }
            self.relationships.append(relationship)

    def process_spec(self, resource_uri: URIRef, spec_data: Dict, resource: Dict):
        """Process specification data"""
        if not isinstance(spec_data, dict):
            return

        # Process direct references
        for key, value in spec_data.items():
            if key.endswith('Ref'):
                self.add_reference_relationship(resource_uri, key, value)
            elif isinstance(value, dict):
                for nested_key, nested_value in value.items():
                    if nested_key.endswith('Ref'):
                        self.add_reference_relationship(
                            resource_uri,
                            f"{key}_{nested_key}",
                            nested_value
                        )

    def save_vector_ingestion_data(self):
        """Save vector ingestion data as JSON"""
        try:
            vector_data = self.generate_vector_ingestion_data()

            output_file = os.path.join(
                self.output_dir, "vector_ingestion.json")
            with open(output_file, 'w') as f:
                json.dump({
                    'metadata': {
                        'generated_at': datetime.now().isoformat(),
                        'total_documents': len(vector_data),
                        'document_types': list(set(doc['type'] for doc in vector_data)),
                        'version': '1.0'
                    },
                    'documents': vector_data
                }, f, indent=2)

            logger.info(
                f"Successfully saved vector ingestion data to {output_file}")
        except Exception as e:
            logger.error(f"Error saving vector ingestion data: {str(e)}")
            raise

    def generate_ontology_and_vectors(self):
        """Generate ontology and vector ingestion data"""
        try:
            json_files = [f for f in os.listdir(
                self.input_dir) if f.endswith('.json')]

            for filename in json_files:
                logger.info(f"Processing file: {filename}")
                data = self.load_json_file(filename)
                for resource in data:
                    if all(k in resource for k in ['kind', 'namespace', 'name']):
                        resource_uri = self.create_uri(
                            resource['kind'],
                            resource['namespace'],
                            resource['name']
                        )
                        self.g.add((resource_uri, RDF.type,
                                   self.lla[resource['kind']]))

                        if 'spec' in resource:
                            self.process_spec(
                                resource_uri, resource['spec'], resource)

            # Save ontology
            ontology_file = os.path.join(self.output_dir, "ontology.ttl")
            self.g.serialize(destination=ontology_file, format="turtle")
            logger.info(f"Successfully saved ontology to {ontology_file}")

            # Save vector ingestion data
            self.save_vector_ingestion_data()

            return self.relationships

        except Exception as e:
            logger.error(f"Error generating ontology and vectors: {str(e)}")
            raise

    def generate_html_visualization(self):
        """Generate HTML visualization of relationships"""
        try:
            G = nx.DiGraph()

            # Add nodes and edges
            for rel in self.relationships:
                G.add_edge(rel['from'], rel['to'], label=rel['label'])

            # Create visualization
            plt.figure(figsize=(20, 15))
            pos = nx.spring_layout(G, k=2, iterations=50)

            # Draw nodes
            nx.draw_networkx_nodes(G, pos, node_color='lightblue',
                                   node_size=3000, alpha=0.7)
            nx.draw_networkx_labels(G, pos, font_size=8)

            # Draw edges
            nx.draw_networkx_edges(G, pos, edge_color='gray',
                                   arrows=True, arrowsize=20)

            # Draw edge labels
            edge_labels = nx.get_edge_attributes(G, 'label')
            nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=6)

            # Save to buffer
            buf = BytesIO()
            plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
            plt.close()

            # Convert to base64
            img_str = base64.b64encode(buf.getvalue()).decode()

            # Generate and save HTML
            html_content = self.generate_html_content(img_str)
            html_file = os.path.join(self.output_dir, "relationships.html")
            with open(html_file, 'w') as f:
                f.write(html_content)

            logger.info(f"Successfully generated visualization: {html_file}")

        except Exception as e:
            logger.error(f"Error generating visualization: {str(e)}")
            raise

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
                .timestamp {{
                    text-align: right;
                    color: #666;
                    font-size: 0.9em;
                    margin-top: 20px;
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

                <div class="timestamp">
                    Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </div>
            </div>
        </body>
        </html>
        """


def main():
    processor = NetworkDataProcessor()

    try:
        logger.info("Starting network data processing...")

        logger.info("Setting up directories...")
        processor.setup_directories()

        logger.info("Processing data and generating ontology...")
        processor.generate_ontology_and_vectors()

        logger.info("Generating visualization...")
        processor.generate_html_visualization()

        logger.info(
            "\nSuccessfully generated files in 'data/output' directory:")
        logger.info("- ontology.ttl (RDF ontology file)")
        logger.info("- relationships.html (Interactive visualization)")
        logger.info("- vector_ingestion.json (Vector store ingestion file)")

    except Exception as e:
        logger.error(f"Fatal error occurred: {str(e)}")
        raise


if __name__ == "__main__":
    main()
