"""
Create two test syllabus files for E2E verification:
  1. OS_Syllabus.pdf  — Operating Systems content
  2. DBMS_Reference.txt — Database Management Systems content
"""
import os

def make_os_pdf():
    from reportlab.pdfgen import canvas
    os.makedirs("test_syllabi", exist_ok=True)
    c = canvas.Canvas("test_syllabi/OS_Syllabus.pdf")

    sections = [
        ("Processes and Process Management",
         "A process is an instance of a program in execution. Process management involves creation, scheduling, "
         "and termination of processes. Each process has its own memory space, process control block (PCB), "
         "program counter, stack, and heap. Process states include new, ready, running, waiting, and terminated. "
         "The operating system uses a process table to track all active processes. Context switching involves "
         "saving the state of the current process and loading the state of the next process. "
         "Process creation is done via fork() in Unix systems. The parent process spawns child processes. "
         "Process termination happens via exit() or when the program finishes execution normally. "),

        ("Threads and Concurrency",
         "A thread is the smallest unit of execution within a process. Threads share the process address space "
         "but have their own stack and registers. Multithreading allows parallel execution of multiple tasks "
         "within a single process. User-level threads are managed by user libraries. Kernel-level threads are "
         "managed by the operating system. Thread synchronization is critical to avoid race conditions. "
         "Mutex locks and semaphores are common synchronization primitives. A race condition occurs when "
         "the outcome depends on the sequence of uncontrollable events. Thread pools pre-create a set of "
         "worker threads to avoid overhead of repeatedly creating and destroying threads. "),

        ("CPU Scheduling Algorithms",
         "CPU scheduling determines which process runs on the CPU at any given time. First Come First Served "
         "(FCFS) schedules processes in the order they arrive. Shortest Job First (SJF) selects the process "
         "with the smallest CPU burst. Round Robin assigns a fixed time quantum to each process in circular order. "
         "Priority Scheduling assigns priorities to processes and schedules the highest priority first. "
         "Multilevel Queue Scheduling divides processes into separate queues with different priorities. "
         "The goal of scheduling is to maximize CPU utilization, throughput, and minimize turnaround time, "
         "waiting time, and response time. Preemptive scheduling can interrupt a running process while "
         "non-preemptive scheduling lets the process run until it completes or blocks. "),

        ("Deadlocks and Deadlock Prevention",
         "A deadlock is a situation where a group of processes are permanently blocked waiting for resources "
         "held by each other. The four necessary conditions for deadlock are: mutual exclusion, hold and wait, "
         "no preemption, and circular wait. Deadlock prevention eliminates one of these four conditions. "
         "Deadlock avoidance uses algorithms like the Banker's algorithm to ensure the system never enters "
         "an unsafe state. Deadlock detection allows deadlocks to occur but detects them using resource "
         "allocation graphs and then recovers. Deadlock recovery can be done by process termination or "
         "resource preemption. Resource allocation graphs visually represent the relationships between "
         "processes and resources. "),

        ("Memory Management and Virtual Memory",
         "Memory management is responsible for allocating and deallocating memory to processes. Paging divides "
         "physical memory into fixed-size frames and logical memory into pages of the same size. Segmentation "
         "divides memory into variable-length segments based on logical divisions. Virtual memory allows "
         "processes to use more memory than physically available by using disk as an extension. Page faults "
         "occur when a process accesses a page not currently in physical memory. Page replacement algorithms "
         "include FIFO, LRU (Least Recently Used), and Optimal. The Translation Lookaside Buffer (TLB) is "
         "a cache that speeds up virtual-to-physical address translation. Thrashing occurs when the system "
         "spends more time paging than executing. "),

        ("File Systems and I/O Management",
         "A file system provides mechanisms for storing and retrieving data on secondary storage. File "
         "allocation methods include contiguous, linked, and indexed allocation. Directory structures can "
         "be single-level, two-level, tree-structured, or acyclic graph. File permissions define read, "
         "write, and execute access for owner, group, and others. I/O management involves controlling "
         "hardware devices through device drivers. Disk scheduling algorithms include FCFS, SSTF (Shortest "
         "Seek Time First), SCAN, and C-SCAN. Buffering improves I/O performance by temporarily storing "
         "data in memory buffers. Caching stores frequently accessed data in faster storage. "),
    ]

    for title, body in sections:
        c.setFont("Helvetica-Bold", 14)
        y = 750
        c.drawString(50, y, title)
        c.setFont("Helvetica", 10)
        y -= 25
        # wrap body text
        words = body.split()
        line = ""
        for word in words:
            if len(line + " " + word) > 100:
                c.drawString(50, y, line.strip())
                y -= 14
                if y < 80:
                    c.showPage()
                    y = 750
                line = word
            else:
                line += " " + word
        if line.strip():
            c.drawString(50, y, line.strip())
        c.showPage()

    c.save()
    print("Created test_syllabi/OS_Syllabus.pdf")


