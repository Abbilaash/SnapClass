import threading
import os
from datetime import datetime
from stt import transcribe_audio
from pdf_reader import PDFTextImageExtractor

class ContentProcessor:
    def __init__(self, output_dir="output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.status_callback = None
        
    def set_status_callback(self, callback):
        """Set callback function for status updates"""
        self.status_callback = callback
        
    def _update_status(self, message, is_content=False):
        """Helper function to send status updates"""
        if self.status_callback:
            self.status_callback({
                'type': 'content' if is_content else 'status',
                'message': message if not is_content else message,
                'content': message if is_content else None
            })
    
    def process_audio(self, audio_path):
        """Process audio file and convert to text"""
        try:
            self._update_status("Starting audio transcription...")

            # Transcribe audio
            result = transcribe_audio(
                audio_path=audio_path,
                output_dir=self.output_dir
            )

            # Save to markdown (already done in stt.py)
            output_path = result["output_path"]

            self._update_status(f"Audio transcription completed and saved to: {output_path}")
            return output_path

        except Exception as e:
            self._update_status(f"Error in audio processing: {str(e)}")
            raise
    
    def process_pdf(self, pdf_path):
        """Process PDF file and extract content"""
        try:
            self._update_status("Starting PDF processing...")
            
            # Initialize PDF extractor
            extractor = PDFTextImageExtractor()
            
            # Process PDF with status updates
            pdf_content = extractor.extract_full_content(
                pdf_path,
                output_dir=self.output_dir,
                status_callback=self._update_status
            )
            
            # Save to markdown
            base_name = os.path.splitext(os.path.basename(pdf_path))[0]
            output_path = os.path.join(self.output_dir, f"{base_name}_content.md")
            
            extractor.save_to_markdown(pdf_content, output_path)
            self._update_status(f"PDF processing completed and saved to: {output_path}")
            return output_path
            
        except Exception as e:
            self._update_status(f"Error in PDF processing: {str(e)}")
            raise

def process_files(audio_path, pdf_path, status_callback=None):
    """
    Process audio and PDF files in parallel using threads
    
    Args:
        audio_path (str): Path to audio file
        pdf_path (str): Path to PDF file
        status_callback (callable): Function to receive status updates
        
    Returns:
        tuple: Paths to the generated markdown files (audio_transcription.md, pdf_content.md)
    """
    processor = ContentProcessor()
    if status_callback:
        processor.set_status_callback(status_callback)
    
    # Create threads for parallel processing
    audio_thread = threading.Thread(
        target=processor.process_audio,
        args=(audio_path,)
    )
    
    pdf_thread = threading.Thread(
        target=processor.process_pdf,
        args=(pdf_path,)
    )
    
    # Start both threads
    audio_thread.start()
    pdf_thread.start()
    
    # Wait for both threads to complete
    audio_thread.join()
    pdf_thread.join()
    
    # Return paths to generated files
    audio_output = os.path.join(
        processor.output_dir,
        f"{os.path.splitext(os.path.basename(audio_path))[0]}_transcription.md"
    )
    pdf_output = os.path.join(
        processor.output_dir,
        f"{os.path.splitext(os.path.basename(pdf_path))[0]}_content.md"
    )
    
    return audio_output, pdf_output

if __name__ == "__main__":
    # Example usage
    audio_file = "sample_audio.mp3"
    pdf_file = "sample.pdf"
    
    def print_status(update):
        print(f"[{update['type']}] {update.get('message', update.get('content', ''))}")
    
    try:
        audio_output, pdf_output = process_files(
            audio_file,
            pdf_file,
            status_callback=print_status
        )
        print(f"\nProcessing complete!")
        print(f"Audio transcription: {audio_output}")
        print(f"PDF content: {pdf_output}")
    except Exception as e:
        print(f"Error: {str(e)}")