import time
import datetime
import os

from os.path import getsize

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
    
    def get_info(self, file):
        file_info = self.infoDict.copy() # получаем пустой словарь с ключами-параметрами
        file_info['last_modified'] = time.ctime(os.path.getmtime(file)) #наполняем
        file_info['size'] = round(getsize(file)/1024) # в кб
        return file_info

    # имеет вот такое смысл? с учетом того, что и внутри self будем вызывать?
    # def get_extension(self, file):
    #     extension = os.path.splitext(file)[1].lower()
    #     return extension if extension else "None"

    
# далее ряд "специализированных" рисерчеров: для XLS, DOC и графических файлов
class ExcelResearcher(GeneralResearcher):
    def get_info(self, file):
        file_info = super(ExcelResearcher, self).get_info(file)

        wb = openpyxl.load_workbook(file)
        file_info['XLS_num_sheets'] = len(wb.sheetnames)

        # все библиотеки отдают время по-разному, сейчас для простоты перевожу все в ctime
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
        
        for root, dirs, files in iso.walk(iso_path='/'):    # на каждый уровень вложенности
            for d in dirs:
                dir_researcher = GeneralResearcher()
                iso_dir_info = dir_researcher.infoDict
                iso_dir_info['path']= file+root+'/'+d
                iso_dir_info['is_folder'] = True
                iso_dir_info['size'] = 0 # не сумеем определить размер вложенных файлов
                iso_dir_info['within_container'] = True
                iso_dir_info['parent_object'] = file
                objects_list.append(iso_dir_info)
            for f in files:
                nested_file_researcher = GeneralResearcher()
                iso_nested_file_info = nested_file_researcher.infoDict
                iso_nested_file_info['path']= file+root+'/'+f[:-2]
                iso_nested_file_info['size'] = 0 # не сумеем определить размер вложенных файлов
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