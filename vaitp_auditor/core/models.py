"""
Core data models for the VAITP-Auditor system.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional, List


@dataclass
class CodePair:
    """Represents a pair of code snippets for comparison."""
    identifier: str
    expected_code: Optional[str]
    generated_code: str
    source_info: Dict[str, Any]
    input_code: Optional[str] = None  # Original input code

    def __post_init__(self):
        """Validate required fields."""
        if not self.identifier:
            raise ValueError("identifier cannot be empty")
        # Note: generated_code can be empty - it's a valid failure case for review
    
    def validate_integrity(self) -> bool:
        """Perform comprehensive data integrity validation."""
        try:
            # Check identifier format (basic alphanumeric + underscore + dash)
            if not self.identifier.replace('_', '').replace('-', '').replace('.', '').isalnum():
                return False
            
            # Check that source_info is a valid dictionary
            if not isinstance(self.source_info, dict):
                return False
            
            # Check code content is string or None
            if self.expected_code is not None and not isinstance(self.expected_code, str):
                return False
            
            if not isinstance(self.generated_code, str):
                return False
            
            if self.input_code is not None and not isinstance(self.input_code, str):
                return False
                
            return True
        except Exception:
            return False


@dataclass
class ReviewResult:
    """Represents the result of a manual code review."""
    review_id: int
    source_identifier: str
    experiment_name: str
    review_timestamp_utc: datetime
    reviewer_verdict: str
    reviewer_comment: str
    time_to_review_seconds: float
    expected_code: Optional[str]
    generated_code: str
    code_diff: str
    model_name: Optional[str] = None  # AI model used to generate the code
    prompting_strategy: Optional[str] = None  # Prompting strategy used

    def __post_init__(self):
        """Validate required fields and data types."""
        if self.review_id < 0:
            raise ValueError("review_id must be non-negative")
        if not self.source_identifier:
            raise ValueError("source_identifier cannot be empty")
        if not self.experiment_name:
            raise ValueError("experiment_name cannot be empty")
        if not self.reviewer_verdict:
            raise ValueError("reviewer_verdict cannot be empty")
        if self.time_to_review_seconds < 0:
            raise ValueError("time_to_review_seconds must be non-negative")
    
    def validate_verdict(self) -> bool:
        """Validate that the reviewer verdict is one of the expected values."""
        valid_verdicts = {
            'Success', 
            'Failure - No Change', 
            'Invalid Code', 
            'Wrong Vulnerability', 
            'Partial Success',
            'Flag NOT Vulnerable Expected',
            'Custom',
            'Undo',
            'Quit'
        }
        return self.reviewer_verdict in valid_verdicts
    
    def validate_integrity(self) -> bool:
        """Perform comprehensive data integrity validation."""
        try:
            # Check data types
            if not isinstance(self.review_id, int):
                return False
            if not isinstance(self.source_identifier, str):
                return False
            if not isinstance(self.experiment_name, str):
                return False
            if not isinstance(self.review_timestamp_utc, datetime):
                return False
            if not isinstance(self.reviewer_verdict, str):
                return False
            if not isinstance(self.reviewer_comment, str):
                return False
            if not isinstance(self.time_to_review_seconds, (int, float)):
                return False
            if self.expected_code is not None and not isinstance(self.expected_code, str):
                return False
            if not isinstance(self.generated_code, str):
                return False
            if not isinstance(self.code_diff, str):
                return False
            
            # Validate verdict
            if not self.validate_verdict():
                return False
            
            return True
        except Exception:
            return False


@dataclass
class DiffLine:
    """Represents a single line in a code difference."""
    tag: str  # 'equal', 'add', 'remove', 'modify'
    line_content: str
    line_number: Optional[int] = None

    def __post_init__(self):
        """Validate tag values."""
        valid_tags = {'equal', 'add', 'remove', 'modify'}
        if self.tag not in valid_tags:
            raise ValueError(f"tag must be one of {valid_tags}, got '{self.tag}'")


@dataclass
class SessionState:
    """Represents the current state of a review session."""
    session_id: str
    experiment_name: str
    data_source_config: Dict[str, Any]
    completed_reviews: List[str]
    remaining_queue: List[CodePair]
    created_timestamp: datetime

    def __post_init__(self):
        """Validate required fields."""
        if not self.session_id:
            raise ValueError("session_id cannot be empty")
        if not self.experiment_name:
            raise ValueError("experiment_name cannot be empty")
    
    def validate_integrity(self) -> bool:
        """Perform comprehensive data integrity validation."""
        try:
            # Check data types
            if not isinstance(self.session_id, str):
                return False
            if not isinstance(self.experiment_name, str):
                return False
            if not isinstance(self.data_source_config, dict):
                return False
            if not isinstance(self.completed_reviews, list):
                return False
            if not isinstance(self.remaining_queue, list):
                return False
            if not isinstance(self.created_timestamp, datetime):
                return False
            
            # Check that all completed_reviews are strings
            if not all(isinstance(review, str) for review in self.completed_reviews):
                return False
            
            # Check that all remaining_queue items are CodePair instances
            if not all(isinstance(pair, CodePair) for pair in self.remaining_queue):
                return False
            
            return True
        except Exception:
            return False
    
    def get_total_reviews(self) -> int:
        """Get total number of reviews (completed + remaining)."""
        return len(self.completed_reviews) + len(self.remaining_queue)
    
    def get_progress_percentage(self) -> float:
        """Get completion percentage."""
        total = self.get_total_reviews()
        if total == 0:
            return 100.0
        return (len(self.completed_reviews) / total) * 100.0


@dataclass
class SessionConfig:
    """Configuration for a review session."""
    experiment_name: str
    data_source_type: str  # 'folders', 'sqlite', 'excel'
    data_source_params: Dict[str, Any]
    sample_percentage: float
    output_format: str  # 'excel', 'csv'
    selected_model: Optional[str] = None  # Optional model filtering
    selected_strategy: Optional[str] = None  # Optional prompting strategy filtering

    def __post_init__(self):
        """Validate configuration values."""
        if not self.experiment_name:
            raise ValueError("experiment_name cannot be empty")
        
        valid_source_types = {'folders', 'sqlite', 'excel'}
        if self.data_source_type not in valid_source_types:
            raise ValueError(f"data_source_type must be one of {valid_source_types}")
        
        if not (1 <= self.sample_percentage <= 100):
            raise ValueError("sample_percentage must be between 1 and 100")
        
        valid_output_formats = {'excel', 'csv'}
        if self.output_format not in valid_output_formats:
            raise ValueError(f"output_format must be one of {valid_output_formats}")