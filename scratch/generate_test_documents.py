"""
Generate test documents for end-to-end interview testing:
1. Alex Chen - Senior Backend Engineer Resume (PDF)
2. Senior Backend Engineer - Job Description (PDF)
3. CS450 - Distributed Systems Course Syllabus (PDF)
"""

from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

OUT_DIR = Path(__file__).resolve().parent

def build_pdf(filename: Path, elements):
    doc = SimpleDocTemplate(
        str(filename),
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40,
    )
    doc.build(elements)
    print(f"Generated: {filename} ({filename.stat().st_size} bytes)")

def create_resume_pdf():
    pdf_path = OUT_DIR / "alex_chen_resume.pdf"
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1e293b')
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748b')
    )
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#4f46e5'),
        spaceBefore=10,
        spaceAfter=4
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#334155')
    )
    bold_body_style = ParagraphStyle(
        'BoldBody',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#1e293b')
    )

    story = [
        Paragraph("Alex Chen", title_style),
        Paragraph("San Francisco, CA | alex.chen@example.com | github.com/alexchen-dev | linkedin.com/in/alexchen", subtitle_style),
        Spacer(1, 6),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cbd5e1'), spaceAfter=8),

        Paragraph("PROFESSIONAL SUMMARY", section_style),
        Paragraph(
            "Senior Backend Engineer with 5+ years of hands-on experience building resilient microservices, high-throughput APIs, "
            "and event-driven data pipelines. Proficient in Python, FastAPI, PostgreSQL, Redis, Docker, Kubernetes, and AWS cloud infrastructure.",
            body_style
        ),
        Spacer(1, 6),

        Paragraph("TECHNICAL SKILLS", section_style),
        Paragraph("<b>Languages & Frameworks:</b> Python, FastAPI, Django, Go, SQL, REST APIs", body_style),
        Paragraph("<b>Databases & Caching:</b> PostgreSQL, Redis, SQLAlchemy, Database Indexing, Query Optimization", body_style),
        Paragraph("<b>Cloud & Infrastructure:</b> Docker, Kubernetes, AWS (EC2, S3, RDS), CI/CD, Git, Linux", body_style),
        Paragraph("<b>Distributed Systems:</b> Microservices, Celery, RabbitMQ, Kafka, Concurrency, Asyncio", body_style),
        Spacer(1, 6),

        Paragraph("WORK EXPERIENCE", section_style),
        Paragraph("<b>Senior Backend Engineer</b> — FinTech Cloud Solutions (2022 – Present)", bold_body_style),
        Paragraph("• Architected and developed scalable RESTful microservices using Python and FastAPI handling 15M+ requests daily.", body_style),
        Paragraph("• Implemented Redis caching layers and token-bucket rate limiting, decreasing 99th-percentile response latency by 42%.", body_style),
        Paragraph("• Engineered complex relational database schemas and optimized indexing in PostgreSQL, reducing query bottlenecks.", body_style),
        Paragraph("• Containerized legacy backend services with Docker and managed deployment pipelines to Kubernetes clusters.", body_style),
        Spacer(1, 4),
        Paragraph("<b>Backend Software Engineer</b> — DataStream Technologies (2019 – 2022)", bold_body_style),
        Paragraph("• Designed asynchronous data ingestion microservices with Python, Celery, and RabbitMQ.", body_style),
        Paragraph("• Built comprehensive automated integration test suites and CI/CD pipelines reducing deployment defects by 25%.", body_style),
        Paragraph("• Collaborated with product and frontend engineering teams to deliver high-performance GraphQL and REST APIs.", body_style),
        Spacer(1, 6),

        Paragraph("PROJECTS", section_style),
        Paragraph("<b>CloudRate (Distributed Rate Limiter)</b>", bold_body_style),
        Paragraph("Open-source distributed rate-limiting middleware written in Python and Redis supporting sliding-window and token-bucket algorithms.", body_style),
        Paragraph("<b>EventMesh (Lightweight Async Message Broker)</b>", bold_body_style),
        Paragraph("High-performance asyncio pub/sub message broker supporting persistent logging and zero-copy JSON streaming.", body_style),
        Spacer(1, 6),

        Paragraph("EDUCATION", section_style),
        Paragraph("<b>Bachelor of Science in Computer Science</b> — University of California, Berkeley (2015 – 2019)", body_style),
    ]
    build_pdf(pdf_path, story)

