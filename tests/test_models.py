"""
Unit tests for core data models.
"""

import pytest
from datetime import datetime
from vaitp_auditor.core.models import (
    CodePair, ReviewResult, DiffLine, SessionState, SessionConfig
)


class TestCodePair:
    """Test cases for CodePair model."""
    
    def test_valid_code_pair_creation(self):
        """Test creating a valid CodePair."""
        code_pair = CodePair(
            identifier="test_001",
            expected_code="print('hello')",
            generated_code="print('world')",
            source_info={"file": "test.py"}
        )
        assert code_pair.identifier == "test_001"
        assert code_pair.expected_code == "print('hello')"
        assert code_pair.generated_code == "print('world')"
        assert code_pair.source_info == {"file": "test.py"}
    
    def test_code_pair_with_none_expected(self):
        """Test CodePair with None expected_code."""
        code_pair = CodePair(
            identifier="test_002",
            expected_code=None,
            generated_code="print('world')",
            source_info={}
        )
        assert code_pair.expected_code is None
        assert code_pair.generated_code == "print('world')"
    
    def test_empty_identifier_raises_error(self):
        """Test that empty identifier raises ValueError."""
        with pytest.raises(ValueError, match="identifier cannot be empty"):
            CodePair(
                identifier="",
                expected_code="test",
                generated_code="test",
                source_info={}
            )
    
    def test_empty_generated_code_raises_error(self):
        """Test that empty generated_code raises ValueError."""
        with pytest.raises(ValueError, match="generated_code cannot be empty"):
            CodePair(
                identifier="test",
                expected_code="test",
                generated_code="",
                source_info={}
            )
    
    def test_none_generated_code_raises_error(self):
        """Test that None generated_code raises ValueError."""
        with pytest.raises(ValueError, match="generated_code cannot be empty"):
            CodePair(
                identifier="test",
                expected_code="test",
                generated_code=None,
                source_info={}
            )
    
    def test_validate_integrity_valid_pair(self):
        """Test validate_integrity with valid CodePair."""
        code_pair = CodePair(
            identifier="test_001",
            expected_code="print('hello')",
            generated_code="print('world')",
            source_info={"file": "test.py"}
        )
        assert code_pair.validate_integrity() is True
    
    def test_validate_integrity_invalid_identifier(self):
        """Test validate_integrity with invalid identifier."""
        code_pair = CodePair(
            identifier="test@#$%",
            expected_code="test",
            generated_code="test",
            source_info={}
        )
        assert code_pair.validate_integrity() is False
    
    def test_validate_integrity_invalid_source_info(self):
        """Test validate_integrity with invalid source_info."""
        code_pair = CodePair(
            identifier="test",
            expected_code="test",
            generated_code="test",
            source_info="not_a_dict"
        )
        assert code_pair.validate_integrity() is False


