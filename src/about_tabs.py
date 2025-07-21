#!/usr/bin/env python3
"""
About Tabs Module for DDSM115 Motor Control GUI
Modular about tab implementation that loads documentation from external files
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from doc_loader import DocumentationLoader


class AboutTabs:
    """Manages the About tab and its sub-tabs using external documentation"""
    
    def __init__(self, parent_notebook, gui_instance):
        """Initialize About tabs
        
        Args:
            parent_notebook: The main notebook widget to add tabs to
            gui_instance: Reference to main GUI instance for styling methods
        """
        self.parent_notebook = parent_notebook
        self.gui = gui_instance
        self.doc_loader = DocumentationLoader()
        
        # Create main about frame
        self.about_frame = ttk.Frame(self.parent_notebook)
        self.parent_notebook.add(self.about_frame, text="📋 About")
        
        # Create sub-notebook for about sections
        self.about_notebook = ttk.Notebook(self.about_frame)
        self.about_notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create all sub-tabs
        self.create_all_tabs()
    
    def create_all_tabs(self):
        """Create all about sub-tabs"""
        self.create_tab("🎨 Motor Art", "motor_art", monospace=True)
        self.create_tab("ℹ️ System Info", "system_info")
        self.create_tab("📖 Operation Guide", "operation_guide")
        self.create_tab("🔧 API Reference", "api_reference", dark_theme=True)
        self.create_tab("🔍 Troubleshooting", "troubleshooting")
    
    def create_tab(self, tab_title: str, doc_name: str, monospace: bool = False, dark_theme: bool = False):
        """Create a documentation tab
        
        Args:
            tab_title: Display title for the tab
            doc_name: Document name to load from doc_loader
            monospace: Whether to use monospace font
            dark_theme: Whether to use dark theme colors
        """
        # Create tab frame
        tab_frame = ttk.Frame(self.about_notebook)
        self.about_notebook.add(tab_frame, text=tab_title)
        
        # Create scrollable frame
        scroll_frame = ttk.Frame(tab_frame)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create scrollbar
        scrollbar = tk.Scrollbar(scroll_frame)
        scrollbar.pack(side="right", fill="y")
        
        # Configure scrollbar style (reuse GUI instance method if available)
        if hasattr(self.gui, 'configure_wide_scrollbar_direct'):
            self.gui.configure_wide_scrollbar_direct(scrollbar)
        
        # Determine colors and font
        if dark_theme:
            bg_color = '#1e1e1e'
            fg_color = '#d4d4d4'
        elif monospace:
            bg_color = '#1a1a1a'
            fg_color = '#00ff00'
        else:
            bg_color = '#2b2b2b'
            fg_color = '#e0e0e0'
        
        font_family = "Courier" if monospace else "Arial"
        font_size = 8 if monospace else 10
        
        # Create text widget
        text_widget = scrolledtext.ScrolledText(
            scroll_frame,
            font=(font_family, font_size),
            bg=bg_color,
            fg=fg_color,
            insertbackground=fg_color,
            selectbackground='#2a2a2a',
            wrap=tk.WORD,
            padx=10,
            pady=10
        )
        text_widget.pack(side="left", fill="both", expand=True)
        
        # Load and insert content
        try:
            content = self.doc_loader.load_document(doc_name)
            text_widget.insert(tk.END, content)
            text_widget.config(state=tk.DISABLED)  # Make read-only
        except Exception as e:
            error_msg = f"❌ Error loading documentation: {e}\n\nDocument: {doc_name}"
            text_widget.insert(tk.END, error_msg)
            text_widget.config(state=tk.DISABLED)
        
        # Connect scrollbar
        scrollbar.config(command=text_widget.yview)
        text_widget.config(yscrollcommand=scrollbar.set)
    
    def reload_documentation(self):
        """Reload all documentation from files (useful for development)"""
        self.doc_loader.reload_cache()
        
        # Recreate all tabs
        for tab in self.about_notebook.tabs():
            self.about_notebook.forget(tab)
        
        self.create_all_tabs()


def create_about_tab(parent_notebook, gui_instance):
    """Convenience function to create about tabs
    
    Args:
        parent_notebook: The main notebook widget
        gui_instance: Reference to main GUI instance
        
    Returns:
        AboutTabs instance
    """
    return AboutTabs(parent_notebook, gui_instance)


if __name__ == "__main__":
    # Test the about tabs module
    import sys
    sys.path.append('..')
    
    root = tk.Tk()
    root.title("About Tabs Test")
    root.geometry("800x600")
    
    # Create a notebook
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)
    
    # Mock GUI instance with minimal required methods
    class MockGUI:
        def configure_wide_scrollbar_direct(self, scrollbar):
            scrollbar.config(width=20)
    
    mock_gui = MockGUI()
    
    # Create about tabs
    about_tabs = AboutTabs(notebook, mock_gui)
    
    root.mainloop()