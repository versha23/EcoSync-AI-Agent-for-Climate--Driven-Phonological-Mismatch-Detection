**SET UP INSTRCUTIONS**

pip install qdrant-client
Download qdrant and to check to see if it is running see on deckoer desktop
 <img width="979" height="345" alt="image" src="https://github.com/user-attachments/assets/40b95e42-882d-401c-abd5-933350eda05c" />
 
**Folder Structure Should Look Like**

<img width="269" height="413" alt="image" src="https://github.com/user-attachments/assets/6dbb1bbb-0332-4a6f-8f99-b995777edae6" />

 Install Python Dependencies In VS Code Terminal: Open terminal in VS Code: View → Terminal (or Ctrl + `) Create virtual environment:

Setup & Installation Instructions
C.1 System Requirements

Python 3.10 or higher
Docker Desktop (for Qdrant)
8GB RAM minimum
5GB disk space

C.2 Installation Steps
bash# Step 1: Clone repository (if applicable)
git clone <repository-url>
cd phenology_mismatch_detector

# Create virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

Step 3: Install dependencies
pip install -r requirements.txt

#  Start Qdrant in Docker
docker run -d -p 6333:6333 -p 6334:6334 \
  -v qdrant_storage:/qdrant/storage \
  qdrant/qdrant

#  Verify Qdrant is running
# Open browser: http://localhost:6333
# Should see: {"title":"qdrant - vector search engine"...}
C.3 Data Download & Ingestion
bash# Download species observations and climate data
python scripts/download_species_data.py
python scripts/download_climate_data.py

# Clean and filter data
python scripts/clean_and_filter_data.py

# Ingest into Qdrant
python scripts/ingest_to_qdrant.py

# Verify ingestion
python scripts/verify_data.py
C.4 Running the System
**bash# Interactive AI Agent (main demo)**
python scripts/interactive_cli.py

# Automated presentation
python demo.py

# Test queries
python scripts/test_queries.py