def create_jd_pdf():
    pdf_path = OUT_DIR / "senior_backend_jd.pdf"
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0f172a')
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#2563eb')
    )
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=10,
        spaceAfter=4
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#334155')
    )

    story = [
        Paragraph("Horizon Scale Systems — Job Opportunity", subtitle_style),
        Paragraph("Senior Backend Engineer (Distributed Systems)", title_style),
        Paragraph("Location: Remote (US) | Department: Core Platform Infrastructure | Level: Senior (L5)", body_style),
        Spacer(1, 6),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cbd5e1'), spaceAfter=8),

        Paragraph("ABOUT THE ROLE", section_style),
        Paragraph(
            "We are seeking a seasoned Senior Backend Engineer to join our Core Platform team. In this role, you will lead the design, "
            "architecture, and scaling of our distributed backend services handling mission-critical transactional workloads. "
            "You will work closely with staff architects to elevate system reliability, database scalability, and API throughput.",
            body_style
        ),
        Spacer(1, 6),

        Paragraph("KEY RESPONSIBILITIES", section_style),
        Paragraph("• Architect and scale mission-critical backend services in Python (FastAPI / Asyncio) and Go.", body_style),
        Paragraph("• Design and optimize PostgreSQL database schemas, indexing strategies, connection pooling, and ACID transaction isolation.", body_style),
        Paragraph("• Build high-performance caching and messaging architectures utilizing Redis and message queues.", body_style),
        Paragraph("• Containerize services using Docker and manage deployments across Kubernetes microservice infrastructure.", body_style),
        Paragraph("• Champion engineering excellence, writing robust unit and integration tests, and conducting rigorous code reviews.", body_style),
        Spacer(1, 6),

        Paragraph("REQUIRED QUALIFICATIONS & SKILLS", section_style),
        Paragraph("• 4+ years of professional software engineering experience focusing on backend distributed systems.", body_style),
        Paragraph("• Deep technical mastery of Python, including FastAPI, asyncio, typing, and standard architectural design patterns.", body_style),
        Paragraph("• Advanced expertise in PostgreSQL, relational database internals, transaction locks, and query performance profiling.", body_style),
        Paragraph("• Hands-on proficiency with Redis for caching, pub/sub, distributed locking, and rate limiting.", body_style),
        Paragraph("• Practical experience with Docker, Kubernetes, CI/CD pipelines, and cloud environments.", body_style),
        Paragraph("• Strong grasp of software design principles: SOLID, microservice boundaries, distributed transactions, and REST APIs.", body_style),
        Spacer(1, 6),

        Paragraph("NICE-TO-HAVE SKILLS", section_style),
        Paragraph("• Experience with Apache Kafka, Celery, or distributed consensus algorithms (Raft / Paxos).", body_style),
        Paragraph("• Familiarity with observability tools: Prometheus, OpenTelemetry, Grafana.", body_style),
    ]
    build_pdf(pdf_path, story)

