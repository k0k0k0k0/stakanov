from collections import Counter
import csv
import time
import os
from tkinter import *
from tkinter import ttk, filedialog, messagebox
from tksheet import Sheet
import threading

import stakanov
import waffle_graph

class StakanovGUI:
    def __init__(self, root):
        # сделаем доступным для всех функций массив с файлами 
        self.all_items_in_folder = []
        self.files_by_size = Counter()
        # Список столбцов, по которым разрешено искать filter_file_tree: сейчас только по path и extension
        # ничего другого значимого в датасете пока нет
        self.to_search = [0, 1]

        # пустой кастомный путь к csv
        self.custom_csv_path = ''

        root.title("СтаХанов v. 1.0")
        root.geometry("1300x600")

        photo = PhotoImage(file='stakhanov.png')
        root.wm_iconphoto(False, photo)

        # Основная рамка
        main_frame = ttk.Frame(root)
        main_frame.grid(column=0, row=0, sticky='nsew')

        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)

        # общие статус-бары
        self.status_bar = ttk.Label(main_frame, text="", anchor="w")
        self.right_info_bar = ttk.Label(main_frame, text="", anchor="w")
        self.status_bar.grid(row=4, sticky="ew", pady=(0, 5))
        self.right_info_bar.grid(row=4, column=1, sticky="ew", pady=(0, 5))

        menu_bar = Menu(main_frame)

        # Меню "Файл"
        file_menu = Menu(menu_bar, tearoff=False)
        file_menu.add_command(label="Указать путь к индексируемой папке", command=self.choose_directory_path)
        file_menu.add_command(label="Указать свой путь для CSV", command=self.set_custom_csv_path)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=root.quit)
        menu_bar.add_cascade(label="Файл", menu=file_menu)

        # Меню "Действия"
        actions_menu = Menu(menu_bar, tearoff=False)
        actions_menu.add_command(label="Индексировать", command=lambda: self.start_indexing(directory_entry.get()))
        menu_bar.add_cascade(label="Действия", menu=actions_menu)


        # Меню "О программе"
        help_menu = Menu(menu_bar, tearoff=False)
        help_menu.add_command(label="О программе", command=self.about_program)
        menu_bar.add_cascade(label="Справка", menu=help_menu)

        # Устанавливаем строку меню
        root.config(menu=menu_bar)

        # Notebook для вкладок
        notebook = ttk.Notebook(main_frame)
        
        # Вкладка "Список файлов"
        tab_file_listing = ttk.Frame(notebook)
        notebook.add(tab_file_listing, text="Список файлов")
        
        # Вкладка "Статистика"
        tab_statistics = ttk.Frame(notebook)
        notebook.add(tab_statistics, text="Статистика")

        # Вкладка "Визуализации"
        self.tab_visualizations = ttk.Frame(notebook)
        notebook.add(self.tab_visualizations, text="Визуализации")

        notebook.grid(column=0, row=0, columnspan=3, sticky='nsew')
       
        # Элементы для вкладки "Список файлов"
        directory_label = ttk.Label(tab_file_listing, text="Путь к папке:")
        
        self.directory_entry_path = StringVar()
        directory_entry = ttk.Entry(tab_file_listing, textvariable=self.directory_entry_path)
        start_button = ttk.Button(tab_file_listing, text="Индексировать и выгрузить в CSV", default="active", command=lambda: self.start_indexing(directory_entry.get()))
        
        self.use_custom_csv_path = BooleanVar()
        use_custom_csv_path_checkbox = ttk.Checkbutton(tab_file_listing, text='Собственный путь для CSV', variable=self.use_custom_csv_path, onvalue=True, offvalue=False)

        self.progress_bar = ttk.Progressbar(tab_file_listing, mode='indeterminate', length=200)
        #tab_file_listing_sep = ttk.Separator(tab_file_listing, orient='horizontal')
        self.search_query = ttk.Entry(tab_file_listing)
        search_query_label = ttk.Label(tab_file_listing, text="Поиск по списку файлов:")
        self.file_tree = Sheet(tab_file_listing,
                               row_index = 0,
                               show_row_index=False,
                               row_index_width=0,
                               default_row_index_width=0,
                               theme = "light",)

        directory_label.grid(row=0, column=0, padx=5, pady=5)
        directory_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        start_button.grid(row=0, column=2, padx=5, pady=5, ipadx=30)
        use_custom_csv_path_checkbox.grid(row=0, column=3, padx=5, pady=5, ipadx=15)
        self.progress_bar.grid(row=0, column=4, sticky="ew", padx=5, pady=5)
        #tab_file_listing_sep.grid(row=1, columnspan=5, sticky="ew")
        search_query_label.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        self.search_query.grid(row=1, column=1, columnspan=4, sticky="ew", padx=10, pady=5)
        self.file_tree.grid(row=2, columnspan=5, sticky='nswe', padx=5, pady=5)
        
        tab_file_listing.columnconfigure(1, weight=1)
        tab_file_listing.rowconfigure(2, weight=1)

      
        # Элементы для вкладки "Статистика"
        extension_stats_label = ttk.Label(tab_statistics, text="Статистика по расширениям в каталоге")
        extension_stats_label.grid(row=0, column=0, padx=20, pady=20)
        size_stats_label = ttk.Label(tab_statistics, text="10 самых больших файлов")
        size_stats_label.grid(row=0, column=1, padx=20, pady=20)

        self.extension_stats = Sheet(tab_statistics,
                               row_index = 0,
                               show_row_index=False,
                               row_index_width=0,
                               default_row_index_width=0,
                               theme = "light",
                               headers=['Расширение', 'Всего файлов']
                               )
        self.extension_stats.grid(row=2, column=0, sticky='nswe', padx=5, pady=5)

        self.size_stats = Sheet(tab_statistics,
                               row_index = 0,
                               show_row_index=False,
                               row_index_width=0,
                               default_row_index_width=0,
                               theme = "light",
                               headers=['Путь к файлу', 'Размер']
                               )
        self.size_stats.grid(row=2, column=1, sticky='nswe', padx=5, pady=5)

        tab_statistics.columnconfigure(1, weight=1)
        tab_statistics.rowconfigure(2, weight=1)

        # Элементы для вкладки "Визуализации"
        visualization_label = ttk.Label(self.tab_visualizations, text="Здесь будут визуализации")
        visualization_label.grid(row=0, column=0, padx=20, pady=20)
        self.disk_waffle = ttk.Label(self.tab_visualizations)
        self.disk_waffle.grid(row=1, columnspan=5, rowspan=2, sticky='nswe')
        self.disk_waffle['image'] = PhotoImage(file='waffle.png')
        
        # привязки по клавиатуре и фокусу
        directory_entry.focus()
        root.bind('<Return>', lambda e: start_button.invoke())
        self.search_query.bind("<KeyRelease>", self.filter_file_tree)

        # Привязываем событие <Expose> ко всем дочерним элементам Notebook
        #for child in notebook.winfo_children():
        #    child.bind('<Expose>', self.on_expose)
        self.tab_visualizations.bind('<FocusIn>', self.on_expose)

    def display_waffle(self, data: Counter):
        #self.tab_visualizations, dict(self.files_by_size)
        # надо подготовить данные для визуализации
        # взять Х самых больших, перевести в мегабайты
        data = {file:round(size/1024, 2) for file, size in dict(data.most_common(20)).items()}
        print(data)
        waffle_graph.build_waffle(data) # сохранили waffle.png

        imgobj = PhotoImage(file='waffle.png')
        self.disk_waffle['image'] = imgobj
        root.update_idletasks()
    
    def on_expose(self, event):  
        # если открыта вкладка Visualizations
        if event.widget is self.tab_visualizations:
            self.display_waffle(self.files_by_size)

    def show_status_message(self, message):
        self.status_bar.config(text=message)

    def clear_status_bar(self):
        self.status_bar.config(text="")

    def show_info_message(self, message):
        self.right_info_bar.config(text=message)

    def about_program(self):
        messagebox.showinfo(title='О программе', message='СтаХанов v. 1.0\nНакодил Николай Андреев.')
    
    def choose_directory_path(self):
        directory_selected = filedialog.askdirectory()
        if directory_selected:
            self.directory_entry_path.set(directory_selected)
        else: # не выбрали ничего
            self.show_status_message("Папка для сканирования не выбрана")

    def set_custom_csv_path(self):
        self.use_custom_csv_path.set(True)
        self.custom_csv_path = filedialog.askdirectory()

    def start_indexing(self, directory_path, action=None):
        global tic # для тайминга 

        if not str(directory_path):
            self.show_status_message(f"Ошибка! Укажите папку для сканирования.")
            return
        elif not os.path.exists(directory_path):
            self.show_status_message(f"Ошибка! Папка {directory_path} не найдена.")
            return

        tic = time.perf_counter()

        self.santa_maria = stakanov.ResearchVessel(directory_path)

        self.progress_bar.start()

        self.file_tree.total_rows(0) #will delete rows if set to less than current data rows
        self.file_tree.total_columns(0)

        # чтобы отображать прогресс бар в интерфейсе, нужно засунуть процессинг в другой поток, иначе все будет просто подвисать
        thread = threading.Thread(target=self.scan_directory_thread, args=(directory_path,))
        self.show_status_message(f"Папка {directory_path} индексируется...")
        thread.start()


    def scan_directory_thread(self, directory_path):
        global tic
        try:
            count = 0
            field_names = self.santa_maria.Researcher.keyList
            self.file_tree.headers(field_names)

            self.files_by_size.clear()
            self.all_items_in_folder.clear()

            if self.use_custom_csv_path.get() and not self.custom_csv_path:
                filename_selected = filedialog.asksaveasfilename()
                if filename_selected:
                    path_to_csv = filename_selected # + '/file_listing.csv'
                else: # не выбрали ничего
                    path_to_csv = 'file_listing.csv'
            else: # путь по умолчанию
                path_to_csv = 'file_listing.csv'

            # время нужно засечь еще раз, иначе выбор файла тоже будет учитываться в elapsed
            tic = time.perf_counter()

            with open(path_to_csv, 'w', encoding='utf8', newline='') as f:
                writer = csv.DictWriter(f, field_names, extrasaction='raise')
                writer.writeheader()

                # радикально быстрее вначале собрать из итератора fetch_file_objects список списков по всем файлам,
                # а потом нарисовать из них tksheet, чем поштучно добавлять и отрисовывать.
                for info in self.santa_maria.fetch_file_objects():
                    writer.writerow(info)
                    
                    # fetch_file_objects() отдает словарь, нам для tksheet нужен список строго по порядку столбцов                  
                    sorted_values = [info.get(key) for key in self.santa_maria.Researcher.keyList]
                    self.all_items_in_folder.append(sorted_values)

                    # используем Counter не по назначению: пишем размер файла в числовое значение вместо подсчета  
                    self.files_by_size[info.get('path')] = info.get('size', 0)          

                    count += 1
                    if count % 200 == 0:
                        root.update_idletasks()  # обновляем интерфейс каждые 200 элементов
            
            # перерисовываем основной листинг и делаем авторесайз столбцов
            self.file_tree.set_sheet_data(self.all_items_in_folder, reset_col_positions=True, reset_row_positions=True, redraw=True)
            self.file_tree.set_all_cell_sizes_to_text()
            
            # обновляем статистику по расширениям на вкладке "Статистика"
            # self.santa_maria.extension_counter.most_common() - Counter отдает список всех кортежей (расширение, количество)
            self.extension_stats.set_sheet_data(self.santa_maria.extension_counter.most_common(), reset_col_positions=True, reset_row_positions=True, redraw=True)

            # этот трюк позволяет быстро вытащить n "самых частых" (т.е. самых больших) файлов
            self.size_stats.set_sheet_data(self.files_by_size.most_common(10), reset_col_positions=True, reset_row_positions=True, redraw=True)
            self.size_stats.set_all_cell_sizes_to_text()

        except Exception as e:
            self.show_status_message(str(e))
        finally:
            self.progress_bar.stop()
            self.clear_status_bar()
            toc = time.perf_counter()
            self.show_status_message(f"Папка {directory_path} успешно проиндексирована за {toc - tic:0.4f} с.")
            self.show_info_message(f"Последняя индексация: {time.ctime()}")

   
    def filter_file_tree(self, event=None):
        query = self.search_query.get().strip().lower()
    
        # получаем все строки из таблицы
        all_rows = self.file_tree.get_total_rows()
        
        # фильтруем строки по указанным столбцам
        if query != "":
            rows_to_display = []
            for i in range(all_rows):
                row = self.file_tree.get_row_data(i)
                if row is None:
                    continue
                if any(query in str(row[col]).lower() for col in self.to_search):
                    rows_to_display.append(i)
            #print(rows_to_display)
            # обновляем видимые строки
            self.file_tree.display_rows(rows=rows_to_display, all_displayed=False, redraw=True)
        else:
            # показываем все строки, если запрос пустой
            self.file_tree.display_rows("all", redraw=True)
        

if __name__ == "__main__":
    tic = time.time() # вводим глобальную, чтобы работали таймеры
    root = Tk()
    app = StakanovGUI(root)
    root.mainloop()