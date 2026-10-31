from chunking import chunk_text

sample_text = """
Artificial intelligence is increasingly used in healthcare.
Machine learning models can help clinicians analyze medical data.

Deep learning is particularly useful in medical image analysis.
Convolutional neural networks can identify patterns in radiology images.

Natural language processing can analyze clinical notes.
Large language models can support medical question answering.

Retrieval augmented generation combines document retrieval
with language model generation to provide contextual answers.
""" * 15

chunks = chunk_text(
    sample_text,
    chunk_size=100,
    overlap=20,
)

print("Total words:", len(sample_text.split()))
print("Total chunks:", len(chunks))

for i, chunk in enumerate(chunks, start=1):
    print(f"\nCHUNK {i}")
    print(chunk)