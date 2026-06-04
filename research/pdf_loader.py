from pypdf import PdfReader
from chunker import chunk_text

reader = PdfReader("research/datasets/gpt2.pdf")

text = ""

for page in reader.pages:
    extracted = page.extract_text()

    if extracted:
        text += extracted

chunks = chunk_text(text)

print("Total Chunks:", len(chunks))

print("\nFirst Chunk:\n")
print(chunks[0])