"""Resume processing service"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
import json


class ResumeService:
    """Service for processing and extracting resume information"""
    
    def __init__(self):
        self.upload_dir = Path("uploads/resumes")
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    async def process_resume(self, file_path: str, file_type: str) -> Optional[Dict[str, Any]]:
        """
        Process resume and extract information
        
        Args:
            file_path: Path to the resume file
            file_type: Type of file (pdf or docx)
        
        Returns:
            Extracted resume data or None if processing failed
        """
        try:
            if file_type.lower() == "pdf":
                return await self._process_pdf(file_path)
            elif file_type.lower() == "docx":
                return await self._process_docx(file_path)
            else:
                return None
        except Exception as e:
            print(f"Error processing resume: {e}")
            return None
    
    async def _process_pdf(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Extract text from PDF file"""
        try:
            import PyPDF2
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return {"raw_text": text}
        except Exception as e:
            print(f"Error processing PDF: {e}")
            return None
    
    async def _process_docx(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Extract text from DOCX file"""
        try:
            from docx import Document
            doc = Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
            return {"raw_text": text}
        except Exception as e:
            print(f"Error processing DOCX: {e}")
            return None
    
    def extract_sections(self, raw_text: str) -> Dict[str, Any]:
        """
        Extract structured sections from resume text
        
        This is a basic implementation. In production, use AI to parse sections.
        """
        sections = {
            "education": [],
            "experience": [],
            "skills": [],
            "certifications": [],
            "languages": [],
            "projects": []
        }
        
        # Simple keyword-based extraction
        lines = raw_text.split('\n')
        current_section = None
        
        for line in lines:
            line_lower = line.lower().strip()
            
            if 'education' in line_lower:
                current_section = 'education'
            elif 'experience' in line_lower or 'work history' in line_lower:
                current_section = 'experience'
            elif 'skill' in line_lower:
                current_section = 'skills'
            elif 'certification' in line_lower or 'license' in line_lower:
                current_section = 'certifications'
            elif 'language' in line_lower:
                current_section = 'languages'
            elif 'project' in line_lower:
                current_section = 'projects'
            elif current_section and line.strip():
                sections[current_section].append(line.strip())
        
        # Convert lists to JSON strings
        for key in sections:
            sections[key] = json.dumps(sections[key])
        
        return sections


resume_service = ResumeService()
