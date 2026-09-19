import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(PROJECT_ROOT))

from app.services.syllabus_rag_service import extract_text_from_file, chunk_text, infer_subject_and_topics

pdf_path = Path(__file__).resolve().parent / "cs450_distributed_systems_syllabus.pdf"
text = extract_text_from_file(str(pdf_path))
chunks = chunk_text(text)
print(f"Extracted length: {len(text)}, Chunks: {len(chunks)}")
for i, c in enumerate(chunks):
    print(f"Chunk {i}: {c[:100]}...")

from app.services.question_service import get_groq_client, get_groq_model_name

client = get_groq_client()
model = get_groq_model_name()

sample_count = min(15, len(chunks))
step = max(1, len(chunks) // sample_count)
sampled_chunks = [chunks[i][:300] for i in range(0, len(chunks), step)][:sample_count]
excerpts_text = "\n---\n".join(sampled_chunks)

system_prompt = (
    "You are a strict curriculum analyst. You analyze academic syllabi and technical course documents. "
    "Identify the subject discipline and the key topics explicitly covered in the excerpts. "
    "Do NOT invent topics that do not appear in the text. "
    "Output your answer in the exact format:\n"
    "SUBJECT: <1-4 words subject title>\n"
    "TOPICS:\n"
    "- <Topic 1>\n"
    "- <Topic 2>\n"
    "Return between 4 and 14 concise topics (2-5 words each)."
)

user_prompt = f"Filename hint: cs450_distributed_systems_syllabus.pdf\n\nDocument Excerpts:\n{excerpts_text}"

response = client.chat.completions.create(
    model=model,
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ],
    temperature=0.0,
    max_tokens=1500,
)

print("RAW GROQ RESPONSE:")
print(f"Content: '{response.choices[0].message.content}'")
print(f"Finish Reason: '{response.choices[0].finish_reason}'")
print(f"Message: {response.choices[0].message}")
