import csv
import time
import os

from os.path import join, splitext
from collections import Counter

import researchers



# прикрутим общую функцию-декоратор, которая печатает время выполнения
def timeit(fun):
    def newf(*arg, **kw):
        tic = time.perf_counter()
        res = fun(*arg, **kw)
        toc = time.perf_counter()
        print(f"Completed in {toc - tic:0.4f} seconds")
        return res
    return newf

def get_extension(file):
        extension = splitext(file)[1].lower()
        return extension if extension else "None"

class ExplorationTool:
    def __init__(self, path):
        self.path = path
    
    def files(self):
        for root, dirs, files in os.walk(self.path):
            for d in dirs:
                 yield join(root, d)
            for f in files:
                 yield join(root, f)


class ResearchVessel:
    # пусть будет лор про корабли и исследователей
    def __init__(self, path):
        self.ExplorationTool = ExplorationTool(path)
        self.Researcher = researchers.GeneralResearcher()
        # зачем инстацируем все при инициализации? м.б. только нужные при fetch_all_objects?
        self.XLSResearcher = researchers.ExcelResearcher()
        self.DOCResearcher = researchers.WordResearcher()
        self.ImgResearcher = researchers.ImageResearcher()
        self.PDFResearcher = researchers.PDFDocResearcher()
        self.VidResearcher = researchers.VideoResearcher()
        self.IsoFileResearcher = researchers.ISOResearcher()
        #как в этих наименованиях не путаться? инстанцировать циклом?
        self.path = path 
        self.extension_counter = Counter()

    
    def fetch_file_objects(self):  
        for f in self.ExplorationTool.files():

            all_extensions = []

            if not os.path.isdir(f): # если это файл\
                file_extension = get_extension(f)
                all_extensions.append(file_extension)
                match file_extension: # ветвление по специализированным рисерчерам
                    case ".xlsx": # | ".xls" не поддерживается!
                        info = self.XLSResearcher.get_info(f)
                    case '.docx': # | ".doc":
                        info = self.DOCResearcher.get_info(f)
                    case '.pdf':
                        info = self.PDFResearcher.get_info(f)
                    case '.jpg' | '.jpeg' | '.gif' | '.png':
                        info = self.ImgResearcher.get_info(f)
                    case '.avi':
                        info = self.VidResearcher.get_info(f)
                    case ".iso":
                        info = self.IsoFileResearcher.get_info(f)
                    case _: 
                        info = self.Researcher.get_info(f)
                
                info['extension']=file_extension
                info['is_folder']=False
                
            else: # это директорий
                info = self.Researcher.get_info(f)
                info['is_folder']=True
            
            info['path']=f # запишем имя файла в путь

            if info['is_container']==True: # это ISO-файл
                objects_list = info['contents'] # нужно распаковать список из contents
                #info['contents'] = 'unpacked below'
                yield info
                for nested_obj in objects_list:
                    all_extensions.append(nested_obj['extension'])
                    self.extension_counter.update(all_extensions)
                    yield nested_obj 
                    
            else: # это самый обычный файл
                self.extension_counter.update(all_extensions)
                yield info
                
        
    @timeit
    def display_folder_overview(self):
        # условная табличная красота: все равно потом, как я понимаю, будет пандас
        #print('{:^25}'.format('Filename') + " "*45 +"Size      Last Mod                      Additional Info")
        for info in self.fetch_file_objects():
            display_extension = info['extension'] if not info['is_folder'] else "FOLDER"
            #yield file, display_extension, info['size'], info['last_modified']
            yield info
            #yield (f"{file:105} {display_extension:6}    {info['size']:10}    {info['last_modified']}")
                
    # сейчас нерелевантно
    def print_file_info(self, f, info):
        display_extension = info['extension'] if not info['is_folder'] else "FOLDER"
        print(f"{f:65} {display_extension:6}    {info['size']:10}    {info['last_modified']}")
        #ну и любой уже сюда можно вставить вывод
    
        
    @timeit
    def save_as_csv(self, path_to_csv='file_listing.csv'):
        field_names = self.Researcher.infoDict.keys()

        
        with open(path_to_csv, 'w', encoding='utf8', newline='') as f:
            writer = csv.DictWriter(f, field_names, extrasaction='raise')
            writer.writeheader()
            for file_info in self.fetch_file_objects():
                #file_info['path']=file
                writer.writerow(file_info)



    # может быть полезен вот такой метод, чтобы оценить количество файлов разных расширений
    @timeit
    def extension_stats(self):
        all_extensions = []
        for f in self.ExplorationTool.files():
            file_extension = get_extension(f)
            
            all_extensions.append(file_extension)
        c = Counter(all_extensions)
        for item, cnt in c.items():
            print(f"{item:10} :", cnt)
        #return c


if __name__ == "__main__":
    santa_maria = ResearchVessel('P:/Work')
    
    for i in santa_maria.display_folder_overview():
        print(i)
    #santa_maria.extension_stats()
    #santa_maria.save_as_csv()


# глобально todo:
# обработка ошибок