def make_dbms_txt():
    os.makedirs("test_syllabi", exist_ok=True)
    content = """
DATABASE MANAGEMENT SYSTEMS — REFERENCE MATERIAL

=== Entity-Relationship Model ===
The Entity-Relationship (ER) model is a conceptual data model that represents the logical structure of a database. 
Entities are objects or things in the real world. Attributes describe properties of entities. 
Relationships represent associations between entities. Primary keys uniquely identify each entity instance.
Cardinality defines the numerical relationships between entities: one-to-one, one-to-many, many-to-many.
ER diagrams visually represent the ER model using rectangles for entities, ellipses for attributes, and diamonds for relationships.
Weak entities do not have a primary key of their own and depend on a strong entity.

=== Relational Model ===
The relational model represents data as a collection of tables (relations). 
Each table has rows (tuples) and columns (attributes). A schema describes the structure of a relation.
A relation instance is a specific set of tuples in the relation at a given time.
Domain constraints restrict attribute values to specified data types.
Key constraints ensure that primary keys are unique and non-null.
Referential integrity constraints ensure that foreign key values correspond to existing primary key values.
The relational algebra provides a formal query language with operations like selection, projection, join, union, and difference.

=== Structured Query Language (SQL) ===
SQL is the standard language for relational database management systems.
DDL (Data Definition Language) includes CREATE, ALTER, DROP commands.
DML (Data Manipulation Language) includes SELECT, INSERT, UPDATE, DELETE commands.
The SELECT statement retrieves data from one or more tables.
JOIN operations combine rows from two or more tables based on a related column.
INNER JOIN returns rows with matching values in both tables.
LEFT JOIN returns all rows from the left table and matched rows from the right table.
Aggregate functions include COUNT, SUM, AVG, MIN, MAX.
GROUP BY groups rows by one or more columns. HAVING filters groups.
Subqueries are nested SELECT statements within another SQL statement.

=== Database Normalization ===
Normalization is the process of organizing a database to reduce redundancy and improve data integrity.
First Normal Form (1NF): Eliminate repeating groups; all attributes must be atomic.
Second Normal Form (2NF): Must be in 1NF; all non-key attributes must be fully functionally dependent on the primary key.
Third Normal Form (3NF): Must be in 2NF; no transitive dependencies.
Boyce-Codd Normal Form (BCNF): A stronger version of 3NF.
Fourth Normal Form (4NF): Eliminates multi-valued dependencies.
Denormalization is the process of intentionally introducing redundancy to improve read performance.
Functional dependencies describe the relationship between attributes in a relation.

=== Transactions and Concurrency Control ===
A transaction is a logical unit of work consisting of one or more SQL operations.
ACID properties: Atomicity, Consistency, Isolation, Durability.
Atomicity ensures that a transaction is either fully completed or fully rolled back.
Consistency ensures the database moves from one valid state to another.
Isolation ensures that concurrent transactions do not interfere with each other.
Durability ensures that committed transactions persist even after a system failure.
Concurrency control prevents anomalies like dirty reads, non-repeatable reads, and phantom reads.
Locking mechanisms include shared locks (for read) and exclusive locks (for write).
Two-Phase Locking (2PL) ensures serializability.
Deadlocks in transactions are detected via wait-for graphs and resolved by aborting one transaction.
Timestamp-based concurrency control uses timestamps to order transactions.

=== Indexing and Query Optimization ===
An index is a data structure that improves the speed of data retrieval.
Dense indexes have an entry for every record; sparse indexes have entries for only some records.
B+ trees are the most commonly used index structure in relational databases.
Clustered indexes determine the physical order of data in the table.
Non-clustered indexes store the index separately from the data.
Hashing provides O(1) average access time for equality queries.
Query optimization translates a query into an efficient execution plan.
The query optimizer estimates the cost of different execution plans using statistics.
Join ordering and algorithm selection (nested loop, hash join, merge join) greatly affect query performance.

=== Database Recovery ===
Recovery ensures the database is restored to a consistent state after a failure.
Types of failures: transaction failure, system crash, disk failure.
Write-Ahead Logging (WAL) ensures that log records are written before the actual data changes.
Checkpoints reduce recovery time by periodically saving the current database state to disk.
UNDO operations reverse uncommitted transactions. REDO operations reapply committed transactions.
Shadow paging maintains two copies of the database; on commit the shadow becomes the current copy.
Log-based recovery uses transaction logs to redo or undo operations after a failure.
"""
    with open("test_syllabi/DBMS_Reference.txt", "w") as f:
        f.write(content)
    print("Created test_syllabi/DBMS_Reference.txt")


if __name__ == "__main__":
    make_os_pdf()
    make_dbms_txt()
    print("Both test files ready.")
