"""
SmartInterview — Syllabus Engine (Adaptive Topic Selection)
Adapted from friend's syllabus engine, upgraded with adaptive topic selection
based on syllabus coverage constraints and candidate performance.

Role in Architecture:
- Syllabus Engine answers: "What should I ask about next?"
- Shared Adaptive Engine answers: "How difficult/cognitively demanding should it be?"
"""

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class SyllabusState:
    """
    Manages syllabus topics, coverage, per-topic performance,
    and adaptive topic selection.
    """
    selected_topics: list[str]
    current_topic: str = ""
    topic_coverage: dict[str, int] = field(default_factory=dict)
    topic_scores: dict[str, list[float]] = field(default_factory=dict)
    questions_answered_total: int = 0
    previous_questions: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.topic_coverage:
            self.topic_coverage = {t: 0 for t in self.selected_topics}
        if not self.topic_scores:
            self.topic_scores = {t: [] for t in self.selected_topics}
        if not self.current_topic and self.selected_topics:
            self.current_topic = self.selected_topics[0]

    def record_score(self, topic: str, score: float):
        """Record an evaluated score for a topic and increment coverage."""
        if topic not in self.topic_scores:
            self.topic_scores[topic] = []
        if topic not in self.topic_coverage:
            self.topic_coverage[topic] = 0

        self.topic_scores[topic].append(max(0.0, min(100.0, score)))
        self.topic_coverage[topic] += 1
        self.questions_answered_total += 1

    def select_next_topic(self) -> str:
        """
        Adaptive Topic Selection with Syllabus Coverage Constraints:
        1. Breadth first: Choose topics that haven't been asked yet (coverage == 0).
        2. Weakness reinforcement: Choose topics where average score < 60%.
        3. Balance depth: Choose the topic with the fewest questions asked so far.
        """
        if not self.selected_topics:
            return ""

        # 1. Uncovered topics first (breadth across the syllabus)
        uncovered = [t for t in self.selected_topics if self.topic_coverage.get(t, 0) == 0]
        if uncovered:
            self.current_topic = uncovered[0]
            return self.current_topic

        # 2. Weak topics (average score < 60%) that need reinforcement
        weak_topics = []
        for t in self.selected_topics:
            scores = self.topic_scores.get(t, [])
            if scores:
                avg = sum(scores) / len(scores)
                if avg < 60.0:
                    weak_topics.append((avg, self.topic_coverage.get(t, 0), t))

        if weak_topics:
            # Sort by lowest average score, then least coverage
            weak_topics.sort()
            self.current_topic = weak_topics[0][2]
            return self.current_topic

        # 3. Balanced depth: choose topic with least questions asked
        sorted_by_coverage = sorted(self.selected_topics, key=lambda t: self.topic_coverage.get(t, 0))
        self.current_topic = sorted_by_coverage[0]
        return self.current_topic

    def serialize(self) -> dict:
        return asdict(self)

    @classmethod
    def deserialize(cls, data: dict) -> "SyllabusState":
        return cls(**data)


def initialize_syllabus_state(selected_topics: list[str]) -> SyllabusState:
    """Initialize state for a new Syllabus Mode interview."""
    state = SyllabusState(selected_topics=selected_topics)
    if selected_topics:
        state.current_topic = selected_topics[0]
    return state


def calculate_syllabus_summary(state: SyllabusState) -> dict:
    """Calculate final performance summary and recommendations for Syllabus Mode."""
    topic_results = {}
    total_score = 0.0
    total_attempts = 0

    for topic in state.selected_topics:
        scores = state.topic_scores.get(topic, [])
        attempts = len(scores)
        if attempts > 0:
            avg = sum(scores) / attempts
            topic_results[topic] = {
                "attempts": attempts,
                "average_score": round(avg, 1),
                "scores": scores,
                "status": "Proficient" if avg >= 75 else ("Developing" if avg >= 50 else "Needs Review")
            }
            total_score += sum(scores)
            total_attempts += attempts
        else:
            topic_results[topic] = {
                "attempts": 0,
                "average_score": 0.0,
                "scores": [],
                "status": "Not Attempted"
            }

    overall_avg = round(total_score / total_attempts, 1) if total_attempts > 0 else 0.0

    recommendations = []
    for topic, res in topic_results.items():
        avg = res["average_score"]
        attempts = res["attempts"]
        if attempts == 0:
            recommendations.append({
                "skill": topic,
                "priority": "medium",
                "message": f"Topic '{topic}' was not covered during this session. Review recommended."
            })
        elif avg < 50:
            recommendations.append({
                "skill": topic,
                "priority": "high",
                "message": f"Review fundamental concepts in '{topic}' (average score: {avg:.0f}%)."
            })
        elif avg < 75:
            recommendations.append({
                "skill": topic,
                "priority": "medium",
                "message": f"Practice applied problem solving for '{topic}' (average score: {avg:.0f}%)."
            })

    return {
        "overall_average": overall_avg,
        "total_questions": total_attempts,
        "topic_results": topic_results,
        "recommendations": recommendations,
    }