def create_syllabus_pdf():
    pdf_path = OUT_DIR / "cs450_distributed_systems_syllabus.pdf"
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1e1b4b')
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#4338ca')
    )
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11.5,
        leading=15,
        textColor=colors.HexColor('#1e1b4b'),
        spaceBefore=8,
        spaceAfter=3
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155')
    )

    story = [
        Paragraph("DEPARTMENT OF COMPUTER SCIENCE & ENGINEERING", subtitle_style),
        Paragraph("CS450: Distributed Systems & Cloud Architectures", title_style),
        Paragraph("Course Syllabus & Examination Reference Guide · Spring Semester · 4 Credit Units", body_style),
        Spacer(1, 6),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cbd5e1'), spaceAfter=8),

        Paragraph("COURSE DESCRIPTION & OBJECTIVES", section_style),
        Paragraph(
            "CS450 provides rigorous foundational and practical knowledge of distributed computing systems. "
            "Students study concurrency, distributed state machines, failure modes, consensus algorithms, replication, "
            "and scalable data storage across modern cloud networks.",
            body_style
        ),
        Spacer(1, 4),

        Paragraph("UNIT 1: DISTRIBUTED SYSTEM MODELS & INTER-PROCESS COMMUNICATION", section_style),
        Paragraph("• Characterization of distributed systems: heterogeneity, scalability, failure handling, and transparency.", body_style),
        Paragraph("• Network Fallacies: latency, bandwidth, reliability, topology, and transport boundaries.", body_style),
        Paragraph("• Communication abstractions: Sockets, Remote Procedure Calls (RPC), gRPC, and Message-Oriented Middleware.", body_style),
        Paragraph("• Client-server architectures vs peer-to-peer (P2P) systems.", body_style),
        Spacer(1, 4),

        Paragraph("UNIT 2: TIME, LOGICAL CLOCKS & EVENT ORDERING", section_style),
        Paragraph("• Physical clock synchronization: Cristian's algorithm, Berkeley algorithm, Network Time Protocol (NTP).", body_style),
        Paragraph("• Logical time and event ordering: Lamport logical clocks, happens-before relation (->).", body_style),
        Paragraph("• Vector Clocks: tracking causal history, detecting concurrent and conflicting events.", body_style),
        Paragraph("• Total-order multicast and causal message delivery protocols.", body_style),
        Spacer(1, 4),

        Paragraph("UNIT 3: DISTRIBUTED MUTUAL EXCLUSION & CONSENSUS", section_style),
        Paragraph("• Distributed mutual exclusion: Centralized algorithm, Ring-based token passing, Ricart-Agrawala algorithm, Maekawa's voting.", body_style),
        Paragraph("• Leader Election: Bully algorithm, Ring election algorithm.", body_style),
        Paragraph("• Distributed Consensus: The Consensus Problem, FLP Impossibility Result under asynchronous models.", body_style),
        Paragraph("• Practical Consensus Protocols: Paxos protocol (roles, phases 1 & 2) and the Raft consensus algorithm (leader election, log replication, safety invariants).", body_style),
        Spacer(1, 4),

        Paragraph("UNIT 4: FAULT TOLERANCE, REPLICATION & CONSISTENCY", section_style),
        Paragraph("• Failure models: crash-stop, crash-recovery, Byzantine failures, network partitions.", body_style),
        Paragraph("• Atomic Commit Protocols: Two-Phase Commit (2PC) protocol, prepare and commit phases, coordinator recovery.", body_style),
        Paragraph("• CAP Theorem (Consistency, Availability, Partition Tolerance) and PACELC trade-offs.", body_style),
        Paragraph("• Consistency models: Linearizability, Sequential Consistency, Causal Consistency, and Eventual Consistency.", body_style),
        Paragraph("• Replication techniques: Primary-Backup (active/passive), Multi-Leader replication, and Quorum-based consensus (W + R > N).", body_style),
        Spacer(1, 4),

        Paragraph("UNIT 5: DISTRIBUTED STORAGE & CONSISTENT HASHING", section_style),
        Paragraph("• Scalable key-value stores: Dynamo design principles, sloppy quorums, and hinted handoff.", body_style),
        Paragraph("• Consistent Hashing algorithm: hash rings, virtual nodes, load balancing during dynamic node joining and leaving.", body_style),
        Paragraph("• Conflict resolution: Vector clocks, read-repair, and anti-entropy background synchronization with Merkle trees.", body_style),
    ]
    build_pdf(pdf_path, story)

if __name__ == "__main__":
    create_resume_pdf()
    create_jd_pdf()
    create_syllabus_pdf()
    print("All 3 test documents generated successfully!")