class TestReviewResult:
    """Test cases for ReviewResult model."""
    
    def test_valid_review_result_creation(self):
        """Test creating a valid ReviewResult."""
        timestamp = datetime.utcnow()
        result = ReviewResult(
            review_id=1,
            source_identifier="test_001",
            experiment_name="test_experiment",
            review_timestamp_utc=timestamp,
            reviewer_verdict="Success",
            reviewer_comment="Looks good",
            time_to_review_seconds=45.5,
            expected_code="print('hello')",
            generated_code="print('world')",
            code_diff="- print('hello')\n+ print('world')"
        )
        assert result.review_id == 1
        assert result.source_identifier == "test_001"
        assert result.experiment_name == "test_experiment"
        assert result.review_timestamp_utc == timestamp
        assert result.reviewer_verdict == "Success"
        assert result.reviewer_comment == "Looks good"
        assert result.time_to_review_seconds == 45.5
    
    def test_negative_review_id_raises_error(self):
        """Test that negative review_id raises ValueError."""
        with pytest.raises(ValueError, match="review_id must be non-negative"):
            ReviewResult(
                review_id=-1,
                source_identifier="test",
                experiment_name="test",
                review_timestamp_utc=datetime.utcnow(),
                reviewer_verdict="Success",
                reviewer_comment="",
                time_to_review_seconds=10.0,
                expected_code="",
                generated_code="test",
                code_diff=""
            )
    
    def test_empty_source_identifier_raises_error(self):
        """Test that empty source_identifier raises ValueError."""
        with pytest.raises(ValueError, match="source_identifier cannot be empty"):
            ReviewResult(
                review_id=1,
                source_identifier="",
                experiment_name="test",
                review_timestamp_utc=datetime.utcnow(),
                reviewer_verdict="Success",
                reviewer_comment="",
                time_to_review_seconds=10.0,
                expected_code="",
                generated_code="test",
                code_diff=""
            )
    
    def test_empty_experiment_name_raises_error(self):
        """Test that empty experiment_name raises ValueError."""
        with pytest.raises(ValueError, match="experiment_name cannot be empty"):
            ReviewResult(
                review_id=1,
                source_identifier="test",
                experiment_name="",
                review_timestamp_utc=datetime.utcnow(),
                reviewer_verdict="Success",
                reviewer_comment="",
                time_to_review_seconds=10.0,
                expected_code="",
                generated_code="test",
                code_diff=""
            )
    
    def test_empty_reviewer_verdict_raises_error(self):
        """Test that empty reviewer_verdict raises ValueError."""
        with pytest.raises(ValueError, match="reviewer_verdict cannot be empty"):
            ReviewResult(
                review_id=1,
                source_identifier="test",
                experiment_name="test",
                review_timestamp_utc=datetime.utcnow(),
                reviewer_verdict="",
                reviewer_comment="",
                time_to_review_seconds=10.0,
                expected_code="",
                generated_code="test",
                code_diff=""
            )
    
    def test_negative_time_to_review_raises_error(self):
        """Test that negative time_to_review_seconds raises ValueError."""
        with pytest.raises(ValueError, match="time_to_review_seconds must be non-negative"):
            ReviewResult(
                review_id=1,
                source_identifier="test",
                experiment_name="test",
                review_timestamp_utc=datetime.utcnow(),
                reviewer_verdict="Success",
                reviewer_comment="",
                time_to_review_seconds=-5.0,
                expected_code="",
                generated_code="test",
                code_diff=""
            )
    
    def test_validate_verdict_valid_verdicts(self):
        """Test validate_verdict with all valid verdict values."""
        valid_verdicts = [
            'Success', 
            'Failure - No Change', 
            'Invalid Code', 
            'Wrong Vulnerability', 
            'Partial Success'
        ]
        
        for verdict in valid_verdicts:
            result = ReviewResult(
                review_id=1,
                source_identifier="test",
                experiment_name="test",
                review_timestamp_utc=datetime.utcnow(),
                reviewer_verdict=verdict,
                reviewer_comment="",
                time_to_review_seconds=10.0,
                expected_code="",
                generated_code="test",
                code_diff=""
            )
            assert result.validate_verdict() is True
    
    def test_validate_verdict_invalid_verdict(self):
        """Test validate_verdict with invalid verdict."""
        result = ReviewResult(
            review_id=1,
            source_identifier="test",
            experiment_name="test",
            review_timestamp_utc=datetime.utcnow(),
            reviewer_verdict="Invalid Verdict",
            reviewer_comment="",
            time_to_review_seconds=10.0,
            expected_code="",
            generated_code="test",
            code_diff=""
        )
        assert result.validate_verdict() is False
    
    def test_validate_integrity_valid_result(self):
        """Test validate_integrity with valid ReviewResult."""
        result = ReviewResult(
            review_id=1,
            source_identifier="test",
            experiment_name="test",
            review_timestamp_utc=datetime.utcnow(),
            reviewer_verdict="Success",
            reviewer_comment="Good",
            time_to_review_seconds=10.0,
            expected_code="test",
            generated_code="test",
            code_diff="diff"
        )
        assert result.validate_integrity() is True


