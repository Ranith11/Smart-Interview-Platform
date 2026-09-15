import json
from dataclasses import dataclass, field, asdict
from typing import Optional

@dataclass
class SyllabusState:
    """
    Deterministic progression state for Syllabus Mode.
    Stored as JSON in interview_sessions.syllabus_state.
    """
    selected_topics: list[str]
    questions_per_topic: int
    difficulty: str
    current_topic_index: int = 0
    questions_answered_in_topic: int = 0
    questions_answered_total: int = 0
    previous_questions: list[str] = field(default_factory=list)
    topic_scores: dict[str, list[float]] = field(default_factory=dict)
    
    @property
    def current_topic(self) -> str:
        if self.current_topic_index < len(self.selected_topics):
            return self.selected_topics[self.current_topic_index]
        return ""
        
    @property
    def is_complete(self) -> bool:
        return self.current_topic_index >= len(self.selected_topics)
        
    def record_score(self, topic: str, score: float):
        if topic not in self.topic_scores:
            self.topic_scores[topic] = []
        self.topic_scores[topic].append(max(0.0, min(100.0, score)))
        
    def advance(self):
        """Advance the deterministic progression after an answer."""
        self.questions_answered_total += 1
        self.questions_answered_in_topic += 1
        
        if self.questions_answered_in_topic >= self.questions_per_topic:
            self.current_topic_index += 1
            self.questions_answered_in_topic = 0
            
    def serialize(self) -> dict:
        return asdict(self)
        
    @classmethod
    def deserialize(cls, data: dict) -> 'SyllabusState':
        return cls(**data)


def initialize_syllabus_state(selected_topics: list[str], questions_per_topic: int, difficulty: str) -> SyllabusState:
    """Initialize state for a new Syllabus Mode interview."""
    difficulty = difficulty if difficulty in ["easy", "medium", "hard"] else "medium"
    return SyllabusState(
        selected_topics=selected_topics,
        questions_per_topic=questions_per_topic,
        difficulty=difficulty,
    )

def calculate_syllabus_summary(state: SyllabusState) -> dict:
    """Calculate final summary for Syllabus Mode."""
    skill_results = {}
    total_score = 0.0
    total_attempts = 0
    
    for topic in state.selected_topics:
        scores = state.topic_scores.get(topic, [])
        attempts = len(scores)
        if attempts > 0:
            avg = sum(scores) / attempts
            skill_results[topic] = {
                "attempts": attempts,
                "average_score": round(avg, 1),
                "scores": scores,
                "final_bloom_level": "N/A",
                "final_bloom_name": "Syllabus Topic",
                "final_bloom_order": 1,
                "final_difficulty": state.difficulty
            }
            total_score += sum(scores)
            total_attempts += attempts
            
    overall_avg = round(total_score / total_attempts, 1) if total_attempts > 0 else 0.0
    
    # Generate simple recommendations for syllabus topics
    recommendations = []
    for topic, result in skill_results.items():
        avg = result["average_score"]
        if avg < 50:
            recommendations.append({
                "skill": topic,
                "priority": "high",
                "message": f"Review {topic} extensively (average: {avg:.0f}%)."
            })
        elif avg < 75:
            recommendations.append({
                "skill": topic,
                "priority": "medium",
                "message": f"Practice more problems for {topic} (average: {avg:.0f}%)."
            })
            
    return {
        "overall_average_score": overall_avg,
        "total_questions_answered": total_attempts,
        "skill_results": skill_results,
        "recommendations": recommendations,
    }
