import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

class EducationalAnalyzer:
    def __init__(self):
        # Lightweight model (22MB) that works offline after first download
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.knowledge_base = {}  # Stores all learning materials
        self.concept_threshold = 0.7  # Minimum similarity to consider concepts matched
        
    def preprocess(self, text):
        """Basic text normalization"""
        return ' '.join(text.lower().split())
    
    def build_knowledge_base(self, lecture_text, textbook_text):
        """Create unified knowledge representation"""
        # Segment and embed both sources
        lecture_segments = self._segment_text(lecture_text)
        textbook_segments = self._segment_text(textbook_text)
        
        # Create combined knowledge base
        self.knowledge_base = {
            'lecture': {
                'segments': lecture_segments,
                'embeddings': self.model.encode(lecture_segments)
            },
            'textbook': {
                'segments': textbook_segments,
                'embeddings': self.model.encode(textbook_segments)
            },
            'combined_embeddings': None
        }
        
        # Create combined embeddings for comprehensive search
        all_segments = lecture_segments + textbook_segments
        self.knowledge_base['combined_embeddings'] = self.model.encode(all_segments)
        self.knowledge_base['all_segments'] = all_segments
    
    def _segment_text(self, text, sentences_per_segment=2):
        """Split text into meaningful chunks"""
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        segments = []
        for i in range(0, len(sentences), sentences_per_segment):
            segment = '. '.join(sentences[i:i+sentences_per_segment]) + '.'
            segments.append(segment)
        return segments
    
    def analyze_question(self, question_text):
        """Understand what the question is asking"""
        question_embedding = self.model.encode(self.preprocess(question_text))
        
        # Find most relevant concepts from knowledge base
        similarities = cosine_similarity(
            [question_embedding],
            self.knowledge_base['combined_embeddings']
        )[0]
        
        top_indices = np.argsort(similarities)[-3:][::-1]  # Top 3 matches
        relevant_concepts = []
        
        for idx in top_indices:
            if similarities[idx] > self.concept_threshold:
                relevant_concepts.append({
                    'content': self.knowledge_base['all_segments'][idx],
                    'source': 'lecture' if idx < len(self.knowledge_base['lecture']['segments']) else 'textbook',
                    'similarity': float(similarities[idx])
                })
        
        return {
            'original_question': question_text,
            'relevant_concepts': relevant_concepts,
            'main_topic': relevant_concepts[0]['content'] if relevant_concepts else None
        }
    
    def evaluate_answers(self, question_analysis, student_answers):
        """Assess student answers against question requirements"""
        results = []
        expected_concepts = [c['content'] for c in question_analysis['relevant_concepts']]
        expected_embeddings = self.model.encode(expected_concepts)
        
        for answer in student_answers:
            answer_embedding = self.model.encode(self.preprocess(answer))
            
            # Compare with expected concepts
            concept_similarities = cosine_similarity(
                [answer_embedding], 
                expected_embeddings
            )[0]
            
            # Compare with full knowledge base
            knowledge_similarities = cosine_similarity(
                [answer_embedding],
                self.knowledge_base['combined_embeddings']
            )
            best_knowledge_match = np.argmax(knowledge_similarities)
            knowledge_score = knowledge_similarities[0][best_knowledge_match]
            
            # Calculate coverage of expected concepts
            covered_concepts = []
            for i, sim in enumerate(concept_similarities):
                if sim > self.concept_threshold:
                    covered_concepts.append({
                        'concept': expected_concepts[i],
                        'similarity': float(sim)
                    })
            
            results.append({
                'answer': answer,
                'covered_concepts': covered_concepts,
                'coverage_score': len(covered_concepts) / len(expected_concepts) if expected_concepts else 0,
                'knowledge_alignment': {
                    'best_match': self.knowledge_base['all_segments'][best_knowledge_match],
                    'score': float(knowledge_score)
                },
                'needs_review': len(covered_concepts) < len(expected_concepts) / 2  # If <50% covered
            })
        
        return results
    
    def generate_insights(self, question_analysis, answer_evaluations):
        """Generate teacher dashboard data"""
        concept_performance = {}
        
        # Initialize concept tracking
        for concept in question_analysis['relevant_concepts']:
            concept_text = concept['content']
            concept_performance[concept_text] = {
                'times_covered': 0,
                'times_missed': 0,
                'avg_similarity': 0
            }
        
        # Aggregate answer data
        for evaluation in answer_evaluations:
            for covered in evaluation['covered_concepts']:
                concept_text = covered['concept']
                concept_performance[concept_text]['times_covered'] += 1
                concept_performance[concept_text]['avg_similarity'] += covered['similarity']
            
            all_expected = [c['content'] for c in question_analysis['relevant_concepts']]
            for expected in all_expected:
                if expected not in [c['concept'] for c in evaluation['covered_concepts']]:
                    concept_performance[expected]['times_missed'] += 1
        
        # Calculate final metrics
        insights = {
            'question': question_analysis['original_question'],
            'main_topic': question_analysis['main_topic'],
            'concept_performance': [],
            'class_coverage': 0,
            'problem_areas': []
        }
        
        total_answers = len(answer_evaluations)
        for concept, stats in concept_performance.items():
            coverage = stats['times_covered'] / total_answers
            avg_sim = stats['avg_similarity'] / stats['times_covered'] if stats['times_covered'] > 0 else 0
            
            insights['concept_performance'].append({
                'concept': concept,
                'coverage_percentage': coverage * 100,
                'average_similarity': avg_sim
            })
            
            if coverage < 0.5:  # Less than 50% coverage
                insights['problem_areas'].append(concept)
        
        insights['class_coverage'] = sum(
            ev['coverage_score'] for ev in answer_evaluations
        ) / total_answers * 100 if total_answers > 0 else 0
        
        return insights

