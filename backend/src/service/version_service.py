"""
Strategy Version Service - Business logic for strategy version management.

This module provides diff generation and comparison utilities using
Python's difflib for unified diff format.
"""

import difflib
import hashlib
from typing import Optional


def compute_code_hash(code: str) -> str:
    """Compute SHA-256 hash of code for change detection."""
    return hashlib.sha256(code.encode('utf-8')).hexdigest()


def generate_unified_diff(old_code: str, new_code: str,
                          old_label: str = "previous",
                          new_label: str = "current") -> str:
    """
    Generate unified diff between two code versions.
    
    Args:
        old_code: Previous version of the code
        new_code: New version of the code  
        old_label: Label for the old version in diff header
        new_label: Label for the new version in diff header
        
    Returns:
        Unified diff as a string
    """
    old_lines = old_code.splitlines(keepends=True)
    new_lines = new_code.splitlines(keepends=True)
    
    # Ensure lines end with newline for proper diff output
    if old_lines and not old_lines[-1].endswith('\n'):
        old_lines[-1] += '\n'
    if new_lines and not new_lines[-1].endswith('\n'):
        new_lines[-1] += '\n'
    
    diff = difflib.unified_diff(
        old_lines, 
        new_lines,
        fromfile=old_label,
        tofile=new_label,
        lineterm=''
    )
    
    return ''.join(diff)


def generate_side_by_side_diff(old_code: str, new_code: str) -> list[dict]:
    """
    Generate side-by-side diff for Monaco editor display.
    
    Args:
        old_code: Previous version of the code
        new_code: New version of the code
        
    Returns:
        List of diff hunks with line numbers and change types
    """
    old_lines = old_code.splitlines()
    new_lines = new_code.splitlines()
    
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
    
    hunks = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            for i, j in zip(range(i1, i2), range(j1, j2)):
                hunks.append({
                    'type': 'equal',
                    'old_line_num': i + 1,
                    'new_line_num': j + 1,
                    'old_content': old_lines[i],
                    'new_content': new_lines[j]
                })
        elif tag == 'delete':
            for i in range(i1, i2):
                hunks.append({
                    'type': 'delete',
                    'old_line_num': i + 1,
                    'new_line_num': None,
                    'old_content': old_lines[i],
                    'new_content': None
                })
        elif tag == 'insert':
            for j in range(j1, j2):
                hunks.append({
                    'type': 'insert',
                    'old_line_num': None,
                    'new_line_num': j + 1,
                    'old_content': None,
                    'new_content': new_lines[j]
                })
        elif tag == 'replace':
            # Handle replacements as paired deletes and inserts
            max_len = max(i2 - i1, j2 - j1)
            for k in range(max_len):
                old_idx = i1 + k if k < (i2 - i1) else None
                new_idx = j1 + k if k < (j2 - j1) else None
                hunks.append({
                    'type': 'replace',
                    'old_line_num': old_idx + 1 if old_idx is not None else None,
                    'new_line_num': new_idx + 1 if new_idx is not None else None,
                    'old_content': old_lines[old_idx] if old_idx is not None else None,
                    'new_content': new_lines[new_idx] if new_idx is not None else None
                })
    
    return hunks


def count_changes(old_code: str, new_code: str) -> dict:
    """
    Count the number of changes between two code versions.
    
    Args:
        old_code: Previous version of the code
        new_code: New version of the code
        
    Returns:
        dict with lines_added, lines_removed, and lines_modified counts
    """
    old_lines = old_code.splitlines() if old_code else []
    new_lines = new_code.splitlines()
    
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
    
    lines_added = 0
    lines_removed = 0
    lines_modified = 0
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'insert':
            lines_added += j2 - j1
        elif tag == 'delete':
            lines_removed += i2 - i1
        elif tag == 'replace':
            lines_modified += max(i2 - i1, j2 - j1)
    
    return {
        'lines_added': lines_added,
        'lines_removed': lines_removed,
        'lines_modified': lines_modified,
        'total_changes': lines_added + lines_removed + lines_modified
    }


def compare_versions(old_code: str, new_code: str,
                     old_version: int, new_version: int) -> dict:
    """
    Compare two versions and return comprehensive diff information.
    
    Args:
        old_code: Code from the older version
        new_code: Code from the newer version
        old_version: Version number of the old code
        new_version: Version number of the new code
        
    Returns:
        dict with unified diff, change counts, and version info
    """
    unified_diff = generate_unified_diff(
        old_code, 
        new_code,
        old_label=f"version_{old_version}",
        new_label=f"version_{new_version}"
    )
    
    changes = count_changes(old_code, new_code)
    
    return {
        'from_version': old_version,
        'to_version': new_version,
        'unified_diff': unified_diff,
        'old_code': old_code,
        'new_code': new_code,
        **changes
    }
