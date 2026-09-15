import sys
import os

# Add project root and scripts
sys.path.insert(0, os.path.abspath("scripts"))
from generate_question import match_skills_in_text

def test_matching():
    # 1. Go matches "Go" and "Golang" but NOT "Google" or "Good"
    res1 = match_skills_in_text("We use Go and Golang for microservices.")
    assert "Go" in res1, f"Expected 'Go' in {res1}"
    assert res1.count("Go") == 1, f"Expected 'Go' deduplicated, got {res1}"

    res2 = match_skills_in_text("Google is a Good company.")
    assert "Go" not in res2, f"Expected 'Go' NOT in {res2}"

    # 2. PostgreSQL vs SQL
    res3 = match_skills_in_text("We use PostgreSQL database and SQL queries.")
    assert "PostgreSQL" in res3, f"Expected 'PostgreSQL' in {res3}"
    assert "SQL" in res3, f"Expected 'SQL' in {res3}"

    res4 = match_skills_in_text("Refactored legacy PostgreSQL database schemas.")
    assert "PostgreSQL" in res4, f"Expected 'PostgreSQL' in {res4}"
    assert "SQL" not in res4, f"Expected 'SQL' NOT in {res4} because it was part of PostgreSQL"

    # 3. Distributed Tracing vs Tracing
    res5 = match_skills_in_text("Instrumented end-to-end OpenTelemetry distributed tracing.")
    assert "Distributed Tracing" in res5, f"Expected 'Distributed Tracing' in {res5}"
    assert "OpenTelemetry" in res5, f"Expected 'OpenTelemetry' in {res5}"

    # 4. Symbols: C++, C#, Node.js
    res6 = match_skills_in_text("Proficient in C++, C#, and Node.js backend development.")
    assert "C++" in res6, f"Expected 'C++' in {res6}"
    assert "C#" in res6, f"Expected 'C#' in {res6}"
    assert "Node.js" in res6, f"Expected 'Node.js' in {res6}"

    # 5. Aliases normalization: Golang -> Go, k8s -> Kubernetes, Postgres -> PostgreSQL
    res7 = match_skills_in_text("Deployed on k8s with Postgres and Golang.")
    assert "Kubernetes" in res7, f"Expected 'Kubernetes' in {res7}"
    assert "PostgreSQL" in res7, f"Expected 'PostgreSQL' in {res7}"
    assert "Go" in res7, f"Expected 'Go' in {res7}"

    # 6. Advanced modern AI & Infra skills
    res8 = match_skills_in_text("Experience with pgvector, Pinecone, Qdrant, vLLM, LangChain, LlamaIndex, RAG, Terraform, Helm, Prometheus, Datadog, gRPC, Kafka, RabbitMQ.")
    expected = ["pgvector", "Pinecone", "Qdrant", "vLLM", "LangChain", "LlamaIndex", "RAG", "Terraform", "Helm", "Prometheus", "Datadog", "gRPC", "Kafka", "RabbitMQ"]
    for exp in expected:
        assert exp in res8, f"Expected '{exp}' in {res8}"

    print("ALL 6 MATCHING REGRESSION TESTS PASSED PERFECTLY!")

if __name__ == "__main__":
    test_matching()
