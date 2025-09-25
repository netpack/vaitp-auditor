"""
Code difference computation engine for the VAITP-Auditor system.
"""

import difflib
import hashlib
from typing import List, Optional
from .models import DiffLine
from ..utils.performance import (
    get_content_cache, get_performance_monitor, 
    performance_monitor, cached_content
)


class CodeDiffer:
    """
    Computes differences between code snippets using difflib.SequenceMatcher.
    
    This class provides both structured data output for UI rendering and
    text-based unified diff format for report storage.
    """
    
    def __init__(self):
        """Initialize the CodeDiffer."""
        self._cache = get_content_cache()
        self._monitor = get_performance_monitor()
        self._diff_cache = {}  # Local cache for diff results
    
    @performance_monitor("compute_diff")
    def compute_diff(self, expected: Optional[str], generated: str) -> List[DiffLine]:
        """
        Compute line-by-line differences between expected and generated code.
        
        Args:
            expected: The expected (ground-truth) code, can be None
            generated: The generated code to compare against
            
        Returns:
            List of DiffLine objects with tags: 'equal', 'add', 'remove', 'modify'
        """
        if expected is None:
            expected = ""
        
        # Generate cache key for this diff computation
        cache_key = self._generate_diff_cache_key(expected, generated)
        
        # Check local cache first
        if cache_key in self._diff_cache:
            return self._diff_cache[cache_key]
        
        # Check if content is large and should be processed differently
        expected_size = len(expected.encode('utf-8'))
        generated_size = len(generated.encode('utf-8'))
        is_large = expected_size > 100000 or generated_size > 100000  # 100KB threshold
        
        if is_large:
            diff_lines = self._compute_large_diff(expected, generated)
        else:
            diff_lines = self._compute_standard_diff(expected, generated)
        
        # Cache the result (limit cache size for memory management)
        if len(self._diff_cache) < 100:  # Limit to 100 cached diffs
            self._diff_cache[cache_key] = diff_lines
        
        return diff_lines
    
    def _compute_standard_diff(self, expected: str, generated: str) -> List[DiffLine]:
        """Compute diff for standard-sized content."""
        # Split into lines for comparison
        expected_lines = expected.splitlines(keepends=False)
        generated_lines = generated.splitlines(keepends=False)
        
        # Use SequenceMatcher for line-by-line comparison
        matcher = difflib.SequenceMatcher(None, expected_lines, generated_lines)
        
        diff_lines = []
        line_number = 1
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                # Lines are identical
                for i in range(i1, i2):
                    diff_lines.append(DiffLine(
                        tag='equal',
                        line_content=expected_lines[i],
                        line_number=line_number
                    ))
                    line_number += 1
            
            elif tag == 'delete':
                # Lines removed from expected
                for i in range(i1, i2):
                    diff_lines.append(DiffLine(
                        tag='remove',
                        line_content=expected_lines[i],
                        line_number=line_number
                    ))
                    line_number += 1
            
            elif tag == 'insert':
                # Lines added in generated
                for j in range(j1, j2):
                    diff_lines.append(DiffLine(
                        tag='add',
                        line_content=generated_lines[j],
                        line_number=line_number
                    ))
                    line_number += 1
            
            elif tag == 'replace':
                # Lines modified - mark both removed and added
                # First mark the removed lines
                for i in range(i1, i2):
                    diff_lines.append(DiffLine(
                        tag='remove',
                        line_content=expected_lines[i],
                        line_number=line_number
                    ))
                    line_number += 1
                
                # Then mark the added lines
                for j in range(j1, j2):
                    diff_lines.append(DiffLine(
                        tag='add',
                        line_content=generated_lines[j],
                        line_number=line_number
                    ))
                    line_number += 1
        
        return diff_lines
    
    def _compute_large_diff(self, expected: str, generated: str) -> List[DiffLine]:
        """Compute diff for large content using chunked processing."""
        from ..utils.performance import get_chunked_processor
        
        processor = get_chunked_processor()
        
        # Split into lines
        expected_lines = expected.splitlines(keepends=False)
        generated_lines = generated.splitlines(keepends=False)
        
        # For very large files, use a more memory-efficient approach
        if len(expected_lines) > 10000 or len(generated_lines) > 10000:
            return self._compute_chunked_diff(expected_lines, generated_lines)
        else:
            return self._compute_standard_diff(expected, generated)
    
    def _compute_chunked_diff(self, expected_lines: List[str], generated_lines: List[str]) -> List[DiffLine]:
        """Compute diff in chunks for very large files."""
        # For very large files, we'll use a simplified approach
        # that processes the files in chunks to avoid memory issues
        
        chunk_size = 1000  # Process 1000 lines at a time
        diff_lines = []
        line_number = 1
        
        max_lines = max(len(expected_lines), len(generated_lines))
        
        for start in range(0, max_lines, chunk_size):
            end = min(start + chunk_size, max_lines)
            
            expected_chunk = expected_lines[start:end] if start < len(expected_lines) else []
            generated_chunk = generated_lines[start:end] if start < len(generated_lines) else []
            
            # Pad shorter chunk with empty lines for comparison
            while len(expected_chunk) < len(generated_chunk):
                expected_chunk.append("")
            while len(generated_chunk) < len(expected_chunk):
                generated_chunk.append("")
            
            # Compare chunk
            matcher = difflib.SequenceMatcher(None, expected_chunk, generated_chunk)
            
            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                if tag == 'equal':
                    for i in range(i1, i2):
                        if i < len(expected_chunk) and expected_chunk[i]:
                            diff_lines.append(DiffLine(
                                tag='equal',
                                line_content=expected_chunk[i],
                                line_number=line_number + i
                            ))
                
                elif tag == 'delete':
                    for i in range(i1, i2):
                        if i < len(expected_chunk) and expected_chunk[i]:
                            diff_lines.append(DiffLine(
                                tag='remove',
                                line_content=expected_chunk[i],
                                line_number=line_number + i
                            ))
                
                elif tag == 'insert':
                    for j in range(j1, j2):
                        if j < len(generated_chunk) and generated_chunk[j]:
                            diff_lines.append(DiffLine(
                                tag='add',
                                line_content=generated_chunk[j],
                                line_number=line_number + j
                            ))
                
                elif tag == 'replace':
                    for i in range(i1, i2):
                        if i < len(expected_chunk) and expected_chunk[i]:
                            diff_lines.append(DiffLine(
                                tag='remove',
                                line_content=expected_chunk[i],
                                line_number=line_number + i
                            ))
                    
                    for j in range(j1, j2):
                        if j < len(generated_chunk) and generated_chunk[j]:
                            diff_lines.append(DiffLine(
                                tag='add',
                                line_content=generated_chunk[j],
                                line_number=line_number + j
                            ))
            
            line_number += len(expected_chunk)
        
        return diff_lines
    
    def _generate_diff_cache_key(self, expected: str, generated: str) -> str:
        """Generate a cache key for diff computation."""
        content = f"{expected}|||{generated}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    @performance_monitor("get_diff_text")
    def get_diff_text(self, expected: Optional[str], generated: str) -> str:
        """
        Generate unified diff format text for report storage.
        
        Args:
            expected: The expected (ground-truth) code, can be None
            generated: The generated code to compare against
            
        Returns:
            Unified diff format string
        """
        if expected is None:
            expected = ""
        
        # Generate cache key for text diff
        cache_key = f"text_diff_{self._generate_diff_cache_key(expected, generated)}"
        
        # Check cache
        cached_result = self._cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Check if content is large
        expected_size = len(expected.encode('utf-8'))
        generated_size = len(generated.encode('utf-8'))
        is_large = expected_size > 100000 or generated_size > 100000  # 100KB threshold
        
        if is_large:
            # For large files, create a summary diff instead of full diff
            result = self._generate_summary_diff(expected, generated)
        else:
            # Split into lines for difflib.unified_diff
            expected_lines = expected.splitlines(keepends=True)
            generated_lines = generated.splitlines(keepends=True)
            
            # Generate unified diff
            diff_lines = list(difflib.unified_diff(
                expected_lines,
                generated_lines,
                fromfile='expected_code',
                tofile='generated_code',
                lineterm=''
            ))
            
            result = ''.join(diff_lines)
        
        # Cache the result if it's not too large
        if len(result) < 50000:  # Don't cache very large diffs
            self._cache.put(cache_key, result)
        
        return result
    
    def _generate_summary_diff(self, expected: str, generated: str) -> str:
        """Generate a summary diff for large files."""
        expected_lines = expected.splitlines()
        generated_lines = generated.splitlines()
        
        # Create a summary instead of full diff for large files
        summary = [
            f"=== LARGE FILE DIFF SUMMARY ===",
            f"Expected lines: {len(expected_lines)}",
            f"Generated lines: {len(generated_lines)}",
            f"Size difference: {len(generated_lines) - len(expected_lines)} lines",
            ""
        ]
        
        # Sample first and last few lines for context
        sample_size = 10
        
        if expected_lines:
            summary.extend([
                "--- Expected (first 10 lines) ---",
                *expected_lines[:sample_size],
                "",
                "--- Expected (last 10 lines) ---",
                *expected_lines[-sample_size:],
                ""
            ])
        
        if generated_lines:
            summary.extend([
                "+++ Generated (first 10 lines) +++",
                *generated_lines[:sample_size],
                "",
                "+++ Generated (last 10 lines) +++",
                *generated_lines[-sample_size:],
                ""
            ])
        
        summary.append("=== END SUMMARY ===")
        
        return '\n'.join(summary)
    
    def _detect_modifications(self, expected_lines: List[str], generated_lines: List[str]) -> List[DiffLine]:
        """
        Helper method to detect line modifications more granularly.
        
        This method could be extended in the future to provide more sophisticated
        modification detection (e.g., word-level changes within lines).
        
        Args:
            expected_lines: Lines from expected code
            generated_lines: Lines from generated code
            
        Returns:
            List of DiffLine objects with 'modify' tags where appropriate
        """
        # For now, this is a placeholder for future enhancement
        # The current implementation in compute_diff handles replacements
        # as separate remove/add operations, which is sufficient for the requirements
        return []