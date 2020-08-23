# -*- coding: utf-8 -*-
import os

import tkinter as tk
import pandas as pd

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from matplotlib import style
style.use('ggplot')

from gerenciador import Gerenciador_de_Ativos
import recursos as rec

#lista_ativos = [ os.path.splitext(f)[0] for f in os.listdir(rec.historical_data_folder) if os.path.isfile(os.path.join(rec.historical_data_folder, f)) ]

class Application(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        
        self.container = tk.Frame(self, borderwidth = 1, relief = 'groove')
        self.container.pack(side = 'top', fill = 'both', expand = True)
        
        self.frame_control = tk.Frame(self.container, borderwidth = 1, relief = 'groove')
        self.frame_control.pack(side = 'left', fill = 'both')
        
        self.frame_chart = tk.Frame(self.container, borderwidth = 1, relief = 'groove')
        self.frame_chart.pack(side = 'right', fill = 'both', expand = True)
        
        self.init_frame_control()
        self.init_frame_chart()
        
        self.abrir_ativos_cadastrados()
        self.update()
        self.entry_ticker.focus_set()
    
    def abrir_ativos_cadastrados(self):
        try:
            with open(rec.arq_ativos, 'r', encoding = 'utf8') as f:
                txt = f.read()
                self.ativos = {}
                for line in txt.split('\n'):
                    if len(line) == 0:
                        continue
                    a, d, m = line.split('~')
                    self.ativos[a] = {'d':d, 'm':m}
        except:
            self.ativos = {}
    
    def init_frame_control(self):
        tk.Label(self.frame_control, text = rec.label_ticker).pack()
        self.txtvar_entry_ticker = tk.StringVar()
        self.entry_ticker = tk.Entry(self.frame_control, textvariable = self.txtvar_entry_ticker)
        self.entry_ticker.pack()
        self.entry_ticker.bind('<Return>', self.entry_return_key_callback)
        
        tk.Button(self.frame_control, text = 'Ativos', command = self.abrir_gerenciador_de_ativos).pack(pady = 30)
    
    def init_frame_chart(self):
        self.msg = tk.StringVar()
        tk.Label(self.frame_chart, textvar = self.msg).pack()
        
        self.fig = Figure(figsize = (6, 5), dpi = 100)
        self.ax = self.fig.add_subplot(111)
        
        self.canvas = FigureCanvasTkAgg(self.fig, self.frame_chart)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill = 'both', expand = True)
        
        toolbar_miniframe = tk.Frame(self.frame_chart)
        toolbar_miniframe.pack(side = 'left')
        NavigationToolbar2Tk(self.canvas, toolbar_miniframe).pack()
        
        # TODO: plot cursor lines.
    
    def abrir_gerenciador_de_ativos(self):
        top = tk.Toplevel()
        top.wm_title(rec.titulo_janela_gerenciador)
        top.resizable(False, False)
        top.ativos = self.ativos
        Gerenciador_de_Ativos(top, self)
        top.focus_set()
        top.bind_all('<Escape>', lambda event: top.destroy())
        top.wait_window()
    
    def entry_return_key_callback(self, event):
        self.msg.set('')
        ticker = self.txtvar_entry_ticker.get().upper()
        if ticker in self.ativos:
            fname = os.path.join(rec.historical_data_folder, ticker+'.csv')
            df = pd.read_csv(fname, parse_dates = ['Date'])
            self.plot(ticker, df)
        else:
            self.msg.set(rec.msg_ativo_nao_cadastrado)
        self.entry_ticker.selection_range(0, 'end')
    
    def plot(self, ticker, dados):
        self.ax.clear()
        self.ax.set_title('{}: {}'.format(ticker, self.ativos[ticker]['d']))
        if self.ativos[ticker]['m'] == 'Brasil':
            self.ax.set_ylabel('BRL')
        else:
            self.ax.set_ylabel('USD')
        dados.plot(ax = self.ax, x = 'Date', y = 'Close', logy = True, legend = False)
        self.canvas.draw()

app = Application()
app.state('zoomed')
app.bind_all('<Escape>', lambda event: app.destroy())
app.mainloop()
