import datetime
import time
import os

from tqdm import tqdm
from os.path import join, getsize, splitext
from collections import Counter

# для обработки файловых типов
import openpyxl
import docx
from PIL import Image
#from PIL.ExifTags import TAGS
from pypdf import PdfReader
import cv2
from pydub.utils import mediainfo
from tinytag import TinyTag
import sys, pycdlib
import csv
#import ffmpeg



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
        self.Researcher = GeneralResearcher()
        # зачем инстацируем все при инициализации? м.б. только нужные при fetch_all_objects?
        self.XLSResearcher = ExcelResearcher()
        self.DOCResearcher = WordResearcher()
        self.ImgResearcher = ImageResearcher()
        self.PDFResearcher = PDFDocResearcher()
        self.VidResearcher = VideoResearcher()
        self.IsoFileResearcher = ISOResearcher()
        #как в этих наименованиях не путаться? инстанцировать циклом?
        self.path = path 
        self.extension_counter = Counter()
    
    def fetch_file_objects(self):  
        for f in self.ExplorationTool.files():
            #assert os.path.isfile(f) # убедимся, что файл существует, а то мало ли -- не работает, если подать в него директорий

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
                    #case ".iso":
                    #    info = self.IsoFileResearcher.get_info(f)
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
                info['contents'] = 'unpacked below'
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
        # решил вынести функцию вывода в отдельный метод (хорошее решение?)
            # интуитивно — да, с т.з. читаемости и будущей расширяемости (напр., можно переиспользовать,
            # вводить доп. параметры типа настройки колонок), но по науке как?
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
            # как лучше всего не теряться в коде?
        #return c


class GeneralResearcher:
    def __init__(self): # создаем пустой словарь с заранее определенным списком ключей-параметров файлов
        self.keyList = ['path', 'extension', 'is_folder', "size", "last_modified", "created_time",
                         'is_container', 'contents', 
                         'within_container', 'parent_object',
                    "Office_last_mod_time", "Office_last_mod_by",
                    'XLS_num_sheets',
                    'PDF_num_pages', 'PDF_layout',
                    "MP3_track title", "MP3_artist", "MP3_duration", 'AUD_bitrate',
                    'IMG_size', 'IMG_dpi', "IMG_device"]
        self.infoDict = {key: None for key in self.keyList}
        #return info
    
    def get_info(self, file):
        file_info = self.infoDict.copy() # получаем пустой словарь с ключами-параметрами
        file_info['last_modified'] = time.ctime(os.path.getmtime(file)) #наполняем
        file_info['size'] = round(getsize(file)/1024)
        return file_info

    # имеет вот такое смысл? с учетом того, что и внутри self будем вызывать?
    # def get_extension(self, file):
    #     extension = os.path.splitext(file)[1].lower()
    #     return extension if extension else "None"

    
# далее ряд "специализированных" рисерчеров: для XLS, DOC и графических файлов
class ExcelResearcher(GeneralResearcher):
    def get_info(self, file):
        file_info = super(ExcelResearcher, self).get_info(file)
        # здесь это же то же самое, что file_info = Researcher.get_info(file), разве нет?

        wb = openpyxl.load_workbook(file)
        file_info['XLS_num_sheets'] = len(wb.sheetnames)

        # все библиотеки отдают время по-разному, м.б. глобальную функцию для его обработки ввести?
        # сейчас для простоты перевожу все в ctime
        file_info['created_time'] = datetime.date.ctime(wb.properties.created)
        file_info['Office_last_mod_time'] = datetime.date.ctime(wb.properties.modified)
        file_info['Office_last_mod_by'] = wb.properties.lastModifiedBy

        return file_info
    

class WordResearcher(GeneralResearcher):
    def get_info(self, file):
        file_info = super(WordResearcher, self).get_info(file)

        doc = docx.Document(file)
        prop = doc.core_properties
        ### todo: количество страниц и формат
        file_info['created_time'] = datetime.date.ctime(prop.created)
        file_info['Office_last_mod_time'] = datetime.date.ctime(prop.modified)
        file_info['Office_last_mod_by'] = prop.last_modified_by

        return file_info
    

