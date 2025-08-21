import os
import shutil
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import threading
import time
import glob
from PIL import Image, ImageTk
import pandas as pd
import traceback
import sys
import requests
import webbrowser
import sentry_sdk
from tkinterdnd2 import DND_FILES, TkinterDnD

from app.processing import toGoodColumn
from app.utils import (
    list_dropbox_folders,
    generate_available_dates,
    open_csv_file,
    replace_comma_to_dot_separator,
    replace_dot_to_comma_separator,
    move_columns_right,
    convert_xlsx_to_csv
)
from app import config

if config.SENTRY_DSN:
    sentry_sdk.init(
        dsn=config.SENTRY_DSN,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )

def check_for_existing_instance():
    if os.path.exists(config.LOCK_FILE):
        messagebox.showwarning("Application Already Running", "An instance of the application is already running.")
        sys.exit()
    with open(config.LOCK_FILE, 'w') as f:
        f.write('running')

def remove_lock_file():
    if os.path.exists(config.LOCK_FILE):
        os.remove(config.LOCK_FILE)

def menu_closing():
    remove_lock_file()
    sys.exit()

def check_for_updates():
    try:
        response = requests.get(config.VERSION_URL, timeout=5)
        response.raise_for_status()
        latest_version = response.json().get("version")
        if latest_version and latest_version > config.APP_VERSION:
            if messagebox.askyesno("Update Available", f"A new version ({latest_version}) is available. Would you like to download it?"):
                webbrowser.open(config.DOWNLOAD_URL)
    except requests.exceptions.RequestException as e:
        print(f"Could not check for updates (network error): {e}")
    except ValueError:
        print(f"Could not check for updates (invalid JSON response from the server).")
    except Exception as e:
        print(f"An unexpected error occurred during update check: {e}")

def restore_from_backup(yearMonth='2024-09'):
    backup_files = glob.glob(os.path.join(config.OUTPUT_DIR, yearMonth, "output_backup_*.xlsx"))
    backup_temps = glob.glob(os.path.join(config.OUTPUT_DIR, yearMonth, "output_temp.csv"))
    if backup_files and backup_temps:
        latest_backup = max(backup_files, key=os.path.getctime)
        latest_temp = max(backup_temps, key=os.path.getctime)
        shutil.copy(latest_backup, config.OUTPUT_XLSX)
        shutil.copy(latest_temp, config.OUTPUT_TEMP_CSV)
        shutil.copy(latest_temp, config.OUTPUT_CSV)
        print(f"Restored from backup: {latest_backup}")
        messagebox.showinfo("Success", "Output successfully restored from backup.\nIf already running, the process will automatically continue in a few seconds.")
    else:
        print("No backup files found.")
        messagebox.showwarning("Warning", "No backup files available to restore.\nIf already running, the process will automatically continue in a few seconds.")

