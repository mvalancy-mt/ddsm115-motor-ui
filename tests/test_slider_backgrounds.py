#!/usr/bin/env python3
"""
Test colored backgrounds behind sliders
"""

import tkinter as tk
from tkinter import ttk

def test_slider_backgrounds():
    """Test colored background approach"""
    root = tk.Tk()
    root.title("Slider Background Test")
    root.geometry("600x400")
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
    
    style.configure('TFrame', 
                   background='#2b2b2b')
    style.configure('TLabelFrame', 
                   background='#2b2b2b',
                   foreground='#e0e0e0')
    style.configure('TLabel',
                   background='#2b2b2b',
                   foreground='#e0e0e0')
    
    # Clean slider style
    style.configure('Touch.Horizontal.TScale', 
                   sliderthickness=28,
                   background='#2b2b2b',
                   troughcolor='#3c3c3c',
                   borderwidth=0,
                   lightcolor='#5a5a5a',
                   darkcolor='#5a5a5a')
    
    # Main frame
    main_frame = ttk.Frame(root)
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    ttk.Label(main_frame, text="Sliders with Color Backgrounds", 
             font=('Arial', 14, 'bold')).pack(pady=15)
    
    # Velocity control with blue background
    vel_frame = ttk.LabelFrame(main_frame, text="Velocity Control", padding=5)
    vel_frame.pack(fill="x", pady=5)
    
    ttk.Label(vel_frame, text="Speed (RPM):").pack()
    
    vel_row = ttk.Frame(vel_frame)
    vel_row.pack(fill="x", pady=5)
    
    # Blue background (darker blue that matches graph)
    vel_bg = tk.Frame(vel_row, bg="#3a5f9f", height=35)
    vel_bg.pack(side="left", fill="x", expand=True, padx=(0, 5))
    
    vel_var = tk.DoubleVar(value=50)
    vel_scale = ttk.Scale(vel_bg, from_=-143, to=143, variable=vel_var, 
                         orient="horizontal", style='Touch.Horizontal.TScale')
    vel_scale.pack(fill="x", padx=5, pady=5)
    
    vel_entry = ttk.Entry(vel_row, textvariable=vel_var, width=6)
    vel_entry.pack(side="right")
    
    # Position control with red background
    pos_frame = ttk.LabelFrame(main_frame, text="Position Control", padding=5)
    pos_frame.pack(fill="x", pady=5)
    
    ttk.Label(pos_frame, text="Position (°):").pack()
    
    pos_row = ttk.Frame(pos_frame)
    pos_row.pack(fill="x", pady=5)
    
    # Red background (darker red that matches graph)
    pos_bg = tk.Frame(pos_row, bg="#9f3a3a", height=35)
    pos_bg.pack(side="left", fill="x", expand=True, padx=(0, 5))
    
    pos_var = tk.DoubleVar(value=180)
    pos_scale = ttk.Scale(pos_bg, from_=0, to=360, variable=pos_var, 
                         orient="horizontal", style='Touch.Horizontal.TScale')
    pos_scale.pack(fill="x", padx=5, pady=5)
    
    pos_entry = ttk.Entry(pos_row, textvariable=pos_var, width=6)
    pos_entry.pack(side="right")
    
    # Current control with green background
    curr_frame = ttk.LabelFrame(main_frame, text="Current Control", padding=5)
    curr_frame.pack(fill="x", pady=5)
    
    ttk.Label(curr_frame, text="Current (A):").pack()
    
    curr_row = ttk.Frame(curr_frame)
    curr_row.pack(fill="x", pady=5)
    
    # Green background (darker green that matches graph)
    curr_bg = tk.Frame(curr_row, bg="#3a9f6b", height=35)
    curr_bg.pack(side="left", fill="x", expand=True, padx=(0, 5))
    
    curr_var = tk.DoubleVar(value=4)
    curr_scale = ttk.Scale(curr_bg, from_=-8, to=8, variable=curr_var, 
                          orient="horizontal", style='Touch.Horizontal.TScale')
    curr_scale.pack(fill="x", padx=5, pady=5)
    
    curr_entry = ttk.Entry(curr_row, textvariable=curr_var, width=6)
    curr_entry.pack(side="right")
    
    # Instructions
    instructions = ttk.Label(main_frame, 
                           text="Each slider sits on a colored background\\n" +
                                "that matches the graph line color.\\n" +
                                "Clean, subtle, and clearly connected to the graph.",
                           justify="center")
    instructions.pack(pady=20)
    
    # Close button
    ttk.Button(main_frame, text="Excellent!", command=root.quit).pack(pady=10)
    
    print("Slider background test opened")
    print("Check that the colored backgrounds clearly show the connection to graph lines")
    
    root.mainloop()

if __name__ == "__main__":
    test_slider_backgrounds()