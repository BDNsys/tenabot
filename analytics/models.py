from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any


# --- Auxiliary Schemas ---

class WorkExperience(BaseModel):
    """Schema for a single job entry."""
    title: str = Field(description="Job title, e.g., 'Software Engineer'.")
    company: str = Field(description="Employer name.")
    start_date: str = Field(description="Start date, e.g., '01/2020'.")
    end_date: str = Field(description="End date, or 'Present'.")
    summary: str = Field(description="2-3 key accomplishments/responsibilities.")
    
    # Configuration to prevent additionalProperties from being generated for this nested object
    model_config = ConfigDict(extra='forbid')


class Education(BaseModel):
    """Schema for an education entry."""
    institution: str
    degree: str
    field_of_study: str
    graduation_date: str
    
    # Configuration to prevent additionalProperties from being generated for this nested object
    model_config = ConfigDict(extra='forbid')

# --- Core Analysis Schema ---

class ResumeAnalysisSchema(BaseModel):
    """
    The main schema matching the fields we want to populate in ResumeInfo.
    
    NOTE: The 'structured_json' field was removed to eliminate Dict[str, Any].
    The data returned by Gemini will *be* the structured JSON dictionary.
    """
    
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
    
    # Configuration to prevent additionalProperties from being generated
    model_config = ConfigDict(extra='forbid')


# --- Final Output Model ---

class FinalResumeOutput(BaseModel):
    """
    The final model expected by the Python SDK when structured JSON is wrapped.
    This model MUST use 'extra='forbid'' to ensure a clean schema.
    """
    resume_data: ResumeAnalysisSchema = Field(description="The root object containing all parsed resume data.")
    
    # CRITICAL FIX: Ensures the generated schema does not contain 'additionalProperties'.
    model_config = ConfigDict(extra='forbid')