class ImageResearcher(GeneralResearcher):
    def get_info(self, file):
        file_info = super(ImageResearcher, self).get_info(file)

        image = Image.open(file)
        exifdata = image.getexif()
        # тут отдается что-то вроде словаря
        #for tag_id in exifdata:
            # в экзифе ключи — числа, но можно достать названия
            #tag = TAGS.get(tag_id, tag_id)
            #print(f"{tag:25}: {exifdata.get(tag_id)}")  

        file_info['created_time'] = exifdata.get(306, "None")
        file_info['IMG_size'] = image.size
        file_info['IMG_dpi'] = image.info.get('dpi', 'No data')
        file_info['IMG_device'] = exifdata.get(271, "No data")  # это модель устройства, с которого снимали
    
        return file_info
    
class VideoResearcher(GeneralResearcher):
    def get_info(self, file):
        file_info = super(VideoResearcher, self).get_info(file)

        vid = cv2.VideoCapture(file)
        file_info['VID_height'] = vid.get(cv2.CAP_PROP_FRAME_HEIGHT)
        file_info['VID_width'] = vid.get(cv2.CAP_PROP_FRAME_WIDTH)
    
        return file_info
    

class PDFDocResearcher(GeneralResearcher):
    def get_info(self, file):
        file_info = super(PDFDocResearcher, self).get_info(file)

        reader = PdfReader(file)
        file_info['PDF_num_pages'] = reader.get_num_pages()
        file_info['PDF_layout'] = reader.page_layout

        meta = reader.metadata
        file_info['created_time'] = datetime.date.ctime(meta.creation_date)
        file_info['Office_last_mod_time'] = datetime.date.ctime(meta.modification_date)
        file_info['Office_last_mod_by'] = meta.author

        return file_info
    

class MusicResearcher(GeneralResearcher):
    def get_info(self, file):
        file_info = super(MusicResearcher, self).get_info(file)

        mediainfo(file)
        file_info['AUD_bitrate'] = mediainfo['bit_rate']
        
        tag = TinyTag.get(file)
        file_info['MP3_track title'] = tag.title 
        file_info['MP3_artist'] = tag.albumartist
        file_info['MP3_duration'] = tag.duration
        
        return file_info
    
class ISOResearcher(GeneralResearcher):
    def get_info(self, file):
        file_info = super(ISOResearcher, self).get_info(file)
        file_info['is_container'] = True

        # Create a new PyCdlib object.
        iso = pycdlib.PyCdlib()

        # Open up a file object.  This causes PyCdlib to parse all of the metadata on the
        # ISO, which is used for later manipulation.
        iso.open(file)
        objects_list = []
        
        # Now iterate through each of the files on the root of the ISO, printing out
        # their names.
        
        for root, dirs, files in iso.walk(iso_path='/'):    # на каждый уровень вложенности
            for d in dirs:
                dir_researcher = GeneralResearcher()
                dir_info = dir_researcher.infoDict
                dir_info['path']= root+'/'+d
                dir_info['is_folder'] = True
                dir_info['within_container'] = True
                dir_info['parent_object'] = file
                objects_list.append(dir_info)
            for f in files:
                nested_file_researcher = GeneralResearcher()
                iso_nested_file_info = nested_file_researcher.infoDict
                iso_nested_file_info['path']= root+'/'+f[:-2]
                #iso_nested_file_info['AUD_bitrate'] = 9999999
                iso_nested_file_info['is_folder'] = False
                iso_nested_file_info['within_container'] = True
                iso_nested_file_info['parent_object'] = file
                iso_nested_file_info['extension'] = f[:-2].split(".")[1].lower() # потому что на выдаче FILENAME.FIL;1
                objects_list.append(iso_nested_file_info)
                

        # Close the ISO object.  After this call, the PyCdlib object has forgotten
        # everything about the previous ISO, and can be re-used.
        iso.close()

        file_info['contents'] = objects_list
        return file_info


if __name__ == "__main__":
    santa_maria = ResearchVessel('P:/Work')
    
    for i in santa_maria.display_folder_overview():
        print(i)
    #santa_maria.extension_stats()
    #santa_maria.save_as_csv()


# глобально todo:
# обработка ошибок