# Example Usage
analyzer = EducationalAnalyzer()

# 1. Build knowledge base (from lecture audio and textbook PDF)
lecture_content = """
Photosynthesis converts light energy to chemical energy. 
This process occurs in chloroplasts containing chlorophyll. 
The light-dependent reactions produce ATP and NADPH.
"""

textbook_content = """
Plants synthesize glucose through photosynthesis using sunlight. 
Chloroplast organelles contain chlorophyll pigments. 
The first stage (light reactions) generates energy carriers ATP and NADPH.
"""

analyzer.build_knowledge_base(lecture_content, textbook_content)

# 2. Analyze a question
question = "How do plants convert sunlight into usable energy?"
question_analysis = analyzer.analyze_question(question)

print("Question Analysis:")
print(f"Main Topic: {question_analysis['main_topic']}")
print("Relevant Concepts:")
for concept in question_analysis['relevant_concepts']:
    print(f"- {concept['content'][:50]}... (Similarity: {concept['similarity']:.2f})")

# 3. Evaluate student answers
student_answers = [
    "Plants use photosynthesis in chloroplasts to make energy from light",
    "Chlorophyll captures sunlight",
    "Through some process involving leaves"
]

evaluations = analyzer.evaluate_answers(question_analysis, student_answers)

print("\nAnswer Evaluations:")
for eval in evaluations:
    print(f"\nAnswer: {eval['answer']}")
    print(f"Coverage: {eval['coverage_score']:.1%}")
    print(f"Best Knowledge Match: {eval['knowledge_alignment']['best_match'][:50]}...")
    print(f"Needs Review: {'Yes' if eval['needs_review'] else 'No'}")

# 4. Generate teacher insights
insights = analyzer.generate_insights(question_analysis, evaluations)

print("\nClass Insights:")
print(f"Overall Coverage: {insights['class_coverage']:.1f}%\n")

print("🔍 Topic-Wise Performance:")
for cp in insights['concept_performance']:
    print(f"- {cp['concept'][:60]}...")
    print(f"  - Coverage: {cp['coverage_percentage']:.1f}%")
    print(f"  - Avg Similarity: {cp['average_similarity']:.2f}")
    print()

if insights['problem_areas']:
    print("⚠️  Topics Needing Review:")
    for concept in insights['problem_areas']:
        print(f"- {concept[:60]}...")
else:
    print("✅ No significant problem areas detected.")