class TestDiffLine:
    """Test cases for DiffLine model."""
    
    def test_valid_diff_line_creation(self):
        """Test creating valid DiffLine instances."""
        for tag in ['equal', 'add', 'remove', 'modify']:
            diff_line = DiffLine(
                tag=tag,
                line_content="print('test')",
                line_number=1
            )
            assert diff_line.tag == tag
            assert diff_line.line_content == "print('test')"
            assert diff_line.line_number == 1
    
    def test_diff_line_without_line_number(self):
        """Test DiffLine with None line_number."""
        diff_line = DiffLine(
            tag="equal",
            line_content="test content"
        )
        assert diff_line.line_number is None
    
    def test_invalid_tag_raises_error(self):
        """Test that invalid tag raises ValueError."""
        with pytest.raises(ValueError, match="tag must be one of"):
            DiffLine(
                tag="invalid_tag",
                line_content="test"
            )
    
    def test_empty_tag_raises_error(self):
        """Test that empty tag raises ValueError."""
        with pytest.raises(ValueError, match="tag must be one of"):
            DiffLine(
                tag="",
                line_content="test"
            )


class TestSessionState:
    """Test cases for SessionState model."""
    
    def test_valid_session_state_creation(self):
        """Test creating a valid SessionState."""
        timestamp = datetime.utcnow()
        code_pair = CodePair(
            identifier="test",
            expected_code="test",
            generated_code="test",
            source_info={}
        )
        
        session_state = SessionState(
            session_id="session_123",
            experiment_name="test_experiment",
            data_source_config={"type": "folders"},
            completed_reviews=["review_1", "review_2"],
            remaining_queue=[code_pair],
            created_timestamp=timestamp
        )
        
        assert session_state.session_id == "session_123"
        assert session_state.experiment_name == "test_experiment"
        assert session_state.data_source_config == {"type": "folders"}
        assert session_state.completed_reviews == ["review_1", "review_2"]
        assert len(session_state.remaining_queue) == 1
        assert session_state.created_timestamp == timestamp
    
    def test_empty_session_id_raises_error(self):
        """Test that empty session_id raises ValueError."""
        with pytest.raises(ValueError, match="session_id cannot be empty"):
            SessionState(
                session_id="",
                experiment_name="test",
                data_source_config={},
                completed_reviews=[],
                remaining_queue=[],
                created_timestamp=datetime.utcnow()
            )
    
    def test_empty_experiment_name_raises_error(self):
        """Test that empty experiment_name raises ValueError."""
        with pytest.raises(ValueError, match="experiment_name cannot be empty"):
            SessionState(
                session_id="test",
                experiment_name="",
                data_source_config={},
                completed_reviews=[],
                remaining_queue=[],
                created_timestamp=datetime.utcnow()
            )
    
    def test_validate_integrity_valid_state(self):
        """Test validate_integrity with valid SessionState."""
        code_pair = CodePair(
            identifier="test",
            expected_code="test",
            generated_code="test",
            source_info={}
        )
        
        session_state = SessionState(
            session_id="session_123",
            experiment_name="test_experiment",
            data_source_config={"type": "folders"},
            completed_reviews=["review_1"],
            remaining_queue=[code_pair],
            created_timestamp=datetime.utcnow()
        )
        
        assert session_state.validate_integrity() is True
    
    def test_get_total_reviews(self):
        """Test get_total_reviews calculation."""
        code_pair = CodePair(
            identifier="test",
            expected_code="test",
            generated_code="test",
            source_info={}
        )
        
        session_state = SessionState(
            session_id="session_123",
            experiment_name="test_experiment",
            data_source_config={},
            completed_reviews=["review_1", "review_2"],
            remaining_queue=[code_pair],
            created_timestamp=datetime.utcnow()
        )
        
        assert session_state.get_total_reviews() == 3
    
    def test_get_progress_percentage(self):
        """Test get_progress_percentage calculation."""
        code_pair = CodePair(
            identifier="test",
            expected_code="test",
            generated_code="test",
            source_info={}
        )
        
        session_state = SessionState(
            session_id="session_123",
            experiment_name="test_experiment",
            data_source_config={},
            completed_reviews=["review_1"],
            remaining_queue=[code_pair],
            created_timestamp=datetime.utcnow()
        )
        
        assert session_state.get_progress_percentage() == 50.0
    
    def test_get_progress_percentage_empty(self):
        """Test get_progress_percentage with no reviews."""
        session_state = SessionState(
            session_id="session_123",
            experiment_name="test_experiment",
            data_source_config={},
            completed_reviews=[],
            remaining_queue=[],
            created_timestamp=datetime.utcnow()
        )
        
        assert session_state.get_progress_percentage() == 100.0


