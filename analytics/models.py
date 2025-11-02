
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


  
# Pydantic models to define the exact structure we expect from Gemini

class WorkExperience(BaseModel):
    """Schema for a single job entry."""
    title: str = Field(description="Job title, e.g., 'Software Engineer'.")
    company: str = Field(description="Employer name.")
    start_date: str = Field(description="Start date, e.g., '01/2020'.")
    end_date: str = Field(description="End date, or 'Present'.")
    summary: str = Field(description="2-3 key accomplishments/responsibilities.")

class Education(BaseModel):
    """Schema for an education entry."""
    institution: str
    degree: str
    field_of_study: str
    graduation_date: str

class ResumeAnalysisSchema(BaseModel):
    """The main schema matching the fields we want to populate in ResumeInfo."""
    
    # Simple Fields
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=150)
    linkedin: Optional[str] = Field(None, max_length=255)
    position_inferred: str = Field(description="The primary job role or career target inferred from the resume.")
    education_level: str = Field(description="Highest education level, e.g., 'Master', 'BSc in Computer Science'.")
    
    # JSON Fields (Will map to ResumeInfo's JSON columns)
    skills: List[str] = Field(description="A list of 10-15 most important technical and soft skills.")
    core_values: List[str] = Field(description="A list of 3-5 core professional values/traits inferred from the text.")
    work_history: List[WorkExperience] = Field(description="Detailed list of work experiences.")
    
    # Nested field for structured data (maps to structured_json)
    full_education: List[Education] = Field(description="All formal education entries.")
    
    # The overall JSON that will be stored in 'structured_json'
    structured_json: Dict[str, Any] = Field(description="The full dictionary of all extracted data for structured storage.")

# The final model that includes the necessary nested structure for the API call
class FinalResumeOutput(BaseModel):
    resume_data: ResumeAnalysisSchema
