import json
import random
import urllib.request
import tkinter as tk
from tkinter import messagebox
import textwrap

# --- Класс тестового приложения (QuizApp) ---
class QuizApp:
    def __init__(self, root, questions):
        self.root = root
        self.root.title("Тестовый тренажер")
        # Используем очередь для хранения вопросов, которые ещё надо ответить
        self.questions_queue = questions[:]  
        self.score = 0
        self.answered = False   # Флаг: ответ по текущему вопросу получен или нет
        self.time_left = 1800   # 30 минут в секундах

        # Метка таймера
        self.timer_label = tk.Label(root, text="Оставшееся время: 30:00", font=("Arial", 12), fg="red")
        self.timer_label.pack(pady=5)

        # Метка вопроса с автоматическим переносом строки
        self.question_label = tk.Label(root, text="", font=("Arial", 14), wraplength=500, justify="center")
        self.question_label.pack(pady=10)

        # Фрейм для кнопок с вариантами ответов
        self.buttons_frame = tk.Frame(root)
        self.buttons_frame.pack()

        self.answer_buttons = []
        for i in range(4):
            button = tk.Button(self.buttons_frame, text="", font=("Arial", 12),
                               width=40, command=lambda i=i: self.select_answer(i),
                               anchor="w", justify="left")
            self.answer_buttons.append(button)
            button.pack(pady=5)

        # Фрейм для управляющих кнопок: слева «Вернуться позже», справа «Следующий вопрос»
        self.control_frame = tk.Frame(root)
        self.control_frame.pack(pady=10)

        self.skip_button = tk.Button(self.control_frame, text="Вернуться позже", font=("Arial", 12),
                                     command=self.skip_question)
        self.skip_button.grid(row=0, column=0, padx=10)

        self.next_button = tk.Button(self.control_frame, text="Следующий вопрос", font=("Arial", 12),
                                     command=self.next_question)
        self.next_button.grid(row=0, column=1, padx=10)

        self.update_timer()
        self.load_question()

    def update_timer(self):
        """Обновляет таймер каждую секунду и завершает тест по истечении времени."""
        minutes = self.time_left // 60
        seconds = self.time_left % 60
        self.timer_label.config(text=f"Оставшееся время: {minutes:02}:{seconds:02}")
        if self.time_left > 0:
            self.time_left -= 1
            self.root.after(1000, self.update_timer)
        else:
            messagebox.showinfo("Время вышло!", f"Ваш результат: {self.score} из {self.initial_total}")
            self.root.quit()

    def load_question(self):
        """Загружает вопрос из начала очереди и обновляет варианты ответов."""
        if not self.questions_queue:
            messagebox.showinfo("Результат", f"Тест завершён! Ваш счёт: {self.score} из {self.initial_total}")
            self.root.quit()
            return

        self.answered = False
        current_question = self.questions_queue[0]
        self.question_label.config(text=current_question["question"])
        options = current_question["options"]
        # correct_answer в JSON начинается с 1 – вычитаем 1
        correct_answer = current_question["correct_answer"] - 1  
        # Перемешиваем варианты и определяем новый индекс правильного ответа
        self.shuffled_options = options.copy()
        random.shuffle(self.shuffled_options)
        self.correct_index = self.shuffled_options.index(options[correct_answer])
        # Заполняем кнопки вариантами ответа с переносом длинного текста
        for i, option in enumerate(self.shuffled_options):
            wrapped_option = textwrap.fill(option, width=40)
            self.answer_buttons[i].config(text=wrapped_option, bg="lightgray", state=tk.NORMAL)
        self.update_control_buttons()

    def select_answer(self, index):
        """Обрабатывает выбор ответа пользователем.
        Если ответ правильный — окрашивает выбранную кнопку в светло-зелёный,
        иначе — выбранную в светло-красный и правильную в светло-зелёный.
        Затем отключает кнопки.
        """
        if self.answered:
            return

        if index == self.correct_index:
            self.answer_buttons[index].config(bg="#90EE90")  # Светло-зеленый
            self.score += 1
        else:
            self.answer_buttons[index].config(bg="#FFB6C1")  # Светло-красный
            self.answer_buttons[self.correct_index].config(bg="#90EE90")
        self.answered = True
        for button in self.answer_buttons:
            button.config(state=tk.DISABLED)
        self.update_control_buttons()

    def next_question(self):
        """Переходит к следующему вопросу, если текущий ответ получен.
        Если ответ не выбран, выводит предупреждение.
        После ответа удаляет текущий вопрос из очереди.
        """
        if not self.answered:
            messagebox.showwarning("Внимание",
                                   "Вы не выбрали вариант. Нажмите 'Вернуться позже', чтобы отложить вопрос.")
            return

        self.questions_queue.pop(0)
        self.load_question()

    def skip_question(self):
        """Перемещает текущий вопрос в конец очереди, если ответ не получен.
        Если это единственный вопрос, откладывать нельзя.
        """
        if self.answered:
            messagebox.showwarning("Внимание", "Вы уже ответили на этот вопрос.")
            return

        if len(self.questions_queue) == 1:
            messagebox.showwarning("Внимание", "Это последний вопрос, его нельзя откладывать.")
            return

        question = self.questions_queue.pop(0)
        self.questions_queue.append(question)
        self.load_question()

    def update_control_buttons(self):
        """Обновляет текст кнопки 'Следующий вопрос': если остался последний вопрос, меняем текст на 'Завершить тест'."""
        if len(self.questions_queue) == 1:
            self.next_button.config(text="Завершить тест")
        else:
            self.next_button.config(text="Следующий вопрос")

