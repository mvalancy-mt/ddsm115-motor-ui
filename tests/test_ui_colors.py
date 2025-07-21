#!/usr/bin/env python3
"""
Test script to verify UI color theming
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

def test_color_theme():
    """Test the color theme styles"""
    root = tk.Tk()
    root.title("Color Theme Test")
    root.geometry("400x300")
    
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
    
    # Color-coded slider styles (matching graph colors)
    # Velocity = Blue (#4a9eff)
    style.configure('Velocity.Horizontal.TScale', 
                   sliderthickness=28,
                   background='#2b2b2b',
                   troughcolor='#1a1a1a',
                   borderwidth=0,
                   lightcolor='#4a9eff',
                   darkcolor='#4a9eff',
                   slidercolor='#4a9eff')
    
    # Position = Red (#ff6b6b) 
    style.configure('Position.Horizontal.TScale', 
                   sliderthickness=28,
                   background='#2b2b2b',
                   troughcolor='#1a1a1a',
                   borderwidth=0,
                   lightcolor='#ff6b6b',
                   darkcolor='#ff6b6b',
                   slidercolor='#ff6b6b')
    
    # Current/Torque = Green (#4ecdc4)
    style.configure('Current.Horizontal.TScale', 
                   sliderthickness=28,
                   background='#2b2b2b',
                   troughcolor='#1a1a1a',
                   borderwidth=0,
                   lightcolor='#4ecdc4',
                   darkcolor='#4ecdc4',
                   slidercolor='#4ecdc4')
    
    # Touch-friendly checkboxes
    style.configure('Touch.TCheckbutton',
                   background='#2b2b2b',
                   foreground='#e0e0e0',
                   focuscolor='none',
                   borderwidth=0,
                   relief='flat')
    
    # Test widgets
    main_frame = ttk.Frame(root)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    ttk.Label(main_frame, text="Color-Coded Sliders Test", 
             font=('Arial', 14, 'bold')).pack(pady=10)
    
    # Velocity slider (blue)
    ttk.Label(main_frame, text="Velocity (Blue):").pack(anchor="w")
    vel_var = tk.DoubleVar(value=50)
    ttk.Scale(main_frame, from_=0, to=100, variable=vel_var, 
             orient="horizontal", style='Velocity.Horizontal.TScale').pack(fill="x", pady=5)
    
    # Position slider (red)
    ttk.Label(main_frame, text="Position (Red):").pack(anchor="w")
    pos_var = tk.DoubleVar(value=180)
    ttk.Scale(main_frame, from_=0, to=360, variable=pos_var, 
             orient="horizontal", style='Position.Horizontal.TScale').pack(fill="x", pady=5)
    
    # Current slider (green)
    ttk.Label(main_frame, text="Current (Green):").pack(anchor="w")
    curr_var = tk.DoubleVar(value=4)
    ttk.Scale(main_frame, from_=-8, to=8, variable=curr_var, 
             orient="horizontal", style='Current.Horizontal.TScale').pack(fill="x", pady=5)
    
    # Test checkboxes
    ttk.Label(main_frame, text="Touch-Friendly Checkboxes:", 
             font=('Arial', 12, 'bold')).pack(anchor="w", pady=(20, 5))
    
    checkbox_frame = ttk.Frame(main_frame)
    checkbox_frame.pack(fill="x")
    
    vel_check = tk.BooleanVar(value=True)
    pos_check = tk.BooleanVar(value=True)
    torque_check = tk.BooleanVar(value=True)
    
    ttk.Checkbutton(checkbox_frame, text="Velocity", variable=vel_check,
                   style='Touch.TCheckbutton').pack(side="left", padx=10)
    ttk.Checkbutton(checkbox_frame, text="Position", variable=pos_check,
                   style='Touch.TCheckbutton').pack(side="left", padx=10)
    ttk.Checkbutton(checkbox_frame, text="Torque", variable=torque_check,
                   style='Touch.TCheckbutton').pack(side="left", padx=10)
    
    # Instructions
    instructions = ttk.Label(main_frame, 
                           text="• Sliders should show colors matching graph lines\n" +
                                "• Checkboxes should be easy to see and touch\n" +
                                "• Dark theme should be consistent",
                           justify="left")
    instructions.pack(anchor="w", pady=20)
    
    # Close button
    ttk.Button(main_frame, text="Close", command=root.quit).pack(pady=10)
    
    print("Color theme test window opened")
    print("Check that:")
    print("1. Velocity slider is blue")
    print("2. Position slider is red") 
    print("3. Current slider is green")
    print("4. Checkboxes are visible and touch-friendly")
    print("5. Dark theme looks consistent")
    
    root.mainloop()

if __name__ == "__main__":
    test_color_theme()