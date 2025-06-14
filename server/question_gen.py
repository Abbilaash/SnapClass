from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from pathlib import Path
import re

class EducationalQuestionGenerator:
    def __init__(self):
        # Load Phi-3 model (optimized for educational content)
        self.model_name = "microsoft/phi-3-mini-4k-instruct"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            device_map="auto",
            torch_dtype="auto",
            trust_remote_code=True
        )
        
    def read_markdown(self, file_path):
        """Read and clean markdown content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # Remove markdown formatting
            content = re.sub(r'#+\s*', '', content)  # Headers
            content = re.sub(r'\[.*?\]\(.*?\)', '', content)  # Links
            content = re.sub(r'\*{1,2}(.*?)\*{1,2}', r'\1', content)  # Bold/italic
            return content.strip()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return ""

    def generate_comparison_questions(self, audio_path, pdf_path):
        """Generate 5 focused questions comparing audio and PDF content"""
        audio_content = self.read_markdown(audio_path)
        pdf_content = self.read_markdown(pdf_path)
        
        if not audio_content or not pdf_content:
            return []
        
        # Create comparison prompt
        prompt = f"""You are an expert educator analyzing two versions of course material:
        
        AUDIO ANALYSIS (Key Points):
        {audio_content[:3000]}... [truncated]
        
        PDF ANALYSIS (Key Points):
        {pdf_content[:3000]}... [truncated]
        
        Generate exactly 5 focused questions that:
        1. Compare specific concepts between both sources
        2. Highlight any contradictions
        3. Probe deeper into topics mentioned in the AUDIO analysis
        4. Require analytical answers (no yes/no)
        5. Are suitable for classroom discussion
        
        Format each question with a number and newline:
        1. First question...
        2. Second question...
        3. Third question...
        4. Fourth question...
        5. Fifth question..."""
        
        # Generate questions
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=500,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
            pad_token_id=self.tokenizer.eos_token_id
        )
        
        # Extract and clean questions
        full_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        questions = self._extract_questions(full_response)
        
        return questions[:5]  # Return exactly 5 questions
    
    def _extract_questions(self, text):
        """Extract numbered questions from model output"""
        question_pattern = r'\d+\.\s(.*?)(?=\n\d+\.|\n*$)'
        questions = re.findall(question_pattern, text, re.DOTALL)
        return [q.strip() for q in questions if q.strip()]

# Example Usage
if __name__ == "__main__":
    generator = EducationalQuestionGenerator()
    
    # Paths to your analysis files
    audio_file = "uploads/audio_analysis.md"
    pdf_file = "uploads/pdf_analysis.md"
    
    # Generate and display questions
    questions = generator.generate_comparison_questions(audio_file, pdf_file)
    
    print("\nGenerated Questions (Audio vs PDF Comparison):")
    for i, question in enumerate(questions, 1):
        print(f"\n{i}. {question}")
    
    # Save to file
    with open("generated_questions.txt", "w") as f:
        f.write("Questions Comparing Audio and PDF Content:\n")
        for i, question in enumerate(questions, 1):
            f.write(f"\n{i}. {question}")
    print("\nQuestions saved to 'generated_questions.txt'")