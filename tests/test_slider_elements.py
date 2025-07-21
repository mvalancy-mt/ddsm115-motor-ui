#!/usr/bin/env python3
"""
Test different approaches to color slider handles
"""

import tkinter as tk
from tkinter import ttk

def test_slider_elements():
    """Test different slider coloring approaches"""
    root = tk.Tk()
    root.title("Slider Element Test")
    root.geometry("600x500")
    root.configure(bg='#2b2b2b')
    
    style = ttk.Style()
    
    # Print available themes and test each
    print("Available themes:", style.theme_names())
    
    # Test with different themes
    for theme in ['alt', 'clam', 'classic']:
        if theme in style.theme_names():
            print(f"\\nTesting {theme} theme:")
            try:
                style.theme_use(theme)
                
                # Check what elements are available
                layout = style.layout('Horizontal.TScale')
                print(f"Layout: {layout}")
                
                # Get current configuration
                current_config = style.configure('Horizontal.TScale')
                print(f"Current config: {current_config}")
                
                # Try configuring different elements
                try:
                    style.element_options('Horizontal.Scale.slider')
                    print("Slider element found!")
                except:
                    print("No slider element options")
                
                try:
                    style.element_options('Horizontal.Scale.trough')
                    print("Trough element found!")
                except:
                    print("No trough element options")
                    
            except Exception as e:
                print(f"Error testing {theme}: {e}")
    
    # Use the best theme for dark interface
    style.theme_use('alt')
    
    # Main frame
    main_frame = ttk.Frame(root)
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    ttk.Label(main_frame, text="Slider Element Testing", 
             font=('Arial', 14, 'bold')).pack(pady=10)
    
    # Test approach 1: Element-specific configuration
    print("\\nTrying element-specific configuration...")
    try:
        style.element_create('colored.Scale.slider', 'from', 'alt')
        style.configure('Blue.Horizontal.TScale', 
                       sliderthickness=25,
                       background='#2b2b2b',
                       troughcolor='#3c3c3c')
        style.layout('Blue.Horizontal.TScale',
                   [('Horizontal.Scale.trough',
                     {'children': [('colored.Scale.slider', 
                                   {'side': 'left', 'sticky': ''})],
                      'sticky': 'ew'})])
        
        ttk.Label(main_frame, text="Element-configured slider:").pack(anchor="w")
        test_var1 = tk.DoubleVar(value=50)
        ttk.Scale(main_frame, from_=0, to=100, variable=test_var1, 
                 orient="horizontal", style='Blue.Horizontal.TScale').pack(fill="x", pady=5)
        print("Element approach worked!")
    except Exception as e:
        print(f"Element approach failed: {e}")
    
    # Test approach 2: State mapping
    print("\\nTrying state mapping...")
    try:
        style.configure('Red.Horizontal.TScale', 
                       sliderthickness=25,
                       background='#2b2b2b',
                       troughcolor='#3c3c3c')
        style.map('Red.Horizontal.TScale',
                 background=[('active', '#ff8a8a'),
                            ('pressed', '#ff6b6b'),
                            ('focus', '#ff8a8a')])
        
        ttk.Label(main_frame, text="State-mapped slider:").pack(anchor="w", pady=(10, 0))
        test_var2 = tk.DoubleVar(value=75)
        ttk.Scale(main_frame, from_=0, to=100, variable=test_var2, 
                 orient="horizontal", style='Red.Horizontal.TScale').pack(fill="x", pady=5)
        print("State mapping approach worked!")
    except Exception as e:
        print(f"State mapping failed: {e}")
    
    # Test approach 3: Direct color configuration
    print("\\nTrying direct color configuration...")
    try:
        style.configure('Green.Horizontal.TScale', 
                       sliderthickness=25,
                       background='#2b2b2b',
                       troughcolor='#3c3c3c',
                       lightcolor='#8affb3',
                       darkcolor='#6fdd8f',
                       bordercolor='#8affb3',
                       slidercolor='#8affb3')
        
        ttk.Label(main_frame, text="Direct color slider:").pack(anchor="w", pady=(10, 0))
        test_var3 = tk.DoubleVar(value=25)
        ttk.Scale(main_frame, from_=0, to=100, variable=test_var3, 
                 orient="horizontal", style='Green.Horizontal.TScale').pack(fill="x", pady=5)
        print("Direct color approach worked!")
    except Exception as e:
        print(f"Direct color failed: {e}")
    
    # Test approach 4: Theme override
    print("\\nTrying theme override...")
    try:
        # Override the default slider style
        style.configure('Horizontal.TScale', 
                       sliderthickness=25,
                       background='#2b2b2b',
                       troughcolor='#3c3c3c',
                       borderwidth=1,
                       relief='solid',
                       bordercolor='#6ba3ff')
        
        ttk.Label(main_frame, text="Theme override slider:").pack(anchor="w", pady=(10, 0))
        test_var4 = tk.DoubleVar(value=60)
        ttk.Scale(main_frame, from_=0, to=100, variable=test_var4, 
                 orient="horizontal").pack(fill="x", pady=5)
        print("Theme override worked!")
    except Exception as e:
        print(f"Theme override failed: {e}")
    
    # Close button
    ttk.Button(main_frame, text="Close", command=root.quit).pack(pady=20)
    
    root.mainloop()

if __name__ == "__main__":
    test_slider_elements()