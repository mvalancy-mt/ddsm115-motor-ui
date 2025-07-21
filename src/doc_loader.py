#!/usr/bin/env python3
"""
Documentation Loader for DDSM115 Motor Control GUI
Loads markdown documentation files and converts them for tkinter display
"""

import os
import re
from pathlib import Path
from typing import Dict, Optional


class DocumentationLoader:
    """Loads and processes markdown documentation files"""
    
    def __init__(self, docs_dir: Optional[str] = None):
        """Initialize documentation loader
        
        Args:
            docs_dir: Path to documentation directory. If None, auto-detects.
        """
        if docs_dir is None:
            # Auto-detect docs directory relative to this file
            current_dir = Path(__file__).parent
            self.docs_dir = current_dir.parent / "docs"
        else:
            self.docs_dir = Path(docs_dir)
        
        # Cache for loaded documents
        self._cache: Dict[str, str] = {}
        
        # Document files mapping
        self.doc_files = {
            "motor_art": "motor_art.md",
            "system_info": "system_info.md", 
            "operation_guide": "operation_guide.md",
            "api_reference": "api_reference.md",
            "troubleshooting": "troubleshooting.md"
        }
    
    def load_document(self, doc_name: str, use_cache: bool = True) -> str:
        """Load a documentation file
        
        Args:
            doc_name: Name of document (key from doc_files)
            use_cache: Whether to use cached version if available
            
        Returns:
            Processed document content as string
        """
        if use_cache and doc_name in self._cache:
            return self._cache[doc_name]
        
        if doc_name not in self.doc_files:
            return f"❌ Document '{doc_name}' not found.\n\nAvailable documents: {', '.join(self.doc_files.keys())}"
        
        file_path = self.docs_dir / self.doc_files[doc_name]
        
        try:
            if not file_path.exists():
                return f"❌ Documentation file not found: {file_path}\n\nPlease ensure the docs directory contains the required markdown files."
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Process markdown for tkinter display
            processed_content = self._process_markdown(content)
            
            # Cache the result
            if use_cache:
                self._cache[doc_name] = processed_content
            
            return processed_content
            
        except Exception as e:
            return f"❌ Error loading documentation: {e}\n\nFile: {file_path}"
    
    def _process_markdown(self, content: str) -> str:
        """Process markdown content for tkinter text widget display
        
        Args:
            content: Raw markdown content
            
        Returns:
            Processed content suitable for tkinter Text widget
        """
        # Remove markdown syntax while preserving structure
        processed = content
        
        # Convert headers (keep structure but remove markdown)
        processed = re.sub(r'^### (.*)', r'▪ \1', processed, flags=re.MULTILINE)
        processed = re.sub(r'^## (.*)', r'◆ \1', processed, flags=re.MULTILINE)
        processed = re.sub(r'^# (.*)', r'█ \1', processed, flags=re.MULTILINE)
        
        # Convert bold text
        processed = re.sub(r'\*\*(.*?)\*\*', r'\1', processed)
        
        # Convert code blocks (preserve monospace appearance)
        processed = re.sub(r'```.*?\n(.*?)```', r'\1', processed, flags=re.DOTALL)
        processed = re.sub(r'`(.*?)`', r'[\1]', processed)
        
        # Convert links (keep text, note URL)
        processed = re.sub(r'\[(.*?)\]\((.*?)\)', r'\1 (→ \2)', processed)
        
        # Convert lists
        processed = re.sub(r'^- (.*)', r'  • \1', processed, flags=re.MULTILINE)
        processed = re.sub(r'^\d+\. (.*)', r'  \1', processed, flags=re.MULTILINE)
        
        # Convert tables (enhanced formatting with proper borders)
        lines = processed.split('\n')
        table_lines = []
        in_table = False
        table_rows = []
        
        for line in lines:
            if '|' in line and line.strip().startswith('|'):
                if not in_table:
                    in_table = True
                    table_rows = []
                
                # Clean up table formatting
                cleaned = line.strip('|').strip()
                if not cleaned.startswith('-') and cleaned:  # Skip separator lines and empty lines
                    cells = [cell.strip() for cell in cleaned.split('|')]
                    if cells and any(cell.strip() for cell in cells):  # Only add non-empty rows
                        table_rows.append(cells)
            else:
                if in_table:
                    # Process the collected table
                    if table_rows:
                        # Calculate column widths (accounting for Unicode display width)
                        max_widths = []
                        for row in table_rows:
                            for i, cell in enumerate(row):
                                if i >= len(max_widths):
                                    max_widths.append(0)
                                # Use visual width accounting for Unicode characters
                                visual_width = self._get_visual_width(cell)
                                max_widths[i] = max(max_widths[i], visual_width)
                        
                        # Create table with borders
                        table_width = sum(max_widths) + len(max_widths) * 3 + 1
                        
                        # Top border
                        table_lines.append('┌' + '─' * (table_width - 2) + '┐')
                        
                        # Table rows
                        for row_idx, row in enumerate(table_rows):
                            row_text = '│'
                            for i, cell in enumerate(row):
                                if i < len(max_widths):
                                    # Pad considering visual width
                                    visual_width = self._get_visual_width(cell)
                                    padding_needed = max_widths[i] - visual_width
                                    padded_cell = cell + ' ' * padding_needed
                                    row_text += f' {padded_cell} │'
                            table_lines.append(row_text)
                            
                            # Add separator after header row
                            if row_idx == 0 and len(table_rows) > 1:
                                sep_line = '├'
                                for i, width in enumerate(max_widths):
                                    sep_line += '─' * (width + 2)
                                    if i < len(max_widths) - 1:
                                        sep_line += '┼'
                                    else:
                                        sep_line += '┤'
                                table_lines.append(sep_line)
                        
                        # Bottom border
                        table_lines.append('└' + '─' * (table_width - 2) + '┘')
                    
                    in_table = False
                    table_rows = []
                
                table_lines.append(line)
        
        # Handle table at end of file
        if in_table and table_rows:
            # Calculate column widths (accounting for Unicode display width)
            max_widths = []
            for row in table_rows:
                for i, cell in enumerate(row):
                    if i >= len(max_widths):
                        max_widths.append(0)
                    # Use visual width accounting for Unicode characters
                    visual_width = self._get_visual_width(cell)
                    max_widths[i] = max(max_widths[i], visual_width)
            
            # Create table with borders
            table_width = sum(max_widths) + len(max_widths) * 3 + 1
            
            # Top border
            table_lines.append('┌' + '─' * (table_width - 2) + '┐')
            
            # Table rows
            for row_idx, row in enumerate(table_rows):
                row_text = '│'
                for i, cell in enumerate(row):
                    if i < len(max_widths):
                        # Pad considering visual width
                        visual_width = self._get_visual_width(cell)
                        padding_needed = max_widths[i] - visual_width
                        padded_cell = cell + ' ' * padding_needed
                        row_text += f' {padded_cell} │'
                table_lines.append(row_text)
                
                # Add separator after header row
                if row_idx == 0 and len(table_rows) > 1:
                    sep_line = '├'
                    for i, width in enumerate(max_widths):
                        sep_line += '─' * (width + 2)
                        if i < len(max_widths) - 1:
                            sep_line += '┼'
                        else:
                            sep_line += '┤'
                    table_lines.append(sep_line)
            
            # Bottom border
            table_lines.append('└' + '─' * (table_width - 2) + '┘')
        
        processed = '\n'.join(table_lines)
        
        # Clean up extra newlines
        processed = re.sub(r'\n{3,}', r'\n\n', processed)
        
        return processed.strip()
    
    def _get_visual_width(self, text: str) -> int:
        """Calculate the visual width of text, accounting for Unicode characters
        
        Args:
            text: The text to measure
            
        Returns:
            Visual width of the text
        """
        # For monospace fonts, most Unicode characters take up the same space as ASCII
        # But some specific characters may display differently
        
        # Simple approach: treat most common Unicode symbols as single width
        # but account for common issues with specific characters
        width = 0
        for char in text:
            if ord(char) < 128:  # ASCII characters
                width += 1
            elif char in '±≤≥℃°×÷':  # Common symbols that might display wider
                width += 1  # Treat as single width for monospace
            else:
                width += 1  # Default to single width for other Unicode
        
        return width
    
    def get_available_docs(self) -> Dict[str, str]:
        """Get list of available documentation files
        
        Returns:
            Dictionary mapping doc names to file paths
        """
        available = {}
        for name, filename in self.doc_files.items():
            file_path = self.docs_dir / filename
            if file_path.exists():
                available[name] = str(file_path)
        return available
    
    def reload_cache(self):
        """Clear cache and reload all documents"""
        self._cache.clear()
        for doc_name in self.doc_files.keys():
            self.load_document(doc_name, use_cache=True)


# Convenience functions for GUI integration
def load_motor_art() -> str:
    """Load motor art documentation"""
    loader = DocumentationLoader()
    return loader.load_document("motor_art")


def load_system_info() -> str:
    """Load system information documentation"""
    loader = DocumentationLoader()
    return loader.load_document("system_info")


def load_operation_guide() -> str:
    """Load operation guide documentation"""
    loader = DocumentationLoader()
    return loader.load_document("operation_guide")


def load_api_reference() -> str:
    """Load API reference documentation"""
    loader = DocumentationLoader()
    return loader.load_document("api_reference")


def load_troubleshooting() -> str:
    """Load troubleshooting guide documentation"""
    loader = DocumentationLoader()
    return loader.load_document("troubleshooting")


if __name__ == "__main__":
    # Test the documentation loader
    loader = DocumentationLoader()
    
    print("📋 Available documentation files:")
    for name, path in loader.get_available_docs().items():
        print(f"  ✓ {name}: {path}")
    
    print("\n📖 Testing document loading:")
    for doc_name in loader.doc_files.keys():
        print(f"\n--- {doc_name.upper()} ---")
        content = loader.load_document(doc_name)
        print(content[:200] + "..." if len(content) > 200 else content)