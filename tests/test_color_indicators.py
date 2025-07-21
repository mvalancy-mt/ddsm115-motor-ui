#!/usr/bin/env python3
"""
Test color indicators next to sliders
"""

import tkinter as tk
from tkinter import ttk

def test_color_indicators():
    """Test color indicator approach"""
    root = tk.Tk()
    root.title("Color Indicator Test")
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
    
    style.configure('TFrame', 
                   background='#2b2b2b')
    style.configure('TLabelFrame', 
                   background='#2b2b2b',
                   foreground='#e0e0e0')
    style.configure('TLabel',
                   background='#2b2b2b',
                   foreground='#e0e0e0')
    
    # Touch-friendly slider style (no colors, just clean)
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
    
    ttk.Label(main_frame, text="Clean Sliders with Color Indicators", 
             font=('Arial', 14, 'bold')).pack(pady=15)
    
    # Velocity control with blue indicator
    vel_frame = ttk.LabelFrame(main_frame, text="Velocity Control", padding=5)
    vel_frame.pack(fill="x", pady=5)
    
    vel_label_frame = ttk.Frame(vel_frame)
    vel_label_frame.pack(fill="x")
    
    vel_indicator = tk.Label(vel_label_frame, text="●", 
                           fg="#4a9eff", bg="#2b2b2b", 
                           font=('Arial', 14))
    vel_indicator.pack(side="left")
    
    ttk.Label(vel_label_frame, text=" Speed (RPM):").pack(side="left")
    
    vel_var = tk.DoubleVar(value=50)
    ttk.Scale(vel_frame, from_=-143, to=143, variable=vel_var, 
             orient="horizontal", style='Touch.Horizontal.TScale').pack(fill="x", pady=5)
    
    # Position control with red indicator
    pos_frame = ttk.LabelFrame(main_frame, text="Position Control", padding=5)
    pos_frame.pack(fill="x", pady=5)
    
    pos_label_frame = ttk.Frame(pos_frame)
    pos_label_frame.pack(fill="x")
    
    pos_indicator = tk.Label(pos_label_frame, text="●", 
                           fg="#ff6b6b", bg="#2b2b2b", 
                           font=('Arial', 14))
    pos_indicator.pack(side="left")
    
    ttk.Label(pos_label_frame, text=" Position (°):").pack(side="left")
    
    pos_var = tk.DoubleVar(value=180)
    ttk.Scale(pos_frame, from_=0, to=360, variable=pos_var, 
             orient="horizontal", style='Touch.Horizontal.TScale').pack(fill="x", pady=5)
    
    # Current control with green indicator
    curr_frame = ttk.LabelFrame(main_frame, text="Current Control", padding=5)
    curr_frame.pack(fill="x", pady=5)
    
    curr_label_frame = ttk.Frame(curr_frame)
    curr_label_frame.pack(fill="x")
    
    curr_indicator = tk.Label(curr_label_frame, text="●", 
                            fg="#4ecdc4", bg="#2b2b2b", 
                            font=('Arial', 14))
    curr_indicator.pack(side="left")
    
    ttk.Label(curr_label_frame, text=" Current (A):").pack(side="left")
    
    curr_var = tk.DoubleVar(value=4)
    ttk.Scale(curr_frame, from_=-8, to=8, variable=curr_var, 
             orient="horizontal", style='Touch.Horizontal.TScale').pack(fill="x", pady=5)
    
    # Instructions
    instructions = ttk.Label(main_frame, 
                           text="Each slider has a colored dot that matches\\n" +
                                "the corresponding graph line color.\\n" +
                                "Sliders remain clean and touch-friendly.",
                           justify="center")
    instructions.pack(pady=20)
    
    # Close button
    ttk.Button(main_frame, text="Perfect!", command=root.quit).pack(pady=10)
    
    print("Color indicator test opened")
    print("Check that colored dots clearly indicate which slider controls which graph line")
    
    root.mainloop()

if __name__ == "__main__":
    test_color_indicators()