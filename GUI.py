import os
import shutil
import re
import tkinter as tk
from tkinter import ttk
from datetime import datetime
import threading
import time
import glob
from PIL import Image, ImageTk
from mainTer import toGoodColumn
from utils import list_dropbox_folders, generate_available_dates, open_csv_file, replace_comma_to_dot_separator, replace_dot_to_comma_separator, move_columns_right, convert_xlsx_to_csv
from tkinter import messagebox
import traceback
import pandas as pd
import sys

# Path to the lock file (stored in the same directory as the executable)
lock_file = os.path.join(os.path.dirname(sys.argv[0]), 'app.lock')

def check_for_existing_instance():
    # Check if the lock file already exists
    if os.path.exists(lock_file):
        # If the lock file exists, another instance is running; show a warning and exit
        #messagebox.showwarning("Warning", "Application is already running.")
        sys.exit()  # Exit the program if another instance is detected

    # If no lock file, create one to signal that the application is running
    with open(lock_file, 'w') as f:
        f.write('running')

# Function to remove the lock file on exit
def remove_lock_file():
    if os.path.exists(lock_file):
        os.remove(lock_file)

def menu_closing():
        # Ensure the lock file is removed when the program exits
    remove_lock_file()
    sys.exit()



# Initialize the path to the default credentials file
credentials_path = 'credential.json'
yearMonth = '2024-09'

# Modify the restore_from_backup function to include a success message
def restore_from_backup(yearMonth='2024-09'):
    output_xlsx = "output/output.xlsx"
    output_temp = "output/temp/outputTemp.csv"
    output_csv = "output/temp/output.csv"
    
    backup_files = glob.glob(f"output/{yearMonth}/output_backup_*.xlsx")
    backup_temps = glob.glob(f"output/{yearMonth}/output_temp.csv")
    if backup_files and backup_temps:
        latest_backup = max(backup_files, key=os.path.getctime)
        latest_temp = max(backup_temps, key=os.path.getctime)
        shutil.copy(latest_backup, output_xlsx)
        shutil.copy(latest_temp, output_temp)
        shutil.copy(latest_temp, output_csv)
        #pd.read_excel(latest_backup).to_csv(output_temp, sep=';', index=False)
        print(f"Restored from backup: {latest_backup}")
        # Display toast message after successful restoration
        messagebox.showinfo("Success", "Output successfully restored from backup.\nIf already running, the process will automatically continue in a few seconds.")

    else:
        print("No backup files found.")
        messagebox.showwarning("Warning", "No backup files available to restore.\nIf already running, the process will automatically continue in a few seconds.")
                # Ask the user if they want to close the software



