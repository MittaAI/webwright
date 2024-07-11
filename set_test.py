from lib.set_store import SetStore

# Create an instance of SetStore
store = SetStore()

# Create two sets of animals
animals1 = ['dog', 'cat', 'elephant', 'lion', 'tiger']
animals2 = ['dog', 'cat', 'rabbit', 'squirrel', 'monkey']

# Add the animal sets to the store
store.add('animals1', animals1)
store.add('animals2', animals2)

# Compute the Tanimoto coefficient between the animal sets
tanimoto_coefficient = store.tanimoto('animals1', 'animals2')

# Print the animal sets and the Tanimoto coefficient
print("Animals Set 1:", store.get('animals1'))
print("Animals Set 2:", store.get('animals2'))
print("Tanimoto Coefficient:", tanimoto_coefficient)

from lib.vector_store import VectorStore

# Create an instance of the VectorStore
vector_store = VectorStore()

# Example sentences about animals
sentences = [
    "The quick brown fox jumps over the lazy dog.",
    "Cats are known for their agility and curiosity.",
    "Elephants are the largest land mammals on Earth.",
    "Lions are apex predators and live in pride.",
    "Tigers are solitary cats and excellent swimmers.",
    "Rabbits are small mammals with fluffy fur.",
    "Squirrels are known for their bushy tails and love for nuts.",
    "Monkeys are intelligent primates that live in social groups."
]

# Add the sentences to the vector store
nodes = [
    {"id": str(i), "text": sentence}
    for i, sentence in enumerate(sentences)
]
vector_store.add(nodes)

# Perform a search
query_text = "Cats are curious animals."
query_embedding = vector_store.vectorize(query_text)
top_k = 3
search_results = vector_store.query(query_embedding, top_k)

# Print the search results
print(f"Search query: {query_text}")
print(f"Top {top_k} similar sentences:")
for i, node_id in enumerate(search_results, start=1):
    text = vector_store.node_dict[node_id]["text"]
    print(f"{i}. {text}")