#!/usr/bin/env python3
"""
Test subtle color-coded slider handles
"""

import tkinter as tk
from tkinter import ttk

def test_subtle_colors():
    """Test the subtle color approach"""
    root = tk.Tk()
    root.title("Subtle Slider Colors Test")
    root.geometry("500x400")
    root.configure(bg='#2b2b2b')
    
    # Configure dark theme
    style = ttk.Style()
    style.theme_use('alt')
    
    # Base dark theme
    style.configure('.', 
                   background='#2b2b2b',
                   foreground='#e0e0e0',
                   fieldbackground='#3c3c3c',
                   selectbackground='#4a9eff',
                   selectforeground='#ffffff',
                   borderwidth=0,
                   relief='flat')
    
    # Subtle color-coded slider styles (only handle gets color)
    # Velocity slider (subtle blue handle)
    style.configure('Velocity.Horizontal.TScale', 
                   sliderthickness=28,
                   background='#2b2b2b',
                   troughcolor='#3c3c3c',
                   borderwidth=0,
                   lightcolor='#3c3c3c',
                   darkcolor='#3c3c3c')
    style.map('Velocity.Horizontal.TScale',
             slidercolor=[('', '#6ba3ff')])  # Subtle blue for handle only
    
    # Position slider (subtle red handle)
    style.configure('Position.Horizontal.TScale', 
                   sliderthickness=28,
                   background='#2b2b2b',
                   troughcolor='#3c3c3c',
                   borderwidth=0,
                   lightcolor='#3c3c3c',
                   darkcolor='#3c3c3c')
    style.map('Position.Horizontal.TScale',
             slidercolor=[('', '#ff8a8a')])  # Subtle red for handle only
    
    # Current slider (subtle green handle)
    style.configure('Current.Horizontal.TScale', 
                   sliderthickness=28,
                   background='#2b2b2b',
                   troughcolor='#3c3c3c',
                   borderwidth=0,
                   lightcolor='#3c3c3c',
                   darkcolor='#3c3c3c')
    style.map('Current.Horizontal.TScale',
             slidercolor=[('', '#8affb3')])  # Subtle green for handle only
    
    # Test frame
    main_frame = ttk.Frame(root)
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    ttk.Label(main_frame, text="Subtle Color-Coded Slider Handles", 
             font=('Arial', 14, 'bold')).pack(pady=15)
    
    # Velocity slider (blue handle)
    ttk.Label(main_frame, text="Velocity Control (Blue Handle):").pack(anchor="w", pady=(10, 2))
    vel_var = tk.DoubleVar(value=50)
    ttk.Scale(main_frame, from_=-143, to=143, variable=vel_var, 
             orient="horizontal", style='Velocity.Horizontal.TScale').pack(fill="x", pady=5)
    
    # Position slider (red handle)  
    ttk.Label(main_frame, text="Position Control (Red Handle):").pack(anchor="w", pady=(15, 2))
    pos_var = tk.DoubleVar(value=180)
    ttk.Scale(main_frame, from_=0, to=360, variable=pos_var, 
             orient="horizontal", style='Position.Horizontal.TScale').pack(fill="x", pady=5)
    
    # Current slider (green handle)
    ttk.Label(main_frame, text="Current Control (Green Handle):").pack(anchor="w", pady=(15, 2))
    curr_var = tk.DoubleVar(value=4)
    ttk.Scale(main_frame, from_=-8, to=8, variable=curr_var, 
             orient="horizontal", style='Current.Horizontal.TScale').pack(fill="x", pady=5)
    
    # Instructions
    instructions = ttk.Label(main_frame, 
                           text="The slider handles should have subtle colors\\n" +
                                "that match the graph line colors but are not overwhelming.\\n" +
                                "The trough (track) should remain neutral gray.",
                           justify="center")
    instructions.pack(pady=30)
    
    # Close button
    ttk.Button(main_frame, text="Looks Good!", command=root.quit).pack(pady=10)
    
    print("Subtle color test opened")
    print("Check that only the slider handles have color, not the entire track")
    
    root.mainloop()

if __name__ == "__main__":
    test_subtle_colors()