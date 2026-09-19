import asyncio
import os
import edge_tts
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

async def test_tts():
    print("Testing edge-tts...")
    text = "Can you explain what polymorphism is in Java, and give me a practical example of dynamic method dispatch?"
    voice = "en-US-ChristopherNeural"  # Professional, calm, natural technical interviewer voice
    communicate = edge_tts.Communicate(text, voice)
    output_path = "scratch/test_question.mp3"
    await communicate.save(output_path)
    file_size = os.path.getsize(output_path)
    print(f"TTS generated: {output_path} ({file_size} bytes)")
    return output_path

def test_stt(audio_file):
    print("Testing Groq Whisper STT...")
    client = Groq()
    technical_prompt = (
        "Python, Java, JavaScript, C++, SQL, API, REST, HTTP, HTTPS, JWT, OAuth, "
        "Docker, Kubernetes, Git, GitHub, MongoDB, PostgreSQL, Redis, React, Node.js, "
        "OOP, DSA, RAG, LLM, machine learning, neural network, polymorphism, "
        "inheritance, encapsulation, abstraction, multithreading, deadlock, normalization."
    )
    with open(audio_file, "rb") as f:
        transcription = client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=f,
            prompt=technical_prompt,
            response_format="json",
            temperature=0.0
        )
    print("STT Transcription result:")
    print(transcription.text)

async def main():
    audio_path = await test_tts()
    test_stt(audio_path)

if __name__ == "__main__":
    asyncio.run(main())
