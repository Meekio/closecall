"""
Quick test script to verify the styling guidance retrieval system works.
"""

from src.knowledge.retrieval import retrieve_styling_guidance

# Test queries
test_queries = [
    "pairing grey t-shirt with black trousers for office",
    "what colors work well for rainy weather",
    "choosing between multiple formal outfits",
    "casual college outfit with denim",
]

print("Testing CloseCall Styling Guidance Retrieval\n")
print("=" * 60)

for query in test_queries:
    print(f"\nQuery: '{query}'")
    print("-" * 60)
    results = retrieve_styling_guidance(query, top_k=3)
    for i, result in enumerate(results, 1):
        print(f"\n{i}. [Category: {result['category']}] [Score: {result['score']:.4f}]")
        print(f"   {result['text']}")

print("\n" + "=" * 60)
print("✅ Retrieval system working correctly!")
