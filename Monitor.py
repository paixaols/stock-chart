# -*- coding: utf-8 -*-
from datetime import datetime

from matplotlib import style
style.use('ggplot')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.dates as mdates

from mplfinance.original_flavor import candlestick_ohlc

import os
import requests

import pandas as pd

import tkinter as tk

from gerenciador import Gerenciador_de_Ativos
import recursos as rec

monitor_stock = 'monstock'
monitor_mercado = 'monmercado'
monitor_moeda = 'monmoeda'

# TODO: gerenciamento de carteira (usar nested pie).
# TODO: deslocar datas para meio dia, deve melhorar identificação dos candles.

class Monitor(tk.Frame):
    def __init__(self, parent, controller, nome, dim = '11'):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.contr = controller
        self.nlin = int(dim[0])
        self.ncol = int(dim[1])
        self.df = [None]*self.nlin*self.ncol
        self.labels = [(None, None, None)]*self.nlin*self.ncol# Labels e título
        
        self.grid_rowconfigure(0, weight = 1)
        self.grid_columnconfigure(0, weight = 1)
        
        self.container = tk.Frame(self)
        self.container.grid(row = 0, column = 0, sticky = 'nsew')
        
        self.ax_list = []
        for l in range(self.nlin):
            for c in range(self.ncol):
                self.container.grid_rowconfigure(2*l, weight = 1)
                self.container.grid_columnconfigure(c, weight = 1)
                
                fig = Figure(figsize = (6, 5), dpi = 100)
                ax = fig.add_subplot(111)
                
                ax.annotate('No data', (0.5, 0.5), xycoords = 'axes fraction')
                
                canvas = FigureCanvasTkAgg(fig, self.container)
                canvas.draw()
                canvas.get_tk_widget().grid(row = 2*l, column = c, sticky = 'nsew')
                
                toolbar_miniframe = tk.Frame(self.container)
                toolbar_miniframe.grid(row = 2*l+1, column = c, sticky = 'w')
                NavigationToolbar2Tk(canvas, toolbar_miniframe).pack(side = 'right', padx = 10)
                
                self.ax_list.append({'ax': ax, 'canvas': canvas})
    
    def resize_window(self, df):
        janela = self.contr.janela_grafica.get()
        if janela == 'max':
            return df
        hoje = pd.to_datetime('today').normalize()
        ultima_data = hoje-pd.Timedelta(janela)
        return df[df['Date'] > ultima_data]
    
    def set_labels(self, labelx, labely, title, axis = 0):
        self.labels[axis] = (labelx, labely, title)
    
    def candle(self, df, ax, fmt="%Y-%m-%d"):
        ohlc = df.copy()# Evita SettingWithCopyWarning.
        ohlc.loc[:,'Date'] = df['Date'].apply(mdates.date2num)
        ax.xaxis_date()
        ax.xaxis.set_major_formatter(mdates.DateFormatter(fmt))
