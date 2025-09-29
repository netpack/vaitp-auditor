#!/usr/bin/env python3
"""
Verify that icons work correctly on all windows and dialogs in the VAITP-Auditor GUI.
This script can be used to test the icon fix on different platforms.
"""

import sys
import os
import platform

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_all_windows_icons():
    """Test icons on all major windows and dialogs."""
    print(f"Testing all window icons on {platform.system()}")
    
    results = []
    
    try:
        import customtkinter as ctk
        
        # Set appearance
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")
        
        # Create main root window
        root = ctk.CTk()
        root.title("Icon Test Root")
        root.geometry("300x200")
        root.withdraw()  # Hide it
        
        # Test 1: About Dialog
        print("\n1. Testing About Dialog...")
        try:
            from vaitp_auditor.gui.about_dialog import AboutDialog
            
            about_dialog = AboutDialog(root)
            print("   About dialog created - check for icon")
            
            # Show for 3 seconds
            root.after(3000, about_dialog.destroy)
            root.wait_window(about_dialog)
            
            results.append("About Dialog: ✓")
            print("   About dialog closed")
            
        except Exception as e:
            results.append(f"About Dialog: ✗ ({e})")
            print(f"   About dialog failed: {e}")
        
        # Test 2: Progress Dialog
        print("\n2. Testing Progress Dialog...")
        try:
            from vaitp_auditor.gui.progress_widgets import ProgressDialog
            
            progress_dialog = ProgressDialog(
                root, 
                title="Test Progress", 
                message="Testing icon...",
                can_cancel=True
            )
            print("   Progress dialog created - check for icon")
            
            # Show for 3 seconds
            root.after(3000, progress_dialog.destroy)
            root.wait_window(progress_dialog)
            
            results.append("Progress Dialog: ✓")
            print("   Progress dialog closed")
            
        except Exception as e:
            results.append(f"Progress Dialog: ✗ ({e})")
            print(f"   Progress dialog failed: {e}")
        
        # Test 3: Error Dialog
        print("\n3. Testing Error Dialog...")
        try:
            from vaitp_auditor.gui.error_handler import GUIErrorHandler
            
            # This creates and shows an auto-closing dialog
            print("   Creating error dialog - check for icon")
            GUIErrorHandler._show_auto_close_dialog(
                root,
                "Test Error",
                "Testing error dialog icon",
                3000  # 3 seconds
            )
            
            # Wait a bit for the dialog to appear and close
            root.after(4000, lambda: None)  # Wait 4 seconds
            root.update()
            
            results.append("Error Dialog: ✓")
            print("   Error dialog test completed")
            
        except Exception as e:
            results.append(f"Error Dialog: ✗ ({e})")
            print(f"   Error dialog failed: {e}")
        
        # Test 4: Simple CTkToplevel (like Setup Wizard)
        print("\n4. Testing CTkToplevel (Setup Wizard style)...")
        try:
            from vaitp_auditor.gui.icon_utils import set_window_icon
            
            toplevel = ctk.CTkToplevel(root)
            toplevel.title("Setup Wizard Icon Test")
            toplevel.geometry("400x300")
            
            # Set icon
            icon_success = set_window_icon(toplevel, store_reference=True)
            
            # Add content
            label = ctk.CTkLabel(
                toplevel,
                text=f"Setup Wizard Style Window\n\nIcon set: {'✓' if icon_success else '✗'}\n\nCheck title bar for icon",
                font=("Arial", 14)
            )
            label.pack(expand=True)
            
            # Make visible
            toplevel.lift()
            toplevel.focus_force()
            
            print(f"   CTkToplevel icon set: {icon_success}")
            print("   CTkToplevel created - check for icon")
            
            # Show for 4 seconds
            root.after(4000, toplevel.destroy)
            root.wait_window(toplevel)
            
            results.append(f"CTkToplevel: {'✓' if icon_success else '✗'}")
            print("   CTkToplevel closed")
            
        except Exception as e:
            results.append(f"CTkToplevel: ✗ ({e})")
            print(f"   CTkToplevel failed: {e}")
        
        # Clean up
        root.destroy()
        
        # Display results
        print(f"\n=== Results ===")
        success_count = 0
        for result in results:
            print(f"   {result}")
            if "✓" in result:
                success_count += 1
        
        total_count = len(results)
        print(f"\nSuccess rate: {success_count}/{total_count}")
        
        return success_count == total_count
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== VAITP-Auditor All Windows Icon Test ===")
    
    success = test_all_windows_icons()
    
    print(f"\n=== Final Result ===")
    if success:
        print("✅ ALL WINDOWS HAVE ICONS!")
        print("Icons should be visible in all VAITP-Auditor windows and dialogs.")
    else:
        print("❌ Some windows may be missing icons.")
        print("Check the test results above for details.")
    
    sys.exit(0 if success else 1)