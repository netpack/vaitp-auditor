"""
File system data source implementation for folder-based code pairs.
"""

import os
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

from .base import DataSource, DataSourceConfigurationError, DataSourceValidationError
from ..core.models import CodePair
from ..utils.performance import LazyLoader, get_chunked_processor, performance_monitor


class FileSystemSource(DataSource):
    """
    Data source implementation for loading code pairs from file system folders.
    
    Matches files between generated and expected code folders based on base names,
    ignoring file extensions. Handles encoding fallback from UTF-8 to latin-1.
    """

    def __init__(self):
        """Initialize the file system data source."""
        super().__init__()
        self.generated_folder: Optional[Path] = None
        self.expected_folder: Optional[Path] = None
        self.input_folder: Optional[Path] = None
        self._file_pairs: List[Tuple[Path, Optional[Path], Optional[Path]]] = []
        self._chunked_processor = get_chunked_processor()
        self._lazy_loading_threshold = 100 * 1024  # 100KB threshold for lazy loading

    def configure(self) -> bool:
        """
        Configure the file system data source with folder paths.
        
        Prompts user for generated code folder (mandatory) and expected code folder (optional).
        
        Returns:
            bool: True if configuration was successful, False otherwise.
        """
        try:
            # Get generated code folder (mandatory)
            while True:
                generated_path = input("Enter path to Generated Code folder: ").strip()
                if not generated_path:
                    print("Generated Code folder path is required.")
                    continue
                
                generated_folder = Path(generated_path).expanduser().resolve()
                if not generated_folder.exists():
                    print(f"Error: Generated Code folder does not exist: {generated_folder}")
                    continue
                
                if not generated_folder.is_dir():
                    print(f"Error: Path is not a directory: {generated_folder}")
                    continue
                
                self.generated_folder = generated_folder
                break

            # Get expected code folder (optional)
            expected_path = input("Enter path to Expected Code folder (optional, press Enter to skip): ").strip()
            if expected_path:
                expected_folder = Path(expected_path).expanduser().resolve()
                if not expected_folder.exists():
                    print(f"Warning: Expected Code folder does not exist: {expected_folder}")
                    print("Continuing with generated code only...")
                    self.expected_folder = None
                elif not expected_folder.is_dir():
                    print(f"Warning: Expected Code path is not a directory: {expected_folder}")
                    print("Continuing with generated code only...")
                    self.expected_folder = None
                else:
                    self.expected_folder = expected_folder
            else:
                self.expected_folder = None

            # Get input code folder (optional)
            input_path = input("Enter path to Input Code folder (optional, press Enter to skip): ").strip()
            if input_path:
                input_folder = Path(input_path).expanduser().resolve()
                if not input_folder.exists():
                    print(f"Warning: Input Code folder does not exist: {input_folder}")
                    print("Continuing without input code...")
                    self.input_folder = None
                elif not input_folder.is_dir():
                    print(f"Warning: Input Code path is not a directory: {input_folder}")
                    print("Continuing without input code...")
                    self.input_folder = None
                else:
                    self.input_folder = input_folder
            else:
                self.input_folder = None

            # Discover and match files
            self._discover_file_pairs()
            
            if not self._file_pairs:
                print("Error: No code files found in the specified folder(s).")
                return False

            self._configured = True
            print(f"Configuration successful. Found {len(self._file_pairs)} code file(s).")
            return True

        except KeyboardInterrupt:
            print("\nConfiguration cancelled by user.")
            return False
        except Exception as e:
            self._log_error_with_context(e, {
                "generated_folder": str(self.generated_folder) if self.generated_folder else None,
                "expected_folder": str(self.expected_folder) if self.expected_folder else None
            })
            return False

    @performance_monitor("load_data")
    def load_data(self, sample_percentage: float) -> List[CodePair]:
        """
        Load code pairs from the configured folders with performance optimizations.
        
        Args:
            sample_percentage: Percentage of data to sample (1-100).
            
        Returns:
            List[CodePair]: List of code pairs ready for review.
            
        Raises:
            ValueError: If sample_percentage is not between 1 and 100.
            RuntimeError: If data source is not properly configured.
        """
        self._validate_configured()
        self._validate_sample_percentage(sample_percentage)

        # Process file pairs in chunks for better memory management
        def process_file_chunk(file_chunk: List[Tuple[Path, Optional[Path], Optional[Path]]]) -> List[CodePair]:
            chunk_pairs = []
            
            for generated_file, expected_file, input_file in file_chunk:
                try:
                    # Check file sizes first to determine loading strategy
                    generated_size = generated_file.stat().st_size if generated_file.exists() else 0
                    expected_size = expected_file.stat().st_size if expected_file and expected_file.exists() else 0
                    input_size = input_file.stat().st_size if input_file and input_file.exists() else 0
                    
                    # Use lazy loading for large files
                    max_size = max(generated_size, expected_size, input_size)
                    if max_size > self._lazy_loading_threshold:
                        code_pair = self._create_lazy_code_pair(generated_file, expected_file, input_file)
                    else:
                        code_pair = self._create_standard_code_pair(generated_file, expected_file, input_file)
                    
                    if code_pair and self._validate_code_pair(code_pair):
                        chunk_pairs.append(code_pair)
                    elif code_pair:
                        self._logger.warning(f"Skipping invalid code pair: {code_pair.identifier}")

                except Exception as e:
                    self._log_error_with_context(e, {
                        "generated_file": str(generated_file),
                        "expected_file": str(expected_file) if expected_file else None,
                        "input_file": str(input_file) if input_file else None
                    })
                    continue
            
            return chunk_pairs

        # Process all file pairs in chunks
        all_code_pairs = self._chunked_processor.process_chunks(self._file_pairs, process_file_chunk)

        if not all_code_pairs:
            raise DataSourceValidationError("No valid code pairs could be loaded")

        # Apply sampling
        sampled_pairs = self._sample_data(all_code_pairs, sample_percentage)
        
        self._logger.info(f"Loaded {len(sampled_pairs)} code pairs ({sample_percentage}% of {len(all_code_pairs)} total)")
        return sampled_pairs
    
    def _create_standard_code_pair(self, generated_file: Path, expected_file: Optional[Path], input_file: Optional[Path] = None) -> Optional[CodePair]:
        """Create a code pair with immediate loading for standard-sized files."""
        # Load generated code (mandatory)
        generated_code = self._read_file_with_fallback(generated_file)
        if generated_code is None:
            self._logger.warning(f"Skipping {generated_file}: could not read file")
            return None

        # Load expected code (optional)
        expected_code = None
        if expected_file and expected_file.exists():
            expected_code = self._read_file_with_fallback(expected_file)
            if expected_code is None:
                self._logger.warning(f"Could not read expected file {expected_file}, continuing with generated only")

        # Load input code (optional)
        input_code = None
        if input_file and input_file.exists():
            input_code = self._read_file_with_fallback(input_file)
            if input_code is None:
                self._logger.warning(f"Could not read input file {input_file}, continuing without input code")

        # Create code pair
        identifier = self._get_file_identifier(generated_file, expected_file, input_file)
        source_info = {
            "generated_file": str(generated_file),
            "expected_file": str(expected_file) if expected_file else None,
            "input_file": str(input_file) if input_file else None,
            "generated_folder": str(self.generated_folder),
            "expected_folder": str(self.expected_folder) if self.expected_folder else None,
            "input_folder": str(self.input_folder) if self.input_folder else None,
            "lazy_loaded": False
        }

        return CodePair(
            identifier=identifier,
            expected_code=expected_code,
            generated_code=generated_code,
            source_info=source_info,
            input_code=input_code
        )
    
    def _create_lazy_code_pair(self, generated_file: Path, expected_file: Optional[Path], input_file: Optional[Path] = None) -> Optional[CodePair]:
        """Create a code pair with lazy loading for large files."""
        # Create lazy loaders
        generated_loader = LazyLoader(lambda: self._read_file_with_fallback(generated_file))
        expected_loader = None
        if expected_file and expected_file.exists():
            expected_loader = LazyLoader(lambda: self._read_file_with_fallback(expected_file))
        
        input_loader = None
        if input_file and input_file.exists():
            input_loader = LazyLoader(lambda: self._read_file_with_fallback(input_file))

        # Check if we can at least read the files
        try:
            # Test read a small portion to ensure files are accessible
            with open(generated_file, 'r', encoding='utf-8') as f:
                f.read(100)  # Read first 100 chars to test
        except Exception as e:
            self._logger.warning(f"Cannot access generated file {generated_file}: {e}")
            return None

        if expected_file and expected_file.exists():
            try:
                with open(expected_file, 'r', encoding='utf-8') as f:
                    f.read(100)  # Read first 100 chars to test
            except Exception as e:
                self._logger.warning(f"Cannot access expected file {expected_file}: {e}")
                expected_loader = None

        if input_file and input_file.exists():
            try:
                with open(input_file, 'r', encoding='utf-8') as f:
                    f.read(100)  # Read first 100 chars to test
            except Exception as e:
                self._logger.warning(f"Cannot access input file {input_file}: {e}")
                input_loader = None

        # Create code pair with lazy content
        identifier = self._get_file_identifier(generated_file, expected_file, input_file)
        source_info = {
            "generated_file": str(generated_file),
            "expected_file": str(expected_file) if expected_file else None,
            "input_file": str(input_file) if input_file else None,
            "generated_folder": str(self.generated_folder),
            "expected_folder": str(self.expected_folder) if self.expected_folder else None,
            "input_folder": str(self.input_folder) if self.input_folder else None,
            "lazy_loaded": True,
            "generated_size": generated_file.stat().st_size,
            "expected_size": expected_file.stat().st_size if expected_file and expected_file.exists() else 0,
            "input_size": input_file.stat().st_size if input_file and input_file.exists() else 0
        }

        return CodePair(
            identifier=identifier,
            expected_code=expected_loader.content if expected_loader else None,
            generated_code=generated_loader.content,
            source_info=source_info,
            input_code=input_loader.content if input_loader else None
        )

    def get_total_count(self) -> int:
        """
        Get the total number of available code pairs before sampling.
        
        Returns:
            int: Total count of available code pairs.
            
        Raises:
            RuntimeError: If data source is not properly configured.
        """
        self._validate_configured()
        return len(self._file_pairs)

    def _discover_file_pairs(self) -> None:
        """
        Discover and match files between generated, expected, and input folders.
        
        Matches files by base name (ignoring extensions) and creates pairs.
        """
        self._file_pairs = []

        if not self.generated_folder:
            return

        # Get all files from generated folder
        generated_files = []
        for file_path in self.generated_folder.rglob('*'):
            if file_path.is_file() and self._is_code_file(file_path):
                generated_files.append(file_path)

        # Create mapping of base names to expected files
        expected_files_map = {}
        if self.expected_folder:
            for file_path in self.expected_folder.rglob('*'):
                if file_path.is_file() and self._is_code_file(file_path):
                    base_name = self._get_base_name(file_path)
                    expected_files_map[base_name] = file_path

        # Create mapping of base names to input files
        input_files_map = {}
        if self.input_folder:
            for file_path in self.input_folder.rglob('*'):
                if file_path.is_file() and self._is_code_file(file_path):
                    base_name = self._get_base_name(file_path)
                    input_files_map[base_name] = file_path

        # Match generated files with expected and input files
        for generated_file in generated_files:
            base_name = self._get_base_name(generated_file)
            expected_file = expected_files_map.get(base_name)
            input_file = input_files_map.get(base_name)
            
            self._file_pairs.append((generated_file, expected_file, input_file))

        self._logger.info(f"Discovered {len(self._file_pairs)} file pairs")
        if self.expected_folder:
            matched_expected_count = sum(1 for _, expected, _ in self._file_pairs if expected is not None)
            self._logger.info(f"Matched {matched_expected_count} files with expected counterparts")
        if self.input_folder:
            matched_input_count = sum(1 for _, _, input_file in self._file_pairs if input_file is not None)
            self._logger.info(f"Matched {matched_input_count} files with input counterparts")

    def _get_base_name(self, file_path: Path) -> str:
        """
        Get the base name of a file (without extension and relative to its root folder).
        
        Args:
            file_path: Path to the file.
            
        Returns:
            str: Base name for matching purposes.
        """
        # Get relative path from the appropriate root folder
        if self.expected_folder and self.expected_folder in file_path.parents:
            relative_path = file_path.relative_to(self.expected_folder)
        elif self.input_folder and self.input_folder in file_path.parents:
            relative_path = file_path.relative_to(self.input_folder)
        elif self.generated_folder and self.generated_folder in file_path.parents:
            relative_path = file_path.relative_to(self.generated_folder)
        else:
            relative_path = file_path

        # Remove extension and return as string
        return str(relative_path.with_suffix(''))

    def _is_code_file(self, file_path: Path) -> bool:
        """
        Check if a file is a code file based on its extension.
        
        Args:
            file_path: Path to check.
            
        Returns:
            bool: True if it's a code file, False otherwise.
        """
        code_extensions = {
            '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.hpp',
            '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala',
            '.r', '.m', '.mm', '.pl', '.sh', '.bash', '.ps1', '.sql',
            '.html', '.css', '.xml', '.json', '.yaml', '.yml', '.toml',
            '.md', '.txt'  # Include text files that might contain code
        }
        
        return file_path.suffix.lower() in code_extensions

    def _read_file_with_fallback(self, file_path: Path) -> Optional[str]:
        """
        Read a file with UTF-8 encoding and fallback to latin-1 if needed.
        
        Args:
            file_path: Path to the file to read.
            
        Returns:
            Optional[str]: File content or None if reading failed.
        """
        try:
            # Try UTF-8 first
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError as e:
            # Fall back to latin-1
            return self._handle_encoding_error(str(file_path), e)
        except Exception as e:
            self._logger.error(f"Failed to read file {file_path}: {e}")
            return None

    def _get_file_identifier(self, generated_file: Path, expected_file: Optional[Path], input_file: Optional[Path] = None) -> str:
        """
        Generate a unique identifier for a file pair.
        
        Args:
            generated_file: Path to the generated code file.
            expected_file: Path to the expected code file (optional).
            input_file: Path to the input code file (optional).
            
        Returns:
            str: Unique identifier for the file pair.
        """
        base_name = self._get_base_name(generated_file)
        
        # Clean up the base name to make it a valid identifier
        identifier = base_name.replace('/', '_').replace('\\', '_').replace(' ', '_')
        
        # Remove any characters that aren't alphanumeric, underscore, dash, or dot
        identifier = ''.join(c for c in identifier if c.isalnum() or c in '_-.')
        
        # Ensure it's not empty
        if not identifier:
            identifier = f"file_{hash(str(generated_file)) % 10000}"
        
        return identifier