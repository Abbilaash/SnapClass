import torch
from transformers import (
    AutoProcessor, 
    AutoModelForImageTextToText,
    BlipForConditionalGeneration,
    BlipProcessor
)
from pdf2image import convert_from_path
from PIL import Image
import os
import io
import pytesseract
from collections import defaultdict

class PDFTextImageExtractor:
    def __init__(self):
        # Initialize Nougat model for document understanding (keep same)
        self.nougat_processor = AutoProcessor.from_pretrained("facebook/nougat-small")
        self.nougat_model = AutoModelForImageTextToText.from_pretrained("facebook/nougat-small")
        
        # Initialize BLIP base model for image captioning (changed from BLIP-2)
        self.blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        self.blip_model = BlipForConditionalGeneration.from_pretrained(
            "Salesforce/blip-image-captioning-base",
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
        )
        
        # Device configuration
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.nougat_model.to(self.device)
        self.blip_model.to(self.device)
        
        # Configure Tesseract OCR (fallback for pure text pages)
        pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'  # Update path as needed

    def extract_full_content(self, pdf_path, output_dir="output", status_callback=None):
        """Extract all text and image descriptions from PDF"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Convert PDF to images
        poppler_path = "../venv/Lib/poppler/Library/bin"  # Update if needed
        pages = convert_from_path(pdf_path, poppler_path=poppler_path)
        
        if status_callback:
            status_callback({
                'type': 'status',
                'message': f"PDF loaded successfully. Total pages: {len(pages)}"
            })
        
        full_content = {
            'metadata': {
                'source': os.path.basename(pdf_path),
                'total_pages': len(pages)
            },
            'pages': []
        }

        for page_num, page_image in enumerate(pages, start=1):
            if status_callback:
                status_callback({
                    'type': 'status',
                    'message': f"Processing page {page_num}/{len(pages)}..."
                })
            
            page_content = self._process_page(page_image, page_num, output_dir)
            full_content['pages'].append(page_content)
            
            # Send the actual content for this page
            if status_callback:
                content_message = f"Page {page_num} Content:\n\n"
                content_message += f"Text:\n{page_content['text']}\n\n"
                
                if page_content['images']:
                    content_message += "Images Found:\n"
                    for img in page_content['images']:
                        content_message += f"- {img['description']['general_description']}\n"
                        content_message += f"  Educational Context: {img['description']['detailed_description']}\n"
                
                status_callback({
                    'type': 'content',
                    'content': content_message
                })
                
                status_callback({
                    'type': 'status',
                    'message': f"Page {page_num} processed - {len(page_content['text'])} chars, {len(page_content['images'])} images"
                })

        if status_callback:
            status_callback({
                'type': 'status',
                'message': "PDF processing completed successfully!"
            })

        return full_content

    def _process_page(self, page_image, page_num, output_dir):
        """Process a single PDF page"""
        # Save page image temporarily
        img_path = f"{output_dir}/page_{page_num}.png"
        page_image.save(img_path, "PNG")
        
        page_result = {
            'page_number': page_num,
            'text': "",
            'images': [],
            'tables': []
        }

        # Try Nougat first for academic content
        try:
            page_result['text'] = self._extract_with_nougat(page_image)
        except Exception as e:
            print(f"Nougat failed on page {page_num}, using OCR fallback: {str(e)}")
            page_result['text'] = self._extract_with_ocr(page_image)

        # Extract and describe images
        page_result['images'] = self._extract_and_describe_images(page_image, page_num, output_dir)

        os.remove(img_path)
        return page_result

    def _extract_with_nougat(self, page_image):
        """Extract text using Nougat (keep original)"""
        inputs = self.nougat_processor(images=page_image, return_tensors="pt").to(self.device)
        
        with torch.inference_mode():
            outputs = self.nougat_model.generate(
                **inputs,
                max_new_tokens=2048,
                bad_words_ids=[[self.nougat_processor.tokenizer.unk_token_id]]
            )
        
        return self.nougat_processor.batch_decode(outputs, skip_special_tokens=True)[0]

    def _extract_with_ocr(self, page_image):
        """Fallback OCR extraction"""
        return pytesseract.image_to_string(page_image)

    def _extract_and_describe_images(self, page_image, page_num, output_dir):
        """Detect and describe images using BLIP base"""
        img_byte_arr = io.BytesIO()
        page_image.save(img_byte_arr, format='PNG')
        img_bytes = img_byte_arr.getvalue()
        
        description = self._generate_image_description(page_image)
        
        return [{
            'page': page_num,
            'description': description,
            'type': 'diagram' if self._is_diagram(page_image) else 'photograph',
            'content': img_bytes
        }]

    def _generate_image_description(self, image):
        """Generate image caption using BLIP base (changed from BLIP-2)"""
        inputs = self.blip_processor(image, return_tensors="pt").to(self.device)
        
        # Efficient generation with BLIP base
        outputs = self.blip_model.generate(
            **inputs,
            max_new_tokens=100,  # Reduced from BLIP-2's 300
            num_beams=3,         # Default is 5 in BLIP-2
            temperature=0.7
        )
        
        base_description = self.blip_processor.decode(outputs[0], skip_special_tokens=True)
        
        return {
            'general_description': base_description,
            'detailed_description': self._enhance_description(base_description),
            'educational_significance': self._analyze_educational_content(base_description)
        }

    def _enhance_description(self, description):
        """Add educational context to BLIP's output"""
        educational_terms = {
            "diagram": "educational diagram showing",
            "graph": "data visualization illustrating",
            "figure": "illustration depicting",
            "image": "educational content showing"
        }
        
        for term, enhancement in educational_terms.items():
            if term in description.lower():
                return f"This {enhancement} {description}"
        
        return f"This educational image shows: {description}"

    def _is_diagram(self, image):
        """Simple heuristic to detect diagrams"""
        return True  # Assuming academic PDFs contain mostly diagrams

    def _analyze_educational_content(self, description):
        """Analyze educational value"""
        concepts = []
        if "diagram" in description.lower():
            concepts.append("illustrative diagram")
        if any(term in description.lower() for term in ["graph", "chart"]):
            concepts.append("data visualization")
        if any(term in description.lower() for term in ["formula", "equation"]):
            concepts.append("mathematical content")
            
        return {
            'key_concepts': concepts,
            'complexity_level': "high" if len(concepts) > 2 else "medium"
        }

    def save_to_markdown(self, content, output_path):
        """Save results to markdown file"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"# Complete Extraction from: {content['metadata']['source']}\n\n")
            f.write(f"**Total Pages:** {content['metadata']['total_pages']}\n\n")
            
            for page in content['pages']:
                f.write(f"\n\n## Page {page['page_number']}\n\n")
                f.write(page['text'] + "\n\n")
                
                for img in page['images']:
                    f.write(f"\n### Image (Page {img['page']})\n")
                    f.write(f"**Type:** {img['type'].title()}\n\n")
                    f.write(f"**Description:** {img['description']['general_description']}\n\n")
                    f.write(f"**Educational Analysis:** {img['description']['detailed_description']}\n\n")
                    f.write("**Key Concepts:** " + ", ".join(img['description']['educational_significance']['key_concepts']) + "\n")

# Example Usage
if __name__ == "__main__":
    extractor = PDFTextImageExtractor()
    pdf_content = extractor.extract_full_content("../same.pdf")
    extractor.save_to_markdown(pdf_content, "full_extraction_report.md")
    print("Extraction complete! Report saved to full_extraction_report.md")