def main():
    if not os.path.exists(config.OUTPUT_XLSX):
        print("Main CSV file missing. Attempting to restore from backup.")
        restore_from_backup()

    root = TkinterDnD.Tk()
    root.title("Go4Green Software")
    root.geometry("650x700")

    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    icon_path = os.path.join(base_path, 'assets', 'icons', 'go4greenfr_logo.ico')
    theme_path = os.path.join(base_path, 'assets', 'themes', 'forest-ttk-theme', 'forest-light.tcl')

    icon_image = Image.open(icon_path)
    icon_image = icon_image.resize((64, 64))
    root.icon_photo = ImageTk.PhotoImage(icon_image)
    root.iconphoto(True, root.icon_photo)

    root.tk.call('source', theme_path)
    style = ttk.Style(root)
    style.theme_use('forest-light')

    style.configure("DropZone.TFrame", background="#f0f0f0", relief="sunken", borderwidth=2)
    style.configure("DropZoneHover.TFrame", background="#e0e0e0", relief="sunken", borderwidth=2)

    credentials_path = 'credential.json'

    def drop(event):
        filepath = event.data.strip('{}')
        if filepath.lower().endswith('.xlsx'):
            try:
                shutil.copy(filepath, config.OUTPUT_XLSX)
                filename = os.path.basename(filepath)
                drop_label.config(text=f"✅ Successfully loaded:\n{filename}")
                status_bar.config(text=f"Success: '{filename}' is ready to be used.")
                messagebox.showinfo("File Loaded", f"'{filename}' has been set as the new output file.")
            except Exception as e:
                messagebox.showerror("File Error", f"Could not copy the file.\nError: {e}")
                status_bar.config(text=f"Error: Could not copy file.")
        else:
            messagebox.showerror("Invalid File Type", "Error: Only .xlsx files are accepted.\nPlease drag and drop a valid Excel file.")
            status_bar.config(text="Error: Invalid file type. Please use an .xlsx file.")
        
        drop_zone.configure(style="DropZone.TFrame")

    def on_drop_enter(event):
        drop_zone.configure(style="DropZoneHover.TFrame")

    def on_drop_leave(event):
        drop_zone.configure(style="DropZone.TFrame")

    def toggle_credentials():
        nonlocal credentials_path
        if credentials_path == 'credential.json':
            credentials_path = 'credentialBackup.json'
            toggle_button.config(text="Using Backup Credentials")
        else:
            credentials_path = 'credential.json'
            toggle_button.config(text="Using Main Credentials")
        status_bar.config(text=f"Switched to {toggle_button.cget('text')}")

    def on_ok():
        yearMonth = date_var.get()
        newpath = os.path.join(config.OUTPUT_DIR, yearMonth)
        if not os.path.exists(newpath):
            os.makedirs(newpath)

        progress_var.set(0)

        if os.path.exists(config.OUTPUT_XLSX):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_xlsx = os.path.join(newpath, f"output_backup_{timestamp}.xlsx")
            backup_temp = os.path.join(newpath, "output_temp.csv")
            convert_xlsx_to_csv(config.OUTPUT_XLSX, config.OUTPUT_CSV)
            shutil.copy(config.OUTPUT_XLSX, backup_xlsx)
            shutil.copy(config.OUTPUT_CSV, config.OUTPUT_TEMP_CSV)
            shutil.copy(config.OUTPUT_CSV, backup_temp)
            status_bar.config(text=f"Backup created before processing.")
        else:
            status_bar.config(text="Warning: No output file to back up. A new one will be created.")

        ok_button.config(state=tk.DISABLED)
        toggle_button.config(state=tk.DISABLED)
        open_csv_button.config(state=tk.DISABLED)

        dropbox_folders = list_dropbox_folders(config.DROPBOX_BASE_DIR, yearMonth)
        total_folders = len(dropbox_folders)
        start_time = time.time()
        stop_event = threading.Event()

        def process_folders():
            try:
                for i, folder in enumerate(dropbox_folders, 1):
                    if stop_event.is_set():
                        status_bar.config(text="Process interrupted by user.")
                        break
                    
                    status_bar.config(text=f"Processing folder {i}/{total_folders}: {os.path.basename(folder)}...")
                    try:
                        replace_comma_to_dot_separator(config.OUTPUT_TEMP_CSV)
                        toGoodColumn(folder, yearMonth, credentials_path)
                        replace_dot_to_comma_separator(config.OUTPUT_TEMP_CSV)
                        if len(pd.read_csv(config.OUTPUT_TEMP_CSV, sep=';', dtype=str, encoding='iso8859_15')) < 10 :
                            backup_temp = os.path.join(newpath, "output_temp.csv")
                            shutil.copy(backup_temp, config.OUTPUT_TEMP_CSV)
                        if os.path.exists(config.OUTPUT_XLSX):
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            backup_xlsx = os.path.join(newpath, f"output_backup_{timestamp}.xlsx")
                            backup_temp = os.path.join(newpath, "output_temp.csv")
                            pd.read_csv(config.OUTPUT_TEMP_CSV, sep=';', dtype=str, encoding='iso8859_15').to_excel(backup_xlsx, index=False, engine='openpyxl')
                            shutil.copy(config.OUTPUT_TEMP_CSV, backup_temp)
                    except Exception as folder_error:
                        sentry_sdk.capture_exception(folder_error)
                        error_message = f"Error in folder {os.path.basename(folder)}. Restoring from backup..."
                        status_bar.config(text=error_message)
                        messagebox.showerror("Processing Error", f"An error occurred while processing folder {os.path.basename(folder)}:\n\n{folder_error}\n\nAttempting to restore from the last good backup.")
                        traceback.print_exc()
                        restore_from_backup(yearMonth=yearMonth)
                        time.sleep(5)

                    progress_var.set((i / total_folders) * 100)
                    progress_bar.update_idletasks()
                    elapsed_time = time.time() - start_time
                    avg_time_per_folder = elapsed_time / i
                    remaining_time = avg_time_per_folder * (total_folders - i)
                    remaining_hours = (remaining_time // 3600)
                    remaining_minutes = (remaining_time - remaining_hours * 3600) // 60
                    remaining_seconds = remaining_time - remaining_hours * 3600 - remaining_minutes * 60
                    remaining_label.config(text=f"Estimated time remaining: {int(remaining_hours)}h {int(remaining_minutes)}m {int(remaining_seconds)}s")
                    progress_label.config(text=f'Processing Progress: ({i}/{total_folders} folders)')

                if not stop_event.is_set():
                    if os.path.exists(config.OUTPUT_TEMP_CSV):
                        shutil.copy(config.OUTPUT_TEMP_CSV, config.OUTPUT_CSV)
                        pd.read_csv(config.OUTPUT_TEMP_CSV, sep=';', dtype=str, encoding='iso8859_15').to_excel(config.OUTPUT_XLSX, index=False, engine='openpyxl')
                    move_columns_right(config.OUTPUT_XLSX)
                    progress_var.set(100)
                    remaining_label.config(text="Processing complete!")
                    status_bar.config(text="Success! You can now open the Excel file.")
                    open_csv_button.config(state=tk.NORMAL)
                    ok_button.config(state=tk.NORMAL)
                    toggle_button.config(state=tk.NORMAL)
            except Exception as e:
                sentry_sdk.capture_exception(e)
                status_bar.config(text=f"A critical error occurred: {e}")
                messagebox.showerror("Critical Error", f"A critical error occurred during processing: {e}")

        processing_thread = threading.Thread(target=process_folders, daemon=True)
        remaining_label.config(text=f"Estimated time remaining: calculating...")
        status_bar.config(text="Starting process...")
        processing_thread.start()

        def on_closing():
            remove_lock_file()
            if messagebox.askokcancel("Quit", "Do you want to quit? This will stop the current process and restore the last backup."):
                restore_from_backup(yearMonth=yearMonth)
                stop_event.set()
                if processing_thread.is_alive():
                    processing_thread.join(timeout=5)
                root.destroy()
                sys.exit()
        root.protocol("WM_DELETE_WINDOW", on_closing)

    main_frame = ttk.Frame(root, padding="20 20 20 20")
    main_frame.pack(expand=True, fill="both")

    step1_label = ttk.Label(main_frame, text="Step 1: Select Date", font=("Helvetica", 16, "bold"))
    step1_label.pack(fill='x', pady=(0, 5))

    available_dates = generate_available_dates(months_back=4, months_forward=2)
    date_var = tk.StringVar()
    date_var.set(available_dates[0])
    dropdown = ttk.Combobox(main_frame, textvariable=date_var, values=available_dates, font=("Helvetica", 14), state="readonly")
    dropdown.pack(fill='x', pady=10)

    step2_label = ttk.Label(main_frame, text="Step 2 (Optional): Load Previous File", font=("Helvetica", 16, "bold"))
    step2_label.pack(fill='x', pady=(20, 5))

    drop_zone = ttk.Frame(main_frame, style="DropZone.TFrame", width=400, height=100)
    drop_zone.pack(fill="x", pady=10)
    drop_zone.pack_propagate(False)
    drop_label = ttk.Label(drop_zone, text="📥\nDrag & Drop 'output.xlsx' Here to Load It", font=("Helvetica", 12), justify="center", style="DropZone.TLabel")
    drop_label.pack(expand=True)

    drop_zone.drop_target_register(DND_FILES)
    drop_zone.dnd_bind('<<Drop>>', drop)
    drop_zone.bind("<Enter>", on_drop_enter)
    drop_zone.bind("<Leave>", on_drop_leave)

    step3_label = ttk.Label(main_frame, text="Step 3: Start Processing", font=("Helvetica", 16, "bold"))
    step3_label.pack(fill='x', pady=(20, 5))
    
    ok_button = ttk.Button(main_frame, text="Process All Images", style='Accent.TButton', command=on_ok)
    ok_button.pack(fill='x', ipady=5, pady=10)

    progress_label = ttk.Label(main_frame, text="Processing Progress", font=("Helvetica", 12))
    progress_label.pack(pady=(20, 5), anchor='w')

    progress_var = tk.DoubleVar()
    style.configure("green.Horizontal.TProgressbar", troughcolor='#EAEAEA', background='#217346', thickness=20)
    progress_bar = ttk.Progressbar(main_frame, variable=progress_var, maximum=100, length=500, style="green.Horizontal.TProgressbar")
    progress_bar.pack(fill='x', pady=5)

    remaining_label = ttk.Label(main_frame, font=("Helvetica", 10))
    remaining_label.pack(fill='x', pady=5)

    open_csv_button = ttk.Button(main_frame, text="Open Output Excel File", command=lambda: open_csv_file(config.OUTPUT_XLSX))
    open_csv_button.pack(fill='x', ipady=5, pady=(20,10))

    toggle_button = ttk.Checkbutton(main_frame, text="Using Main Credentials", style='Switch', command=toggle_credentials)
    toggle_button.pack(pady=10)
    
    status_bar = ttk.Label(root, text="Ready. Select a month and press 'Process All Images'.", relief=tk.SUNKEN, anchor=tk.W, padding=5)
    status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    root.protocol("WM_DELETE_WINDOW", menu_closing)
    root.mainloop()

if __name__ == "__main__":
    check_for_existing_instance()
    check_for_updates()
    main()