from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

# Connect to Qdrant
client = QdrantClient("localhost", port=6333)

print("🔗 Connecting to Qdrant...")

# Check health
health = client.get_collections()
print(f"✅ Connected! Current collections: {health}")


print("\n📦 Creating test collection...")
client.recreate_collection(
    collection_name="test_collection",
    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
)

print("✅ Test collection created!")


collections = client.get_collections()
print(f"📋 Collections: {collections}")


client.delete_collection("test_collection")
print("🗑️  Test collection deleted!")

print("\n✅ ALL TESTS PASSED! Qdrant is working perfectly!")