#        plt.xticks(rotation=45)
        candlestick_ohlc(ax, ohlc.values, width=.6, colorup = 'b')
    
    def refresh(self):
        for axis in range(len(self.ax_list)):
            df = self.resize_window(self.df[axis])
            ax = self.ax_list[axis]['ax']
            canvas = self.ax_list[axis]['canvas']
            ax.clear()
            
            # Cotações
            tipo = self.contr.tipo_grafico.get()
            if tipo == 'candlestick':
                self.candle(df, ax)
            elif tipo == 'linha':
                df.plot(ax = ax, x = 'Date', y = 'Close', logy = True, legend = False)
            
            # Destacar último preço.
            last_price = df['Close'].iloc[0]
            last_day = df['Date'].iloc[0].date()
            
            ax.axhline(last_price, ls = '-', alpha = 0.2, color = 'gray')
            ax.axvline(last_day, ls = '-', alpha = 0.2, color = 'gray')
            bbox_prop = dict(boxstyle = 'round', fc = 'w', ec = 'k', lw = 1)
            font_prop = {'size': 12}
            
            ax.text(df['Date'].iloc[0], ax.get_ylim()[1], 
                    '{}'.format(last_day), 
                    bbox = bbox_prop, 
                    fontdict = font_prop)
            ax.text(ax.get_xlim()[1], df['Close'].iloc[0], 
                    '{:.2f}'.format(last_price), 
                    bbox = bbox_prop, 
                    fontdict = font_prop)
            
            # Labels title
            ax.set_xlabel(self.labels[axis][0])
            ax.set_ylabel(self.labels[axis][1])
            ax.set_title(self.labels[axis][2])
            
            canvas.draw()
    
    def plot(self, df, tipo = 'candlestick', axis = 0):
        try:
            ax = self.ax_list[axis]['ax']
            canvas = self.ax_list[axis]['canvas']
        except:
            return 'Axis not found'
        ax.clear()
        
        self.df[axis] = df
        
        df = self.resize_window(df)
        
        # Cotações
        if tipo == 'candlestick':
            self.candle(df, ax)
        elif tipo == 'linha':
            df.plot(ax = ax, x = 'Date', y = 'Close', logy = True, legend = False)
        else:
            return 'Tipo {} desconhecido, deve ser candlestick ou linha'.format(tipo)
        
        # Destacar último preço.
        last_price = df['Close'].iloc[0]
        last_day = df['Date'].iloc[0].date()
        
        ax.axhline(last_price, ls = '-', alpha = 0.2, color = 'gray')
        ax.axvline(last_day, ls = '-', alpha = 0.2, color = 'gray')
        bbox_prop = dict(boxstyle = 'round', fc = 'w', ec = 'k', lw = 1)
        font_prop = {'size': 12}
        
        ax.text(df['Date'].iloc[0], ax.get_ylim()[1], 
                '{}'.format(last_day), 
                bbox = bbox_prop, 
                fontdict = font_prop)
        ax.text(ax.get_xlim()[1], df['Close'].iloc[0], 
                '{:.2f}'.format(last_price), 
                bbox = bbox_prop, 
                fontdict = font_prop)
        
        # Labels & title
        ax.set_xlabel(self.labels[axis][0])
        ax.set_ylabel(self.labels[axis][1])
        ax.set_title(self.labels[axis][2])
        
        canvas.draw()

