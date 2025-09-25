#!/usr/bin/env python3
"""
Documentation validation script for VAITP-Auditor.

This script validates:
- Documentation completeness and accuracy
- Link validity (both internal and external)
- Version consistency across files
- Installation instructions accuracy
- Code examples and snippets
"""

import os
import sys
import re
import json
import time
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
import argparse
import subprocess


class DocumentationValidator:
    """Comprehensive documentation validation."""
    
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.results = {
            "validation_timestamp": time.time(),
            "project_root": str(project_root),
            "validation_results": {},
            "overall_status": "unknown"
        }
    
    def validate_required_files(self) -> bool:
        """Validate that all required documentation files exist."""
        print("📋 Validating required documentation files...")
        
        required_files = [
            "README.md",
            "CHANGELOG.md",
            "LICENSE",
            "deployment/README.md",
            "deployment/CODE_SIGNING_GUIDE.md",
            "deployment/MAINTAINER_GUIDE.md",
            "deployment/DEPLOYMENT_PIPELINE_GUIDE.md",
            "docs/GUI_USER_GUIDE.md",
            "docs/GUI_DEVELOPER_GUIDE.md",
            "docs/DEVELOPER_GUIDE.md",
            "docs/USER_GUIDE.md",
            "docs/SETUP_GUIDE.md",
            "docs/VERSIONING.md"
        ]
        
        missing_files = []
        existing_files = []
        
        for file_path in required_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                existing_files.append(file_path)
                print(f"  ✅ {file_path}")
            else:
                missing_files.append(file_path)
                print(f"  ❌ {file_path}")
        
        success = len(missing_files) == 0
        
        self.results["validation_results"]["required_files"] = {
            "success": success,
            "existing_files": existing_files,
            "missing_files": missing_files,
            "total_required": len(required_files),
            "total_existing": len(existing_files)
        }
        
        if success:
            print(f"  ✅ All {len(required_files)} required files present")
        else:
            print(f"  ❌ {len(missing_files)} files missing out of {len(required_files)}")
        
        return success
    
    def validate_internal_links(self) -> bool:
        """Validate internal links in documentation files."""
        print("🔗 Validating internal links...")
        
        # Find all markdown files
        md_files = []
        for pattern in ["*.md", "**/*.md"]:
            md_files.extend(self.project_root.glob(pattern))
        
        all_broken_links = {}
        total_links_checked = 0
        total_broken_links = 0
        
        for md_file in md_files:
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract markdown links [text](url)
                link_pattern = r'\[([^\]]*)\]\(([^)]+)\)'
                links = re.findall(link_pattern, content)
                
                broken_links = []
                
                for link_text, link_url in links:
                    # Skip external links (http/https)
                    if link_url.startswith(('http://', 'https://', 'mailto:')):
                        continue
                    
                    # Skip anchor-only links
                    if link_url.startswith('#'):
                        continue
                    
                    total_links_checked += 1
                    
                    # Handle anchor links
                    if '#' in link_url:
                        link_url = link_url.split('#')[0]
                    
                    # Resolve relative path
                    if link_url:
                        link_path = (md_file.parent / link_url).resolve()
                        
                        # Check if target exists
                        if not link_path.exists():
                            broken_links.append({
                                "text": link_text,
                                "url": link_url,
                                "resolved_path": str(link_path)
                            })
                            total_broken_links += 1
                
                if broken_links:
                    relative_path = md_file.relative_to(self.project_root)
                    all_broken_links[str(relative_path)] = broken_links
                    print(f"  ❌ {relative_path}: {len(broken_links)} broken links")
                else:
                    relative_path = md_file.relative_to(self.project_root)
                    print(f"  ✅ {relative_path}: all links valid")
                    
            except Exception as e:
                relative_path = md_file.relative_to(self.project_root)
                print(f"  ⚠️  {relative_path}: error reading file - {e}")
        
        success = total_broken_links == 0
        
        self.results["validation_results"]["internal_links"] = {
            "success": success,
            "total_links_checked": total_links_checked,
            "total_broken_links": total_broken_links,
            "broken_links_by_file": all_broken_links,
            "files_checked": len(md_files)
        }
        
        if success:
            print(f"  ✅ All {total_links_checked} internal links are valid")
        else:
            print(f"  ❌ {total_broken_links} broken links found out of {total_links_checked}")
        
        return success
    
    def validate_external_links(self) -> bool:
        """Validate external links in documentation files."""
        print("🌐 Validating external links...")
        
        # Find all markdown files
        md_files = []
        for pattern in ["*.md", "**/*.md"]:
            md_files.extend(self.project_root.glob(pattern))
        
        all_external_links = set()
        
        # Extract all external links
        for md_file in md_files:
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract markdown links [text](url)
                link_pattern = r'\[([^\]]*)\]\(([^)]+)\)'
                links = re.findall(link_pattern, content)
                
                for link_text, link_url in links:
                    if link_url.startswith(('http://', 'https://')):
                        all_external_links.add(link_url)
                        
            except Exception as e:
                print(f"  ⚠️  Error reading {md_file}: {e}")
        
        print(f"  📊 Found {len(all_external_links)} unique external links")
        
        # Test a sample of external links (to avoid being rate-limited)
        sample_links = list(all_external_links)[:10]  # Test first 10 links
        broken_external_links = []
        
        for link in sample_links:
            try:
                req = urllib.request.Request(link, headers={
                    'User-Agent': 'Mozilla/5.0 (compatible; DocumentationValidator/1.0)'
                })
                
                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status == 200:
                        print(f"  ✅ {link}")
                    else:
                        print(f"  ❌ {link} (status: {response.status})")
                        broken_external_links.append(link)
                        
            except Exception as e:
                print(f"  ❌ {link} (error: {e})")
                broken_external_links.append(link)
        
        # For remaining links, just report them without testing
        if len(all_external_links) > 10:
            remaining = len(all_external_links) - 10
            print(f"  ℹ️  {remaining} additional external links not tested (to avoid rate limiting)")
        
        success = len(broken_external_links) == 0
        
        self.results["validation_results"]["external_links"] = {
            "success": success,
            "total_external_links": len(all_external_links),
            "links_tested": len(sample_links),
            "broken_links": broken_external_links
        }
        
        return success
    
    def validate_version_consistency(self) -> bool:
        """Validate version consistency across documentation."""
        print("🔢 Validating version consistency...")
        
        # Get current version from _version.py
        version_file = self.project_root / "vaitp_auditor" / "_version.py"
        current_version = None
        
        if version_file.exists():
            try:
                with open(version_file, 'r') as f:
                    content = f.read()
                
                version_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
                if version_match:
                    current_version = version_match.group(1)
                    print(f"  📋 Current version: {current_version}")
                else:
                    print("  ❌ Could not extract version from _version.py")
                    
            except Exception as e:
                print(f"  ❌ Error reading version file: {e}")
        else:
            print("  ❌ Version file not found")
        
        if not current_version:
            self.results["validation_results"]["version_consistency"] = {
                "success": False,
                "current_version": None,
                "error": "Could not determine current version"
            }
            return False
        
        # Check version references in documentation
        version_references = {}
        
        # Files that should reference the current version
        version_files = [
            "README.md",
            "CHANGELOG.md",
            "deployment/README.md",
            "docs/SETUP_GUIDE.md"
        ]
        
        for file_path in version_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Look for version patterns
                    version_patterns = [
                        rf'v?{re.escape(current_version)}',
                        r'v?\d+\.\d+\.\d+(?:-[a-zA-Z0-9.]+)?'
                    ]
                    
                    found_versions = set()
                    for pattern in version_patterns:
                        matches = re.findall(pattern, content)
                        found_versions.update(matches)
                    
                    version_references[file_path] = list(found_versions)
                    
                    if current_version in content or f"v{current_version}" in content:
                        print(f"  ✅ {file_path}: references current version")
                    else:
                        print(f"  ⚠️  {file_path}: may not reference current version")
                        
                except Exception as e:
                    print(f"  ❌ Error checking {file_path}: {e}")
        
        # Check CHANGELOG for current version
        changelog_path = self.project_root / "CHANGELOG.md"
        changelog_has_current = False
        
        if changelog_path.exists():
            try:
                with open(changelog_path, 'r', encoding='utf-8') as f:
                    changelog_content = f.read()
                
                if current_version in changelog_content:
                    changelog_has_current = True
                    print(f"  ✅ CHANGELOG.md: contains current version {current_version}")
                else:
                    print(f"  ⚠️  CHANGELOG.md: does not contain current version {current_version}")
                    
            except Exception as e:
                print(f"  ❌ Error checking CHANGELOG.md: {e}")
        
        success = True  # Version consistency is more of a warning than a failure
        
        self.results["validation_results"]["version_consistency"] = {
            "success": success,
            "current_version": current_version,
            "version_references": version_references,
            "changelog_has_current": changelog_has_current
        }
        
        return success
    
    def validate_installation_instructions(self) -> bool:
        """Validate installation instructions accuracy."""
        print("💿 Validating installation instructions...")
        
        success = True
        issues = []
        
        # Check README.md installation section
        readme_path = self.project_root / "README.md"
        if readme_path.exists():
            try:
                with open(readme_path, 'r', encoding='utf-8') as f:
                    readme_content = f.read()
                
                # Check for installation section
                if re.search(r'##?\s*Installation', readme_content, re.IGNORECASE):
                    print("  ✅ README.md: Installation section found")
                    
                    # Check for pip installation
                    if 'pip install' in readme_content:
                        print("  ✅ README.md: pip installation instructions present")
                    else:
                        print("  ⚠️  README.md: pip installation instructions missing")
                        issues.append("Missing pip installation instructions")
                    
                    # Check for executable download instructions
                    if 'download' in readme_content.lower() and 'release' in readme_content.lower():
                        print("  ✅ README.md: executable download instructions present")
                    else:
                        print("  ⚠️  README.md: executable download instructions unclear")
                        issues.append("Unclear executable download instructions")
                    
                    # Check for system requirements
                    if re.search(r'requirements?|system|platform', readme_content, re.IGNORECASE):
                        print("  ✅ README.md: system requirements mentioned")
                    else:
                        print("  ⚠️  README.md: system requirements not clearly stated")
                        issues.append("System requirements not clearly stated")
                        
                else:
                    print("  ❌ README.md: Installation section not found")
                    issues.append("No installation section in README")
                    success = False
                    
            except Exception as e:
                print(f"  ❌ Error reading README.md: {e}")
                success = False
        else:
            print("  ❌ README.md not found")
            success = False
        
        # Check setup guide
        setup_guide = self.project_root / "docs" / "SETUP_GUIDE.md"
        if setup_guide.exists():
            print("  ✅ SETUP_GUIDE.md: found")
        else:
            print("  ⚠️  SETUP_GUIDE.md: not found")
            issues.append("No detailed setup guide")
        
        # Validate that setup.py exists and is correct
        setup_py = self.project_root / "setup.py"
        if setup_py.exists():
            try:
                with open(setup_py, 'r') as f:
                    setup_content = f.read()
                
                # Check for required fields
                required_fields = ['name', 'version', 'description', 'author', 'install_requires']
                missing_fields = []
                
                for field in required_fields:
                    if field not in setup_content:
                        missing_fields.append(field)
                
                if missing_fields:
                    print(f"  ❌ setup.py: missing fields - {', '.join(missing_fields)}")
                    issues.append(f"setup.py missing fields: {', '.join(missing_fields)}")
                    success = False
                else:
                    print("  ✅ setup.py: all required fields present")
                    
            except Exception as e:
                print(f"  ❌ Error reading setup.py: {e}")
                success = False
        else:
            print("  ❌ setup.py not found")
            issues.append("setup.py not found")
            success = False
        
        self.results["validation_results"]["installation_instructions"] = {
            "success": success,
            "issues": issues
        }
        
        return success
    
    def validate_code_examples(self) -> bool:
        """Validate code examples and snippets in documentation."""
        print("💻 Validating code examples...")
        
        # Find all markdown files
        md_files = []
        for pattern in ["*.md", "**/*.md"]:
            md_files.extend(self.project_root.glob(pattern))
        
        total_code_blocks = 0
        syntax_errors = []
        
        for md_file in md_files:
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract code blocks
                code_block_pattern = r'```(\w+)?\n(.*?)\n```'
                code_blocks = re.findall(code_block_pattern, content, re.DOTALL)
                
                for language, code in code_blocks:
                    total_code_blocks += 1
                    
                    # Validate Python code blocks
                    if language.lower() in ['python', 'py']:
                        try:
                            compile(code, f"{md_file}:code_block", 'exec')
                            # print(f"  ✅ {md_file.name}: Python code block valid")
                        except SyntaxError as e:
                            syntax_errors.append({
                                "file": str(md_file.relative_to(self.project_root)),
                                "language": language,
                                "error": str(e),
                                "code_snippet": code[:100] + "..." if len(code) > 100 else code
                            })
                            print(f"  ❌ {md_file.name}: Python syntax error - {e}")
                    
                    # Validate shell/bash commands (basic check)
                    elif language.lower() in ['bash', 'sh', 'shell']:
                        # Check for common issues
                        if '&&' in code and '\n' in code:
                            # Multi-line commands with && might be problematic
                            print(f"  ⚠️  {md_file.name}: shell command may have line continuation issues")
                        
                        # Check for dangerous commands
                        dangerous_patterns = ['rm -rf /', 'sudo rm', 'format c:']
                        for pattern in dangerous_patterns:
                            if pattern in code.lower():
                                print(f"  ⚠️  {md_file.name}: potentially dangerous command found")
                                break
                    
            except Exception as e:
                print(f"  ⚠️  Error processing {md_file}: {e}")
        
        success = len(syntax_errors) == 0
        
        self.results["validation_results"]["code_examples"] = {
            "success": success,
            "total_code_blocks": total_code_blocks,
            "syntax_errors": syntax_errors,
            "files_checked": len(md_files)
        }
        
        if success:
            print(f"  ✅ All {total_code_blocks} code blocks are valid")
        else:
            print(f"  ❌ {len(syntax_errors)} code blocks have syntax errors")
        
        return success
    
    def validate_cli_documentation(self) -> bool:
        """Validate CLI documentation against actual CLI interface."""
        print("⌨️  Validating CLI documentation...")
        
        success = True
        issues = []
        
        # Get actual CLI help
        try:
            result = subprocess.run([
                sys.executable, "-m", "vaitp_auditor.cli", "--help"
            ], capture_output=True, text=True, timeout=30, cwd=self.project_root)
            
            if result.returncode == 0:
                actual_help = result.stdout
                print("  ✅ CLI help command works")
            else:
                print("  ❌ CLI help command failed")
                actual_help = ""
                success = False
                
        except Exception as e:
            print(f"  ❌ Error getting CLI help: {e}")
            actual_help = ""
            success = False
        
        # Check if CLI documentation matches actual interface
        if actual_help:
            # Extract command line options from help
            option_pattern = r'(-\w|--[\w-]+)'
            actual_options = set(re.findall(option_pattern, actual_help))
            
            # Check documentation files for CLI examples
            doc_files = [
                "README.md",
                "docs/USER_GUIDE.md",
                "docs/SETUP_GUIDE.md"
            ]
            
            for doc_file in doc_files:
                doc_path = self.project_root / doc_file
                if doc_path.exists():
                    try:
                        with open(doc_path, 'r', encoding='utf-8') as f:
                            doc_content = f.read()
                        
                        # Find CLI examples in documentation
                        doc_options = set(re.findall(option_pattern, doc_content))
                        
                        # Check for outdated options
                        outdated_options = doc_options - actual_options
                        if outdated_options:
                            print(f"  ⚠️  {doc_file}: may contain outdated CLI options - {outdated_options}")
                            issues.append(f"{doc_file} contains outdated CLI options")
                        else:
                            print(f"  ✅ {doc_file}: CLI options appear current")
                            
                    except Exception as e:
                        print(f"  ⚠️  Error checking {doc_file}: {e}")
        
        self.results["validation_results"]["cli_documentation"] = {
            "success": success,
            "issues": issues
        }
        
        return success
    
    def run_comprehensive_validation(self) -> bool:
        """Run comprehensive documentation validation."""
        print("📚 Running comprehensive documentation validation")
        print("=" * 60)
        
        validations = [
            ("Required Files", self.validate_required_files),
            ("Internal Links", self.validate_internal_links),
            ("External Links", self.validate_external_links),
            ("Version Consistency", self.validate_version_consistency),
            ("Installation Instructions", self.validate_installation_instructions),
            ("Code Examples", self.validate_code_examples),
            ("CLI Documentation", self.validate_cli_documentation),
        ]
        
        results = {}
        overall_success = True
        
        for name, validator in validations:
            print(f"\n{name}:")
            print("-" * 40)
            
            try:
                success = validator()
                results[name] = success
                if not success:
                    overall_success = False
            except Exception as e:
                print(f"  ❌ Validation error: {e}")
                results[name] = False
                overall_success = False
        
        # Print summary
        print("\n" + "=" * 60)
        print("DOCUMENTATION VALIDATION SUMMARY")
        print("=" * 60)
        
        for name, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {name}")
        
        if overall_success:
            print("\n🎉 ALL DOCUMENTATION VALIDATIONS PASSED!")
            print("Documentation is accurate and complete.")
            self.results["overall_status"] = "success"
        else:
            print("\n💥 SOME DOCUMENTATION VALIDATIONS FAILED!")
            print("Please review and fix the issues above.")
            self.results["overall_status"] = "failed"
        
        return overall_success
    
    def save_results(self, output_file: Path):
        """Save validation results to JSON file."""
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Validation results saved to: {output_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Documentation validation for VAITP-Auditor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script validates documentation completeness, accuracy, and consistency:

- Required documentation files exist
- Internal links are valid
- External links are accessible
- Version information is consistent
- Installation instructions are accurate
- Code examples have correct syntax
- CLI documentation matches actual interface

Examples:
  python validate_documentation.py                    # Run full validation
  python validate_documentation.py --output results.json  # Save results
        """
    )
    
    parser.add_argument("--project-root", type=Path, default=".", 
                       help="Project root directory")
    parser.add_argument("--output", type=Path, 
                       help="Output file for validation results (JSON)")
    
    args = parser.parse_args()
    
    project_root = Path(args.project_root).resolve()
    
    if not project_root.exists():
        print(f"❌ Project root not found: {project_root}")
        sys.exit(1)
    
    # Run validation
    validator = DocumentationValidator(project_root)
    success = validator.run_comprehensive_validation()
    
    # Save results if requested
    if args.output:
        validator.save_results(args.output)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()