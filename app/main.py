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

    root = tk.Tk()

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

    big_frame = ttk.Frame(root)
    big_frame.pack(fill='both', anchor='n')
    root.tk.call('source', theme_path)
    ttk.Style().theme_use('forest-light')
    root.title("Go4Green Software")

    credentials_path = 'credential.json'

    def toggle_credentials():
        nonlocal credentials_path
        if credentials_path == 'credential.json':
            credentials_path = 'credentialBackup.json'
            toggle_button.config(text="Using Backup Credentials")
        else:
            credentials_path = 'credential.json'
            toggle_button.config(text="Using Main Credentials")
        print(f"Selected credentials: {credentials_path}")

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
            print(f"Backup created: {backup_xlsx}")
        else:
            print("The file does not exist. Creating a new file.")

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
                        print("Process interrupted by the user.")
                        break
                    print(folder)
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
                            print(f"Backup created: {backup_xlsx}")
                        else:
                            print("The file does not exist. Creating a new file.")
                    except Exception as folder_error:
                        print(f"An error occurred while processing folder {folder}: {folder_error}")
                        messagebox.showinfo("Error", f"An error occurred while processing folder {folder}: {folder_error}.\n\nCurrently attempting to restore output file from backup ...")
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
                    remaining_label.config(text=f"Estimated remaining time: {int(remaining_hours)} hours {int(remaining_minutes)} minutes {int(remaining_seconds)} seconds")
                    progress_label.config(text=f'Processing Progress: ({i}/{total_folders} folders) ')

                if not stop_event.is_set():
                    if os.path.exists(config.OUTPUT_TEMP_CSV):
                        shutil.copy(config.OUTPUT_TEMP_CSV, config.OUTPUT_CSV)
                        pd.read_csv(config.OUTPUT_TEMP_CSV, sep=';', dtype=str, encoding='iso8859_15').to_excel(config.OUTPUT_XLSX, index=False, engine='openpyxl')
                        print(f"Output created: {config.OUTPUT_XLSX}")
                    else:
                        print("The file does not exist. Creating a new file.")
                    move_columns_right(config.OUTPUT_XLSX)
                    print("Processing complete.")
                    progress_var.set(100)
                    remaining_label.config(text="Process completed! Press 'Open Excel' to open the resulting file")
                    open_csv_button.config(state=tk.NORMAL)
                    ok_button.config(state=tk.NORMAL)
                    toggle_button.config(state=tk.NORMAL)
            except Exception as e:
                print(f"An error occurred: {e}")

        processing_thread = threading.Thread(target=process_folders, daemon=True)
        remaining_label.config(text=f"Estimated remaining time: calculating...")
        processing_thread.start()

        def on_closing():
            remove_lock_file()
            restore_from_backup(yearMonth=yearMonth)
            stop_event.set()
            if processing_thread.is_alive():
                processing_thread.join(timeout=5)
            root.destroy()
            sys.exit()
        root.protocol("WM_DELETE_WINDOW", on_closing)

    label = ttk.Label(root, text="Select Year and Month:", font=("Helvetica", 16))
    label.pack(pady=(30, 10), anchor='n')

    available_dates = generate_available_dates(months_back=4, months_forward=2)
    date_var = tk.StringVar()
    date_var.set(available_dates[0])
    dropdown = ttk.Combobox(root, textvariable=date_var, values=available_dates, font=("Helvetica", 14))
    dropdown.pack(pady=10, anchor='n')

    style = ttk.Style()
    style.configure("TButton", font=("Helvetica", 14), padding=10, relief="flat")
    ok_button = ttk.Button(root, text="Process all images for the selected month", style='Accent.TButton', command=on_ok)
    ok_button.pack(pady=(10, 50), anchor='n')

    progress_label = ttk.Label(root, text="Processing Progress:", font=("Helvetica", 16))
    progress_label.pack(pady=10, anchor='n')

    progress_var = tk.DoubleVar()
    style.configure("green.Horizontal.TProgressbar", troughcolor='#d9ead3', background='#37d3a8', thickness=30)
    progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100, length=500, style="green.Horizontal.TProgressbar")
    progress_bar.pack(padx=100, pady=10, anchor='n')

    remaining_label = ttk.Label(root, font=("Helvetica", 14))
    remaining_label.pack(pady=10, anchor='n')

    open_csv_button = ttk.Button(root, text="Open Excel", command=lambda: open_csv_file(config.OUTPUT_XLSX))
    open_csv_button.pack(pady=10, anchor='n')

    toggle_button = ttk.Checkbutton(root, text="Using Main Credentials", style='Switch', command=toggle_credentials)
    toggle_button.pack(pady=(10, 30), anchor='n')

    root.protocol("WM_DELETE_WINDOW", menu_closing)
    root.mainloop()

if __name__ == "__main__":
    check_for_existing_instance()
    check_for_updates()
    main()