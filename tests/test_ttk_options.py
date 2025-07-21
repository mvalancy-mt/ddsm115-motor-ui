#!/usr/bin/env python3
"""
Test what ttk styling options are available for Scale widgets
"""

import tkinter as tk
from tkinter import ttk

def test_ttk_scale_options():
    """Test available ttk Scale styling options"""
    root = tk.Tk()
    root.title("TTK Scale Options Test")
    root.geometry("600x400")
    
    style = ttk.Style()
    
    # Print available themes
    print("Available themes:", style.theme_names())
    print("Current theme:", style.theme_use())
    
    # Test different themes
    for theme_name in style.theme_names():
        print(f"\n--- Testing theme: {theme_name} ---")
        try:
            style.theme_use(theme_name)
            
            # Get available options for Scale
            scale_options = style.configure('Horizontal.TScale')
            print(f"Scale options: {scale_options}")
            
            # Try to get element options
            try:
                layout = style.layout('Horizontal.TScale')
                print(f"Layout: {layout}")
            except:
                print("Layout not available")
                
        except Exception as e:
            print(f"Error with theme {theme_name}: {e}")
    
    # Reset to default
    style.theme_use('alt')
    
    # Create test frame
    frame = ttk.Frame(root)
    frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    ttk.Label(frame, text="TTK Scale Styling Test", 
              font=('Arial', 14, 'bold')).pack(pady=10)
    
    # Test basic styling options
    test_var = tk.DoubleVar(value=50)
    
    # Try different color approaches
    print("\nTesting color configuration approaches...")
    
    # Approach 1: Configure base style
    try:
        style.configure('Horizontal.TScale', 
                       background='#ff0000',
                       troughcolor='#0000ff',
                       borderwidth=2,
                       relief='solid')
        ttk.Label(frame, text="Test Scale (configured):").pack(anchor="w")
        ttk.Scale(frame, from_=0, to=100, variable=test_var, 
                 orient="horizontal").pack(fill="x", pady=5)
    except Exception as e:
        print(f"Configuration approach failed: {e}")
    
    # Approach 2: Map element states
    try:
        style.map('Horizontal.TScale',
                 background=[('active', '#ff0000'),
                            ('pressed', '#00ff00')])
        ttk.Label(frame, text="Test Scale (mapped):").pack(anchor="w")
        ttk.Scale(frame, from_=0, to=100, variable=test_var, 
                 orient="horizontal").pack(fill="x", pady=5)
    except Exception as e:
        print(f"Mapping approach failed: {e}")
    
    # Show available configure options
    try:
        available_options = style.configure('Horizontal.TScale')
        print(f"Available configuration options: {available_options}")
    except Exception as e:
        print(f"Could not get configuration options: {e}")
    
    ttk.Button(frame, text="Close", command=root.quit).pack(pady=20)
    
    root.mainloop()

if __name__ == "__main__":
    test_ttk_scale_options()