class Application(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        
        self.init_var()
        
        self.container = tk.Frame(self, borderwidth = 1, relief = 'groove')
        self.container.pack(side = 'top', fill = 'both', expand = True)
        
        self.frame_control = tk.Frame(self.container, borderwidth = 1, relief = 'groove')
        self.frame_control.pack(side = 'left', fill = 'both')
        
        self.frame_chart = tk.Frame(self.container, borderwidth = 1, relief = 'groove')
        self.frame_chart.pack(side = 'right', fill = 'both', expand = True)
        self.frame_chart.grid_rowconfigure(1, weight = 1)
        self.frame_chart.grid_columnconfigure(0, weight = 1)
        
        self.init_frame_control()
        self.init_frame_chart()
        
        self.mostrar_monitor()
        
        self.init_cadastro_ativos()
        self.update()
        self.entry_ticker.focus_set()
        
        self.fechamento = pd.to_datetime(rec.horario_de_fechamento_pregao).time()
    
    def mostrar_monitor(self):
        m = self.monitor_ativo.get()
        moni = self.monitores[m]
        moni.tkraise()
    
    def init_var(self):
        self.msg = tk.StringVar()
        self.monitores = {}
        self.monitor_ativo = tk.StringVar()
        self.monitor_ativo.set(monitor_stock)
        self.tipo_grafico = tk.StringVar()
        self.tipo_grafico.set('candlestick')
        self.entry_ticker_txtvar = tk.StringVar()
        self.janela_grafica = tk.StringVar()
        self.janela_grafica.set('180 day')
    
    def init_frame_control(self):
        tk.Label(self.frame_control, text = rec.label_ticker).pack()
        self.entry_ticker = tk.Entry(self.frame_control, textvariable = self.entry_ticker_txtvar)
        self.entry_ticker.pack()
        self.entry_ticker.bind('<Return>', self.callback_ticker_return_key)
        
        tk.Button(self.frame_control, text = 'Ativos', command = self.abrir_gerenciador_de_ativos).pack(pady = 30)
        
        group_plot_window = tk.LabelFrame(self.frame_control, text = 'Período')
        group_plot_window.pack(fill = 'both', expand = False, padx = 5)
        tk.Radiobutton(group_plot_window, text = '1 mês', variable = self.janela_grafica, value = '30 day', command = self.refresh_plot).pack(anchor = 'w')
        tk.Radiobutton(group_plot_window, text = '3 meses', variable = self.janela_grafica, value = '90 day', command = self.refresh_plot).pack(anchor = 'w')
        tk.Radiobutton(group_plot_window, text = '6 meses', variable = self.janela_grafica, value = '180 day', command = self.refresh_plot).pack(anchor = 'w')
        tk.Radiobutton(group_plot_window, text = '1 ano', variable = self.janela_grafica, value = '365 day', command = self.refresh_plot).pack(anchor = 'w')
        tk.Radiobutton(group_plot_window, text = '5 anos', variable = self.janela_grafica, value = '1825 day', command = self.refresh_plot).pack(anchor = 'w')
        tk.Radiobutton(group_plot_window, text = 'Max.', variable = self.janela_grafica, value = 'max', command = self.refresh_plot).pack(anchor = 'w')
        
        group_plot_type = tk.LabelFrame(self.frame_control, text = 'Gráfico')
        group_plot_type.pack(fill = 'both', expand = False, padx = 5)
        tk.Radiobutton(group_plot_type, text = 'Candlestick', variable = self.tipo_grafico, value = 'candlestick').pack(anchor = 'w')
        tk.Radiobutton(group_plot_type, text = 'Linha', variable = self.tipo_grafico, value = 'linha').pack(anchor = 'w')
        
        group_selec_monitor = tk.LabelFrame(self.frame_control, text = 'Monitorar')
        group_selec_monitor.pack(fill = 'both', expand = False, padx = 5)
        tk.Radiobutton(group_selec_monitor, text = 'Ações', variable = self.monitor_ativo, value = monitor_stock, command = self.select_monitor).pack(anchor = 'w')
        tk.Radiobutton(group_selec_monitor, text = 'Mercados', variable = self.monitor_ativo, value = monitor_mercado, command = self.select_monitor).pack(anchor = 'w')
        tk.Radiobutton(group_selec_monitor, text = 'Moedas', variable = self.monitor_ativo, value = monitor_moeda, command = self.select_monitor).pack(anchor = 'w')
    
    def init_frame_chart(self):
        tk.Label(self.frame_chart, textvar = self.msg).grid(row = 0, column = 0, sticky = 'ew', padx = 10)
        
        for nome, dim in ((monitor_stock, '11'), (monitor_mercado, '22'), (monitor_moeda, '12')):
            moni = Monitor(self.frame_chart, self, nome, dim)
            self.monitores[nome] = moni
            moni.grid(row = 1, column = 0, sticky = 'nsew')
        
        # TODO: plot cursor lines.
    
    def init_cadastro_ativos(self):
        try:
            with open(rec.arq_ativos, 'r', encoding = 'utf8') as f:
                txt = f.read()
                self.ativos = {}
                for line in txt.split('\n'):
                    if len(line) == 0:
                        continue
                    a, d, m = line.split('~')
                    self.ativos[a] = {'descr':d, 'mercado':m}
        except:
            self.ativos = {}
    
    def abrir_gerenciador_de_ativos(self):
        top = tk.Toplevel()
        top.wm_title(rec.titulo_janela_gerenciador)
        top.resizable(False, False)
        top.ativos = self.ativos
        Gerenciador_de_Ativos(top, self)
        top.focus_set()
        top.bind_all('<Escape>', lambda event: top.destroy())
        top.wait_window()
    
    def refresh_plot(self):
        self.msg.set('')
        moni = self.monitor_ativo.get()
        ticker = self.entry_ticker_txtvar.get().upper()
        if moni == monitor_stock:
            if ticker in self.ativos:
                self.monitores[moni].refresh()
            self.entry_ticker.selection_range(0, 'end')
        else:
            self.monitores[moni].refresh()
    
    def select_monitor(self):
        self.msg.set('')
        mon = self.monitor_ativo.get()
        if mon == monitor_stock:
            self.entry_ticker.configure(state = 'normal')
        elif mon == monitor_mercado:
            self.entry_ticker.configure(state = 'disabled')
            self.update_mercados()
        else:
            self.entry_ticker.configure(state = 'disabled')
            self.update_moedas()
        
        self.mostrar_monitor()
    
    def check_data_update(self, arq):
        last_update = datetime.fromtimestamp(os.path.getmtime(arq))
        agora = datetime.today()
        dia_semana = agora.weekday()# seg = 0, dom = 6
        if dia_semana < 5:# seg a sex
            if agora.time() < self.fechamento:# Mercado aberto
                return True
            else:# Mercado fechado
                if last_update.date() == agora.date():# Já atualizou hj
                    if last_update.time() < self.fechamento:
                        return True
                    else:
                        return False
                else:# Não atualizou hj
                    return True
        else:# fim de semana
            if last_update.date() == agora.date():
                return False
            else:
                return True
    
    def update_mercados(self):
        # index_info = {'IBOV':{'ticker':'%5EBVSP', 'fname':'^BVSP.csv'},
        #               'S&P 500':{'ticker':'%5EGSPC', 'fname':'^GSPC.csv'}}
        
        tipo = self.tipo_grafico.get()
        
        # IBOV - https://finance.yahoo.com/quote/%5EBVSP/history?p=%5EBVSP
        arq = os.path.join(rec.folder_index, '^BVSP.csv')
        update = self.check_data_update(arq)
        if update:
            df_novo = self.baixar_dados_historicos('%5EBVSP')
            if df_novo is not None:
                self.merge_data(df_novo, arq)
        df = pd.read_csv(arq, parse_dates = ['Date'])
        self.monitores[monitor_mercado].set_labels('', '', 'IBOV')
        self.monitores[monitor_mercado].plot(df, tipo = tipo)
        
        # IFIX - https://finance.yahoo.com/quote/IFIX.SA/history?p=IFIX.SA
        arq = os.path.join(rec.folder_index, 'IFIX.SA.csv')
        if update:
            df_novo = self.baixar_dados_historicos('IFIX.SA')
            if df_novo is not None:
                self.merge_data(df_novo, arq)
        df = pd.read_csv(arq, parse_dates = ['Date'])
        self.monitores[monitor_mercado].set_labels('', '', 'IFIX', axis = 1)
        self.monitores[monitor_mercado].plot(df, tipo = tipo, axis = 1)
        
        # SP500 - https://finance.yahoo.com/quote/%5EGSPC/history?p=%5EGSPC
        arq = os.path.join(rec.folder_index, '^GSPC.csv')
        if update:
            df_novo = self.baixar_dados_historicos('%5EGSPC')
            if df_novo is not None:
                self.merge_data(df_novo, arq)
        df = pd.read_csv(arq, parse_dates = ['Date'])
        self.monitores[monitor_mercado].set_labels('', '', 'S&P 500', axis = 2)
        self.monitores[monitor_mercado].plot(df, tipo = tipo, axis = 2)
    
    def update_moedas(self):
        # currency_info = {'Dólar':{'ticker':'BRL%3DX', 'fname':'BRL=X.csv'},
        #                  'Euro':{'ticker':'EURBRL%3DX', 'fname':'EURBRL=X.csv'}}
        
        tipo = self.tipo_grafico.get()
        
        # Dólar - https://finance.yahoo.com/quote/BRL%3DX/history?p=BRL%3DX
        arq = os.path.join(rec.folder_currency, 'BRL=X.csv')
        update = self.check_data_update(arq)
        if update:
            df_novo = self.baixar_dados_historicos('BRL%3DX')
            if df_novo is not None:
                self.merge_data(df_novo, arq)
        df = pd.read_csv(arq, parse_dates = ['Date'])
        self.monitores[monitor_moeda].set_labels('', '', 'Dólar')
        self.monitores[monitor_moeda].plot(df, tipo = tipo)
        
        # Euro - https://finance.yahoo.com/quote/EURBRL%3DX/history?p=EURBRL%3DX
        arq = os.path.join(rec.folder_currency, 'EURBRL=X.csv')
        if update:
            df_novo = self.baixar_dados_historicos('EURBRL%3DX')
            if df_novo is not None:
                self.merge_data(df_novo, arq)
        df = pd.read_csv(arq, parse_dates = ['Date'])
        self.monitores[monitor_moeda].set_labels('', '', 'Euro', axis = 1)
        self.monitores[monitor_moeda].plot(df, tipo = tipo, axis = 1)
    
    def callback_ticker_return_key(self, event):
        self.msg.set('')

        ticker = self.entry_ticker_txtvar.get().upper()
        if ticker in self.ativos:
            arq = os.path.join(rec.folder_historical_data, ticker+'.csv')
            update = self.check_data_update(arq)
            mercado = self.ativos[ticker]['mercado']
            if update:
                self.msg.set(rec.msg_atualizando_cotacao)
                df_novo = self.baixar_dados_historicos(ticker, classe = 'stock', mercado = mercado)
                if df_novo is None:
                    self.msg.set(rec.msg_erro_download)
                else:
                    self.msg.set(rec.msg_cotacao_atualizada)
                    self.merge_data(df_novo, arq)
            df = pd.read_csv(arq, parse_dates = ['Date'])
            if mercado == 'Brasil':
                labely = 'Real'
            else:
                labely = 'Dólar'
            title = '{}: {}'.format(ticker, self.ativos[ticker]['descr'])
            self.monitores[monitor_stock].set_labels('', labely, title, axis = 0)
            self.monitores[monitor_stock].plot(df, tipo = self.tipo_grafico.get())
        else:
            self.msg.set(rec.msg_ativo_nao_cadastrado)
        
        self.entry_ticker.selection_range(0, 'end')
    
    def merge_data(self, df_novo, arq):
        ultima_data = df_novo['Date'].iloc[-1]
        df = pd.read_csv(arq, parse_dates = ['Date'])
        df.drop(df[df['Date'] >= ultima_data].index, inplace = True)
        df = df_novo.append(df)
        df.reset_index(drop = True, inplace = True)
        df.to_csv(arq, index = False)
    
    def baixar_dados_historicos(self, ticker, classe = None, mercado = None):
        '''Baixa os dados históricos de um ativo do yahoo finance. Retorna um 
        dataframe com os dados ou None caso ocorra erro no download.'''
        if classe == 'stock' and mercado == 'Brasil':
            ticker += '.SA'
        url = 'https://finance.yahoo.com/quote/{}/history?p={}'.format(ticker, ticker)
        try:
            # lista_dfs = pd.read_html(url)
            header = {
              "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36",
              "X-Requested-With": "XMLHttpRequest"
            }
            page = requests.get(url, headers = header)
            lista_dfs = pd.read_html(page.text)
        except:
            return None
        df = lista_dfs[0].copy()
        if 'Close*' in df.columns:# Dividendos, desdobramentos e grupamentos.
            df.drop_duplicates(subset = 'Date', inplace = True)
            df.rename(columns = {'Close*': 'Close', 'Adj Close**': 'Adj Close'}, inplace = True)
            df.drop(df.index[-1], inplace = True)
        
        # Data é baixada no formato 'Oct 03, 2020' ('%b %d, %Y'), converter para datetime.
        df['Date'] = df['Date'].apply(pd.to_datetime)
        
        # O df pode ter dados faltando, a conversão pra float vai falhar.
        df = df[df['Adj Close'] != '-']
        df['Open'] = df['Open'].apply(float)
        df['High'] = df['High'].apply(float)
        df['Low'] = df['Low'].apply(float)
        df['Close'] = df['Close'].apply(float)
        
        df.reset_index(drop = True, inplace = True)
        return df

if not os.path.isdir(rec.folder_historical_data):
    # Importante garantir que a pasta existe mesmo vazia, ou o pd.to_csv 
    # não funciona.
    os.makedirs(rec.folder_historical_data)

app = Application()
app.state('zoomed')
app.bind_all('<Escape>', lambda event: app.destroy())
app.mainloop()
