import tkinter as tk
from tkinter import ttk
import psutil
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume
import threading
import time

def get_active_applications():
    applications = []
    for proc in psutil.process_iter(['pid', 'name']):
        applications.append(proc.info['name'])
    return sorted(set(applications))  # Entfernt Duplikate und sortiert die Liste

def get_application_volume(process_name):
    sessions = AudioUtilities.GetAllSessions()
    for session in sessions:
        volume = session._ctl.QueryInterface(ISimpleAudioVolume)
        if session.Process and session.Process.name() == process_name:
            return volume.GetMasterVolume()
    return None

def set_application_volume(process_name, volume_level):
    sessions = AudioUtilities.GetAllSessions()
    for session in sessions:
        volume = session._ctl.QueryInterface(ISimpleAudioVolume)
        if session.Process and session.Process.name() == process_name:
            volume.SetMasterVolume(volume_level, None)


def monitor_volume(monitor_app, reduce_app, threshold, reduction, status_label):
    original_volume = get_application_volume(reduce_app)
    is_reduced = False

    while True:
        monitor_volume = get_application_volume(monitor_app)
        if monitor_volume is not None:
            threshold_decimal = threshold / 100
            reduction_decimal = reduction / 100

            status_label.config(text=f"{monitor_app} Lautstärke: {monitor_volume * 100:.0f}%")

            if monitor_volume > threshold_decimal and not is_reduced:
                # Reduziere die Lautstärke
                current_volume = get_application_volume(reduce_app)
                if current_volume is not None:
                    new_volume = max(0, current_volume - reduction_decimal)
                    set_application_volume(reduce_app, new_volume)
                    is_reduced = True
                    status_label.config(
                        text=f"{monitor_app} Lautstärke: {monitor_volume * 100:.0f}%\n{reduce_app} reduziert auf {new_volume * 100:.0f}%")
            elif monitor_volume <= threshold_decimal and is_reduced:
                # Stelle die ursprüngliche Lautstärke wieder her
                set_application_volume(reduce_app, original_volume)
                is_reduced = False
                status_label.config(
                    text=f"{monitor_app} Lautstärke: {monitor_volume * 100:.0f}%\n{reduce_app} wiederhergestellt auf {original_volume * 100:.0f}%")
        else:
            status_label.config(text=f"{monitor_app} nicht gefunden")

        time.sleep(0.5)  # Überprüfe alle 0,5 Sekunden

def create_gui():
    root = tk.Tk()
    root.title("Lautstärke-Monitor")
    root.geometry("400x650")  # Leicht vergrößert für zusätzlichen Platz

    apps = get_active_applications()

    frame = ttk.Frame(root, padding="10")
    frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(frame, text="Zu überwachende Anwendung:").pack(pady=5)
    monitor_app = ttk.Combobox(frame, values=apps)
    monitor_app.pack(pady=5)

    ttk.Label(frame, text="Zu reduzierende Anwendung:").pack(pady=5)
    reduce_app = ttk.Combobox(frame, values=apps)
    reduce_app.pack(pady=5)

    # Schwellenwert mit Anzeige
    threshold_frame = ttk.Frame(frame)
    threshold_frame.pack(fill=tk.X, pady=5)
    ttk.Label(threshold_frame, text="Schwellenwert:").pack(side=tk.LEFT)
    threshold_value = tk.StringVar()
    threshold_value.set("70%")
    ttk.Label(threshold_frame, textvariable=threshold_value).pack(side=tk.RIGHT)

    def update_threshold(value):
        threshold_value.set(f"{int(float(value))}%")

    threshold = ttk.Scale(frame, from_=0, to=100, orient=tk.HORIZONTAL, command=update_threshold)
    threshold.set(70)
    threshold.pack(fill=tk.X, pady=5)

    # Reduktionswert mit Anzeige
    reduction_frame = ttk.Frame(frame)
    reduction_frame.pack(fill=tk.X, pady=5)
    ttk.Label(reduction_frame, text="Reduktionswert:").pack(side=tk.LEFT)
    reduction_value = tk.StringVar()
    reduction_value.set("20%")
    ttk.Label(reduction_frame, textvariable=reduction_value).pack(side=tk.RIGHT)

    def update_reduction(value):
        reduction_value.set(f"{int(float(value))}%")

    reduction = ttk.Scale(frame, from_=0, to=100, orient=tk.HORIZONTAL, command=update_reduction)
    reduction.set(20)
    reduction.pack(fill=tk.X, pady=5)

    # Live-Pegel für die überwachte Anwendung
    ttk.Label(frame, text="Lautstärke der überwachten Anwendung:").pack(pady=5)
    monitor_level = ttk.Progressbar(frame, orient=tk.HORIZONTAL, length=300, mode='determinate')
    monitor_level.pack(pady=5)

    # Live-Pegel für die zu reduzierende Anwendung
    ttk.Label(frame, text="Lautstärke der zu reduzierenden Anwendung:").pack(pady=5)
    reduce_level = ttk.Progressbar(frame, orient=tk.HORIZONTAL, length=300, mode='determinate')
    reduce_level.pack(pady=5)

    status_label = ttk.Label(frame, text="")
    status_label.pack(pady=10)

    # ... (der Rest des Codes bleibt unverändert) ...

    def start_monitoring():
        monitor_thread = threading.Thread(target=monitor_volume, args=(
            monitor_app.get(),
            reduce_app.get(),
            threshold.get(),
            reduction.get(),
            status_label
        ))
        monitor_thread.daemon = True
        monitor_thread.start()

        # Starte den Thread für die Live-Pegel-Aktualisierung
        level_thread = threading.Thread(target=set_application_volume())
        level_thread.daemon = True
        level_thread.start()

    start_button = ttk.Button(frame, text="Überwachung starten", command=start_monitoring)
    start_button.pack(pady=10)

    root.mainloop()

# Führen Sie diese Funktion aus
if __name__ == "__main__":
    create_gui()