# Main function with a GUI for date selection
def main():
    #filesToDel = glob.glob('all_images/*')
    #for f in filesToDel:
    #    os.remove(f)
    # Attempt to restore from backup if main file is missing

    # Set up the GUI window using ThemedTk with a selected ttk theme

    root = tk.Tk()

    output_xlsx = "output/output.xlsx"
    output_csv = "output/temp/output.csv"
    output_temp = "output/temp/outputTemp.csv"
    if not os.path.exists(output_xlsx):
        print("Main CSV file missing. Attempting to restore from backup.")
        restore_from_backup()

        # Function to toggle between credential files
    def toggle_credentials():
        global credentials_path
        if credentials_path == 'credential.json':
            credentials_path = 'credentialBackup.json'
            toggle_button.config(text="Using Backup Credentials")
        else:
            credentials_path = 'credential.json'
            toggle_button.config(text="Using Main Credentials")
        print(f"Selected credentials: {credentials_path}")

    def on_ok():
        yearMonth = date_var.get()  # Get the selected date from the dropdown

        newpath = f'output/{yearMonth}' 
        if not os.path.exists(newpath):
            os.makedirs(newpath)

        print(f"Selected date: {yearMonth}")
        print(f"Using credentials: {credentials_path}")  # Show the selected credentials file

        progress_var.set(0)

        # Backup the existing CSV file
        if os.path.exists(output_xlsx):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_xlsx = f"output/{yearMonth}/output_backup_{timestamp}.xlsx"
            backup_temp = f"output/{yearMonth}/output_temp.csv"
            convert_xlsx_to_csv(output_xlsx, output_csv)
            shutil.copy(output_xlsx, backup_xlsx)
            shutil.copy(output_csv, output_temp)
            shutil.copy(output_csv, backup_temp)
            
            #pd.read_excel(output_xlsx).to_csv(output_temp, sep=';', index=False)
            print(f"Backup created: {backup_xlsx}")
        else:
            print("The file does not exist. Creating a new file.")

        #base_dir = '/app_go4green'
        base_dir = '/8. Installations operationnelles/3. Maintenance par projet'

        # Regular expression to match folders in the format LLL-NNN
        #folder_pattern = re.compile(r'^[A-Z]{3}-[A-Z0-9]{3}$')

        # Disable the OK button and credentials toggle to prevent further clicks
        ok_button.config(state=tk.DISABLED)
        toggle_button.config(state=tk.DISABLED)
        open_csv_button.config(state=tk.DISABLED)
        #restore_button.config(state=tk.DISABLED)

        # List all folders in the base directory using list_dropbox_folders
        dropbox_folders = list_dropbox_folders(base_dir, yearMonth)
        total_folders = len(dropbox_folders)  # Total number of folders to process

        # Track the start time to estimate remaining time
        start_time = time.time()

        # Run the processing in a separate thread with a stop flag
        stop_event = threading.Event()

        def process_folders():
            try:
                for i, folder in enumerate(dropbox_folders, 1):

                    
                    if stop_event.is_set():
                        print("Process interrupted by the user.")
                        break

                    print(folder)
                    try:
                        #dropbox_folder = f'/app_go4green/{folder}/Photos/{yearMonth}'  # Dropbox folder path
                        dropbox_folder = folder
                        print(f"Processing folder: {dropbox_folder}")

                        replace_comma_to_dot_separator(output_temp)
                        toGoodColumn(dropbox_folder, yearMonth, credentials_path)
                        replace_dot_to_comma_separator(output_temp)

                        if len(pd.read_csv(output_temp, sep=';', dtype=str, encoding='iso8859_15')) < 10 :
                            backup_temp = f"output/{yearMonth}/output_temp.csv"
                            shutil.copy(backup_temp, output_temp)

                        if os.path.exists(output_xlsx):
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            backup_xlsx = f"output/{yearMonth}/output_backup_{timestamp}.xlsx"
                            backup_temp = f"output/{yearMonth}/output_temp.csv"
                            pd.read_csv(output_temp, sep=';', dtype=str, encoding='iso8859_15').to_excel(backup_xlsx, index = False, engine='openpyxl')
                            shutil.copy(output_temp, backup_temp)
                            print(f"Backup created: {backup_xlsx}")
                        else:
                            print("The file does not exist. Creating a new file.")

                    except Exception as folder_error:
                        print(f"An error occurred while processing folder {folder}: {folder_error}")
                        print("Attempting to restore from backup.")
                        messagebox.showinfo("Error", f"An error occurred while processing folder {folder}: {folder_error}.\n\nCurrently attempting to restore output file from backup ...")
                        traceback.print_exc()
                        restore_from_backup(yearMonth=yearMonth)
                        time.sleep(5)

                    # Update the progress bar
                    progress_var.set((i / total_folders) * 100)
                    progress_bar.update_idletasks()

                    # Estimate remaining time
                    elapsed_time = time.time() - start_time
                    avg_time_per_folder = elapsed_time / i
                    remaining_time = avg_time_per_folder * (total_folders - i)
                    remaining_hours = (remaining_time // 3600)
                    remaining_minutes = (remaining_time - remaining_hours * 3600) // 60
                    remaining_seconds = remaining_time - remaining_hours * 3600 - remaining_minutes * 60
                    remaining_label.config(
                        text=f"Estimated remaining time: {int(remaining_hours)} hours {int(remaining_minutes)} minutes {int(remaining_seconds)} seconds")
                    progress_label.config(text=f'Processing Progress: ({i}/{total_folders} folders) ')

                if not stop_event.is_set():
                    if os.path.exists(output_temp):
                        shutil.copy(output_temp, output_csv)
                        pd.read_csv(output_temp, sep=';', dtype=str, encoding='iso8859_15').to_excel(output_xlsx, index = False, engine='openpyxl')
                        print(f"Output created: {output_xlsx}")
                    else:
                        print("The file does not exist. Creating a new file.")
                    move_columns_right(output_xlsx)
                    print("Processing complete.")
                    progress_var.set(100)
                    remaining_label.config(text="Process completed! Press 'Open Excel' to open the resulting file")
                    open_csv_button.config(state=tk.NORMAL)  # Enable the CSV button
                    ok_button.config(state=tk.NORMAL)  # Re-enable OK button
                    #restore_button.config(state=tk.NORMAL)  # Re-enable Restore button
                    toggle_button.config(state=tk.NORMAL)

            except Exception as e:
                print(f"An error occurred: {e}")

        # Create a thread to process the folders
        processing_thread = threading.Thread(target=process_folders, daemon=True)
        remaining_label.config(text=f"Estimated remaining time: calculating...")
        processing_thread.start()
        

        def on_closing():
            # Ensure the lock file is removed when the program exits
            remove_lock_file()
            restore_from_backup(yearMonth=yearMonth)
            stop_event.set()  # Set the stop flag
            
            if processing_thread.is_alive():
                processing_thread.join(timeout=5)
            root.destroy()  # Destroy the window
            sys.exit()

        root.protocol("WM_DELETE_WINDOW", on_closing)




    # Load the icon image
    icon_image = Image.open('go4greenfr_logo.ico')
    icon_image = icon_image.resize((64, 64))  # Resize to 64x64 pixels
    icon_photo = ImageTk.PhotoImage(icon_image)
    root.iconphoto(True, icon_photo)

    big_frame = ttk.Frame(root)
    big_frame.pack(fill='both', anchor='n')
    root.tk.call('source', 'Forest-ttk-theme-master/forest-light.tcl')
    ttk.Style().theme_use('forest-light')

    root.title("Go4Green Software")

    # Label for the dropdown
    label = ttk.Label(root, text="Select Year and Month:", font=("Helvetica", 16))
    label.pack(pady=(30, 10), anchor='n')

    # Generate available dates dynamically (last 3 months, next 2 months)
    available_dates = generate_available_dates(months_back=4, months_forward=2)

    # Create a Tkinter variable to store the selected date
    date_var = tk.StringVar()
    date_var.set(available_dates[0])  # Default to the first date

    # Create a dropdown (combobox) for date selection
    dropdown = ttk.Combobox(root, textvariable=date_var, values=available_dates, font=("Helvetica", 14))
    dropdown.pack(pady=10, anchor='n')

    style = ttk.Style()
    # Button to confirm the selection and proceed (with rounded corners and larger size)
    style.configure("TButton", font=("Helvetica", 14), padding=10, relief="flat")
    ok_button = ttk.Button(root, text="Process all images for the selected month", style='Accent.TButton', command=on_ok)
    ok_button.pack(pady=(10, 50), anchor='n')



    # Progress bar label
    progress_label = ttk.Label(root, text="Processing Progress:", font=("Helvetica", 16))
    progress_label.pack(pady=10, anchor='n')

    # Progress bar widget (larger size)
    progress_var = tk.DoubleVar()

    style.configure("green.Horizontal.TProgressbar", troughcolor='#d9ead3', background='#37d3a8', thickness=30)
    progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100, length=500,
                                   style="green.Horizontal.TProgressbar")
    progress_bar.pack(padx=100, pady=10, anchor='n')

    # Remaining time label
    remaining_label = ttk.Label(root, font=("Helvetica", 14))
    remaining_label.pack(pady=10, anchor='n')

    # Button to open all_values.csv
    open_csv_button = ttk.Button(root, text="Open Excel", command=lambda: open_csv_file(output_xlsx))
    open_csv_button.pack(pady=10, anchor='n')

    # Button to restore the latest backup
    #restore_button = ttk.Button(root, text="Restore output from Backup", command=restore_from_backup)
    #restore_button.pack(pady=(10, 30), anchor='n')

    # Credentials toggle button
    toggle_button = ttk.Checkbutton(root, text="Using Main Credentials", style = 'Switch', command=toggle_credentials)
    toggle_button.pack(pady=(10, 30), anchor='n')

    # Start the Tkinter event loop
    root.protocol("WM_DELETE_WINDOW", menu_closing)
    root.mainloop()

if __name__ == "__main__":
    check_for_existing_instance()  # Ensures single instance
    main()
