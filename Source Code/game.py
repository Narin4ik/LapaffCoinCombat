import tkinter as tk
from tkinter import messagebox, ttk
from tkinter import filedialog
from PIL import Image, ImageTk
import sqlite3
import pygame
import webbrowser
import os
from pypresence import Presence
import time
from threading import Thread
import json
import random
import glob

# Настройка звука
pygame.mixer.init()

def play_sound():
    if pygame.mixer.music.get_busy():
        pygame.mixer.music.stop()
    pygame.mixer.music.load('lapaffsex.mp3')
    pygame.mixer.music.play()

def play_random_music(volume):
    music_files = glob.glob("music/*.mp3")
    if music_files:
        random_music = random.choice(music_files)
        pygame.mixer.music.load(random_music)
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(-1)

# Функции для работы с базой данных
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_data (
            id INTEGER PRIMARY KEY,
            balance REAL,
            upgrade_level INTEGER
        )
    ''')
    cursor.execute('SELECT * FROM player_data WHERE id = 1')
    if cursor.fetchone() is None:
        cursor.execute('INSERT INTO player_data (id, balance, upgrade_level) VALUES (1, 0, 0)')
    conn.commit()
    conn.close()

def get_balance():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT balance FROM player_data WHERE id = 1')
    balance = cursor.fetchone()[0]
    conn.close()
    return balance

def update_balance(new_balance):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE player_data SET balance = ? WHERE id = 1', (new_balance,))
    conn.commit()
    conn.close()

def get_upgrade_level():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT upgrade_level FROM player_data WHERE id = 1')
    level = cursor.fetchone()[0]
    conn.close()
    return level

def update_upgrade_level(new_level):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE player_data SET upgrade_level = ? WHERE id = 1', (new_level,))
    conn.commit()
    conn.close()

# Функции для работы с Discord Rich Presence
CLIENT_ID = "1255582325232762891"
start_time = int(time.time())

def init_discord_presence():
    RPC = Presence(CLIENT_ID)
    RPC.connect()
    return RPC

def update_discord_presence(RPC, balance):
    RPC.update(
        details=f"{localization['balance']}: {round(balance)} {localization['lapaff_coins']}",
        state=localization['created_by'],
        start=start_time,
        large_image="https://cdn.discordapp.com/attachments/639792159469469698/1255777194920120401/lapaffimage.png?ex=667e5d26&is=667d0ba6&hm=db097c177b80e0586747566ce1a94c027072b41357ece02b75de32d51367d827&",
        large_text="LaPaff Coin Combat",
        buttons=[
            {"label": localization['play_with_me'], "url": "https://github.com/YT-Narin/LapaffCoinCombat"},
            {"label": localization['telegram_channel'], "url": "https://t.me/narinshouse"}
        ]
    )

def discord_presence_thread(app):
    RPC = init_discord_presence()
    while True:
        update_discord_presence(RPC, app.balance)
        time.sleep(1)  # Update every second

# Загрузка локализаций
def load_localization(language):
    with open(f'languages/{language}.json', 'r', encoding='utf-8') as file:
        return json.load(file)

def save_game_settings(settings):
    with open('gamelanguage.json', 'w', encoding='utf-8') as file:
        json.dump(settings, file)

def load_game_settings():
    if os.path.exists('gamelanguage.json'):
        with open('gamelanguage.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    return {'language': 'English'}

from PIL import Image, ImageTk

class LaPaffCoinCombatApp(tk.Tk):
    VERSION = 'v1.0.0-beta-test'  # Версия игры

    def __init__(self):
        super().__init__()
        self.title("LaPaff Coin Combat")
        self.geometry("750x750")
        self.minsize(550, 550)
        self.iconbitmap('gameicon.ico')
        self.configure(bg='white')

        init_db()
        self.balance = get_balance()
        self.upgrade_level = get_upgrade_level()
        self.last_click_time = 0
        self.volume = 0.5
        self.language = load_game_settings()['language']
        global localization
        localization = load_localization(self.language)

        self.init_ui()
        self.update_balance_label()
        play_random_music(self.volume)

        # Запуск Discord Rich Presence в отдельном потоке
        discord_thread = Thread(target=discord_presence_thread, args=(self,), daemon=True)
        discord_thread.start()

    def init_ui(self):
        title_label = tk.Label(self, text="LaPaff Coin Combat", font=("Arial", 18, "bold"), bg='white')
        title_label.pack(pady=5)

        subtitle_label = tk.Label(self, text=localization['created_by'], font=("Arial", 10, "italic"), bg='white')
        subtitle_label.pack(pady=2)

        self.button_img = tk.PhotoImage(file='lapaffimage.png')
        click_button = tk.Button(self, image=self.button_img, command=self.on_button_click, bd=0)
        click_button.pack(pady=20)

        self.balance_label = tk.Label(self, text="", font=("Arial", 14, "bold"), bg='white')
        self.balance_label.pack(side=tk.BOTTOM, pady=10)

        upgrades_frame = tk.Frame(self, bg='white')
        upgrades_frame.pack(side=tk.LEFT, padx=20, pady=20, anchor='n')

        self.upgrades_label = tk.Label(upgrades_frame, text=localization['upgrades'], font=("Arial", 12, "bold"), bg='white')
        self.upgrades_label.pack(anchor='w')

        self.profit_increase_label = tk.Label(upgrades_frame, text=localization['profit_increase'], font=("Arial", 10), bg='white')
        self.profit_increase_label.pack(anchor='w')

        self.cost_label = tk.Label(upgrades_frame, text=f"{localization['cost']}: {self.get_upgrade_cost()} {localization['lapaff_coins']}", font=("Arial", 10), bg='white')
        self.cost_label.pack(anchor='w')

        upgrade_button = tk.Button(upgrades_frame, text=localization['upgrade'], command=self.buy_upgrade, font=("Arial", 10))
        upgrade_button.pack(anchor='w')

        settings_frame = tk.Frame(self, bg='white')
        settings_frame.pack(side=tk.TOP, padx=10, pady=10, anchor='ne')

        self.settings_label = tk.Label(settings_frame, text=localization['settings'], font=("Arial", 12, "bold"), bg='white')
        self.settings_label.pack(anchor='ne', padx=10, pady=10)

        self.music_volume_label = tk.Label(settings_frame, text=localization['music_volume'], font=("Arial", 10), bg='white')
        self.music_volume_label.pack(anchor='ne')

        self.volume_var = tk.DoubleVar(value=self.volume)
        volume_slider = tk.Scale(settings_frame, from_=0, to=1, orient=tk.HORIZONTAL, resolution=0.01, variable=self.volume_var, command=self.change_volume, bg='white')
        volume_slider.pack(anchor='ne')

        self.language_label = tk.Label(settings_frame, text=localization['language'], font=("Arial", 10), bg='white')
        self.language_label.pack(anchor='ne')

        languages = ["English", "Русский", "Українська", "Polski", "Deutsch", "Français", "Italiano", "简体中文", "日本語", "Czech", "Slovenský"]
        self.language_var = tk.StringVar(value=self.language)
        language_menu = ttk.Combobox(settings_frame, values=languages, textvariable=self.language_var, state='readonly')
        language_menu.pack(anchor='ne')

        save_button = tk.Button(settings_frame, text=localization['save'], command=self.save_settings, font=("Arial", 10))
        save_button.pack(anchor='ne')

        qr_frame = tk.Frame(self, bg='white')
        qr_frame.pack(side=tk.BOTTOM, padx=10, pady=10, anchor='se')

        # Уменьшение размера QR-кода
        qr_image = Image.open('telegramqrcode.png')
        qr_image.thumbnail((100, 100), Image.LANCZOS)  # Use Image.LANCZOS instead of Image.ANTIALIAS
        self.qr_img = ImageTk.PhotoImage(qr_image)
        qr_label = tk.Label(qr_frame, image=self.qr_img, bg='white')
        qr_label.pack(anchor='se')

        qr_label = tk.Label(qr_frame, text=localization['telegram_channel'], font=("Arial", 10), bg='white', fg='blue', cursor="hand2")
        qr_label.pack(anchor='se')
        qr_label.bind("<Button-1>", lambda e: webbrowser.open_new("https://t.me/narinshouse"))

        version_label = tk.Label(self, text=f"Game version: {self.VERSION}", font=("Arial", 10, "bold"), bg='white', anchor='sw')
        version_label.place(relx=0, rely=1, anchor='sw')

    def on_button_click(self):
        current_time = time.time()
        if current_time - self.last_click_time < 0.1:
            return

        self.balance += 1 + self.upgrade_level * 0.1
        self.update_balance_label()
        self.last_click_time = current_time
        play_sound()
        update_balance(self.balance)

    def update_balance_label(self):
        self.balance_label.config(text=f"{localization['balance']}: {round(self.balance, 2)} {localization['lapaff_coins']}")

    def get_upgrade_cost(self):
        return 1000 * (self.upgrade_level + 1)

    def buy_upgrade(self):
        cost = self.get_upgrade_cost()
        if self.balance >= cost:
            self.balance -= cost
            self.upgrade_level += 1
            self.update_balance_label()
            self.profit_increase_label.config(text=f"{localization['profit_increase']}: {round(self.upgrade_level * 0.1, 2)}")
            self.cost_label.config(text=f"{localization['cost']}: {self.get_upgrade_cost()} {localization['lapaff_coins']}")
            update_balance(self.balance)
            update_upgrade_level(self.upgrade_level)
        else:
            messagebox.showwarning(localization['not_enough_coins'], localization['not_enough_coins_message'])

    def change_volume(self, volume):
        self.volume = float(volume)
        pygame.mixer.music.set_volume(self.volume)

    def save_settings(self):
        new_language = self.language_var.get()
        if self.language != new_language:
            self.language = new_language
            localization.update(load_localization(self.language))
            self.save_game_settings()
            self.reload_ui()
        else:
            self.save_game_settings()

    def save_game_settings(self):
        settings = {'language': self.language, 'volume': self.volume}
        save_game_settings(settings)

    def reload_ui(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.init_ui()
        self.update_balance_label()

# Запуск приложения
if __name__ == "__main__":
    app = LaPaffCoinCombatApp()
    app.mainloop()
