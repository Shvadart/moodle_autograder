import curses

def main(stdscr):
    # Настройки
    curses.curs_set(0)  # Скрыть курсор
    stdscr.keypad(True)  # Включить спец. клавиши (стрелки)
    
    options = ["Проверить ответы", "Настройки", "Выход"]
    current_row = 0  # Текущая выбранная строка

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()  # Размеры терминала
        
        # Вывод заголовка
        title = "Moodle Evaluator"
        stdscr.addstr(0, w//2 - len(title)//2, title, curses.A_BOLD)
        
        # Вывод пунктов меню
        for idx, option in enumerate(options):
            y = h//2 - len(options)//2 + idx
            x = w//2 - len(option)//2
            if idx == current_row:
                stdscr.addstr(y, x, option, curses.A_REVERSE)  # Выделение
            else:
                stdscr.addstr(y, x, option)
        
        # Обработка клавиш
        key = stdscr.getch()
        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(options)-1:
            current_row += 1
        elif key == curses.KEY_ENTER or key in [10, 13]:  # Enter
            if current_row == len(options)-1:  # Выход
                break
            stdscr.addstr(h-1, 0, f"Выбрано: {options[current_row]}", curses.A_ITALIC)
            stdscr.refresh()
            stdscr.getch()  # Ждём нажатия
        
    stdscr.clear()
    stdscr.addstr(0, 0, "Программа завершена.")
    stdscr.refresh()
    stdscr.getch()

if __name__ == "__main__":
    curses.wrapper(main)  # Обработка ошибок и очистка