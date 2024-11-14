from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import uvicorn
from typing import Dict, Any
import os
import asyncio
from mock_generator import MockDataGenerator
from network_processor import NetworkDataProcessor

class NetworkModelingService:
    def __init__(self):
        self.mock_generator = MockDataGenerator()
        self.network_processor = NetworkDataProcessor()
        self.output_dir = Path("../data/output")
        self.relationships_path = self.output_dir / "relationships.html"
        self.ensure_directories()

    def ensure_directories(self):
        """Ensure necessary directories exist"""
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def generate_and_process_data(self) -> Dict[str, Any]:
        """Generate mock data and process it"""
        try:
            # Generate mock data
            self.mock_generator.generate_all_files()

            # Process data and generate visualizations
            relationships = self.network_processor.generate_ontology_and_vectors()
            self.network_processor.generate_html_visualization()

            return {
                "status": "success",
                "message": "Network model generated successfully",
                "files_generated": {
                    "ontology": str(self.output_dir / "ontology.ttl"),
                    "vector_contexts": str(self.output_dir / "vector_contexts.jsonl"),
                    "visualization": str(self.relationships_path)
                },
                "relationship_count": len(relationships)
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def get_visualization(self) -> str:
        """Retrieve the generated visualization HTML"""
        try:
            if not self.relationships_path.exists():
                raise FileNotFoundError("Visualization has not been generated yet")
            
            with open(self.relationships_path, 'r') as f:
                return f.read()
        except Exception as e:
            raise HTTPException(status_code=404, detail=str(e))

# Initialize FastAPI app
app = FastAPI(
    title="Network Modeling Service",
    description="API for generating and visualizing network infrastructure relationships",
    version="1.0.0"
)

# Initialize service
service = NetworkModelingService()

# Mount static files directory
app.mount("/static", StaticFiles(directory="../data/output"), name="static")

@app.post("/generate")
async def generate_network_model():
    """Generate network model and relationships"""
    return await service.generate_and_process_data()

@app.get("/visualization", response_class=HTMLResponse)
async def get_visualization():
    """Get the relationship visualization"""
    return await service.get_visualization()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# CLI interface
def main():
    """Main function to run the API server"""
    uvicorn.run("api_wrapper:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