class TestSessionConfig:
    """Test cases for SessionConfig model."""
    
    def test_valid_session_config_creation(self):
        """Test creating a valid SessionConfig."""
        config = SessionConfig(
            experiment_name="test_experiment",
            data_source_type="folders",
            data_source_params={"path": "/test"},
            sample_percentage=50.0,
            output_format="excel"
        )
        
        assert config.experiment_name == "test_experiment"
        assert config.data_source_type == "folders"
        assert config.data_source_params == {"path": "/test"}
        assert config.sample_percentage == 50.0
        assert config.output_format == "excel"
    
    def test_empty_experiment_name_raises_error(self):
        """Test that empty experiment_name raises ValueError."""
        with pytest.raises(ValueError, match="experiment_name cannot be empty"):
            SessionConfig(
                experiment_name="",
                data_source_type="folders",
                data_source_params={},
                sample_percentage=100.0,
                output_format="excel"
            )
    
    def test_invalid_data_source_type_raises_error(self):
        """Test that invalid data_source_type raises ValueError."""
        with pytest.raises(ValueError, match="data_source_type must be one of"):
            SessionConfig(
                experiment_name="test",
                data_source_type="invalid_type",
                data_source_params={},
                sample_percentage=100.0,
                output_format="excel"
            )
    
    def test_invalid_sample_percentage_raises_error(self):
        """Test that invalid sample_percentage raises ValueError."""
        # Test below minimum
        with pytest.raises(ValueError, match="sample_percentage must be between 1 and 100"):
            SessionConfig(
                experiment_name="test",
                data_source_type="folders",
                data_source_params={},
                sample_percentage=0.5,
                output_format="excel"
            )
        
        # Test above maximum
        with pytest.raises(ValueError, match="sample_percentage must be between 1 and 100"):
            SessionConfig(
                experiment_name="test",
                data_source_type="folders",
                data_source_params={},
                sample_percentage=101.0,
                output_format="excel"
            )
    
    def test_invalid_output_format_raises_error(self):
        """Test that invalid output_format raises ValueError."""
        with pytest.raises(ValueError, match="output_format must be one of"):
            SessionConfig(
                experiment_name="test",
                data_source_type="folders",
                data_source_params={},
                sample_percentage=100.0,
                output_format="invalid_format"
            )
    
    def test_boundary_sample_percentages(self):
        """Test boundary values for sample_percentage."""
        # Test minimum valid value
        config1 = SessionConfig(
            experiment_name="test",
            data_source_type="folders",
            data_source_params={},
            sample_percentage=1.0,
            output_format="excel"
        )
        assert config1.sample_percentage == 1.0
        
        # Test maximum valid value
        config2 = SessionConfig(
            experiment_name="test",
            data_source_type="folders",
            data_source_params={},
            sample_percentage=100.0,
            output_format="csv"
        )
        assert config2.sample_percentage == 100.0
    
    def test_all_valid_data_source_types(self):
        """Test all valid data_source_type values."""
        for source_type in ['folders', 'sqlite', 'excel']:
            config = SessionConfig(
                experiment_name="test",
                data_source_type=source_type,
                data_source_params={},
                sample_percentage=100.0,
                output_format="excel"
            )
            assert config.data_source_type == source_type
    
    def test_all_valid_output_formats(self):
        """Test all valid output_format values."""
        for output_format in ['excel', 'csv']:
            config = SessionConfig(
                experiment_name="test",
                data_source_type="folders",
                data_source_params={},
                sample_percentage=100.0,
                output_format=output_format
            )
            assert config.output_format == output_format