# --- Функция загрузки вопросов по URL ---
def load_questions(url):
    """Загружает JSON-файл с вопросами через интернет с помощью urllib."""
    with urllib.request.urlopen(url) as response:
        if response.getcode() != 200:
            raise Exception("Ошибка загрузки данных с сервера")
        data = response.read().decode()
        json_obj = json.loads(data)
        return json_obj["questions"]

# --- Функция запуска теста (по выбранному URL) ---
def start_quiz(root, selected_url):
    root.destroy()
    quiz_root = tk.Tk()
    questions = load_questions(selected_url)
    num = min(len(questions), 10)
    sampled_questions = random.sample(questions, num)
    app = QuizApp(quiz_root, sampled_questions)
    app.initial_total = num
    quiz_root.mainloop()

# --- Главное меню выбора предмета и подразделов ---
# Глобальная структура предметов:
subjects = {
    "Естествознание": {
        "subcategories": {
            "1": {"url": "https://raw.githubusercontent.com/Fox-doctor/Quiz-data/refs/heads/main/science_mir_nauki.json", "title": "Мир науки"},
            "2": {"url": "https://raw.githubusercontent.com/Fox-doctor/Quiz-data/refs/heads/main/science_chelovek_zemlya_vselennaya.json", "title": "Человек, Земля, Вселенная"},
            "3": {"url": "https://raw.githubusercontent.com/Fox-doctor/Quiz-data/refs/heads/main/science_veshestva_materialy.json", "title": "Вещества и материалы"},
            "4": {"url": "https://raw.githubusercontent.com/Fox-doctor/Quiz-data/refs/heads/main/science_zhivaya_nezhivaya_priroda.json", "title": "Живая/Неживая природа"},
            "5": {"url": "https://raw.githubusercontent.com/Fox-doctor/Quiz-data/refs/heads/main/science_energia_dvizhenie.json", "title": "Энергия и движение"},
            "6": {"url": "https://raw.githubusercontent.com/Fox-doctor/Quiz-data/refs/heads/main/science_ekologia_ekosistemy.json", "title": "Экология и экосистемы"},
            "7": {"url": "https://raw.githubusercontent.com/Fox-doctor/Quiz-data/refs/heads/main/science_politicheskaya_karta.json", "title": "Политическая карта"}
        }
    },
    "Английский": {"in_development": True},
    "Математика": {"in_development": True},
    "Количественная характеристика": {"in_development": True},
    "Казахский язык": {"in_development": True},
    "Русский язык": {"in_development": True}
}

def show_subject_menu(root):
    """Отображает главное меню выбора предмета."""
    # Очистка окна
    for widget in root.winfo_children():
        widget.destroy()
    tk.Label(root, text="Выберите предмет:", font=("Arial", 14)).pack(pady=10)
    # Для каждого предмета создаём кнопку:
    for subject, info in subjects.items():
        if "subcategories" in info:
            tk.Button(root, text=subject, font=("Arial", 12),
                      command=lambda s=subject, sub=info["subcategories"]: show_subcategory_menu(root, s, sub)
                      ).pack(pady=5)
        else:
            tk.Button(root, text=subject, font=("Arial", 12),
                      command=lambda s=subject: subject_in_development(root, s)
                      ).pack(pady=5)
    tk.Button(root, text="Выход", font=("Arial", 12), command=root.quit).pack(pady=10)

def show_subcategory_menu(root, subject, subcategories):
    """Отображает меню подразделов для выбранного предмета (например, Естествознание)."""
    # Очистка окна
    for widget in root.winfo_children():
        widget.destroy()
    tk.Label(root, text=f"Выберите подраздел предмета {subject}:", font=("Arial", 14)).pack(pady=10)
    for key, sub in subcategories.items():
        tk.Button(root,
                  text=f"{key} - {sub['title']}",
                  font=("Arial", 12),
                  command=lambda u=sub["url"]: start_quiz(root, u)
                  ).pack(pady=5)
    tk.Button(root, text="Назад", font=("Arial", 12), command=lambda: show_subject_menu(root)).pack(pady=10)

def subject_in_development(root, subject):
    """Показывает сообщение о том, что раздел находится в разработке."""
    messagebox.showinfo("Информация", f"Раздел '{subject}' в разработке")
    # После закрытия сообщения остаёмся в главном меню
    show_subject_menu(root)

def choose_category():
    """Запускает главное меню выбора предмета."""
    root = tk.Tk()
    root.title("Выбор предмета")
    show_subject_menu(root)
    root.mainloop()

if __name__ == "__main__":
    choose_category()
