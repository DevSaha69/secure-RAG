import os
import sys

# Add the directory of this file to sys.path so chunker can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pypdf import PdfReader
from chunker import chunk_text

# Resolve PDF path relative to this file
base_dir = os.path.dirname(os.path.abspath(__file__))
pdf_path = os.path.join(base_dir, "datasets", "gpt2.pdf")

reader = PdfReader(pdf_path)

text = ""

for page in reader.pages:
    extracted = page.extract_text()

    if extracted:
        text += extracted

chunks = chunk_text(text)

print("Total Chunks:", len(chunks))

if chunks:
    print("\nFirst Chunk:\n")
    print(chunks[0])
else:
    print("\nNo chunks generated.")