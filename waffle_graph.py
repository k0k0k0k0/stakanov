import matplotlib.pyplot as plt
from pywaffle import Waffle

#from tkinter import * 
from matplotlib.figure import Figure 
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def build_waffle(data: dict):
    #data = {'Democratic': 48, 'Republican': 46, 'Libertarian': 3}
    fig = plt.figure(
        FigureClass=Waffle, 
        columns=30,
        rows=25, 
        values=data, 
        figsize=(12,6),
        rounding_rule='floor',
        #colors=("#983D3D", "#232066", "#DCB732"),
        #title={'label': 'Vote Percentage in 2016 US Presidential Election', 'loc': 'left'},
        #labels=["{0} ({1}%)".format(k, v) for k, v in data.items()],
        legend={'loc': 'upper right', 'ncols': 1, 'bbox_to_anchor':(1.7, 1), 'framealpha': 0, 'fontsize': 'small'},
    )
    #fig.gca().get_legend().remove()
    fig.tight_layout()
    fig.gca().set_facecolor('#EEEEEE')
    fig.set_facecolor('#EEEEEE')
    fig.savefig('waffle.png')



def build_waffle_canvas(master_container, data: dict): #не работает для ttk.Label
    #data = {'Democratic': 48, 'Republican': 46, 'Libertarian': 3}
    fig = plt.figure(
        FigureClass=Waffle, 
        rows=5, 
        values=data, 
        colors=("#983D3D", "#232066", "#DCB732"),
        title={'label': 'Vote Percentage in 2016 US Presidential Election', 'loc': 'left'},
        labels=["{0} ({1}%)".format(k, v) for k, v in data.items()],
        legend={'loc': 'lower left', 'bbox_to_anchor': (0, -0.4), 'ncol': len(data), 'framealpha': 0}
    )
    fig.gca().set_facecolor('#EEEEEE')
    fig.set_facecolor('#EEEEEE')

    canvas = FigureCanvasTkAgg(fig, master = master_container)   
    canvas.draw() 
    
    waffle_chart = canvas.get_tk_widget()
    return waffle_chart

if __name__ == "__main__":
    data = {'p:/work\\gonka\\kp_fullmap.jpg': 10.2, 'p:/work\\university\\diplom\\lit\\Филиппов - Лингвистика текста.djvu': 6.38, 'p:/work\\gonka\\0000285e.jpeg': 5.57, 'p:/work\\human\\OmegaT_1.8.1_06_Windows_without_JRE.exe': 5.49, 'p:/work\\university\\diplom.rar': 4.67, 'p:/work\\bg\\реестр.doc': 3.94, 'p:/work\\university\\baeva\\IMG_3427.JPG': 3.29, 'p:/work\\university\\baeva\\IMG_3423.JPG': 3.27, 'p:/work\\gonka\\kp_fullmap.ozfx3': 3.27, 'p:/work\\university\\baeva\\IMG_3425.JPG': 3.25, 'p:/work\\human\\PTSansWeb.zip': 3.14, 'p:/work\\university\\baeva\\IMG_3428.JPG': 3.09, 'p:/work\\university\\baeva\\IMG_3426.JPG': 3.07, 'p:/work\\university\\baeva\\IMG_3424.JPG': 3.0, 'p:/work\\university\\kaminskaja\\Кася.zip': 2.95, 'p:/work\\aspir\\text\\IMG_0363.JPG': 1.53, 'p:/work\\university\\diplom\\lit\\oformlenie akta ugrozy\\5ballov-40311.rtf': 1.49, 'p:/work\\aspir\\text\\IMG_0359.JPG': 1.47, 'p:/work\\aspir\\text\\IMG_0360.JPG': 1.46, 'p:/work\\aspir\\text\\IMG_0365.JPG': 1.37}
    build_waffle(data)
    print('ГОТОВО')
