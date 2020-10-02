# -*- coding: utf-8 -*-
import os

import tkinter as tk
import pandas as pd

#from datetime import datetime
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from matplotlib import style
style.use('ggplot')

from gerenciador import Gerenciador_de_Ativos
import recursos as rec

# TODO: gerenciamento de carteira (usar nested pie).

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
        
        self.importar_ativos_cadastrados()
        self.update()
        self.entry_ticker.focus_set()
        
        self.fechamento = pd.to_datetime(rec.horario_de_fechamento_pregao).time()
    
    def init_frame_control(self):
        tk.Label(self.frame_control, text = rec.label_ticker).pack()
        self.txtvar_entry_ticker = tk.StringVar()
        self.entry_ticker = tk.Entry(self.frame_control, textvariable = self.txtvar_entry_ticker)
        self.entry_ticker.pack()
        self.entry_ticker.bind('<Return>', self.entry_return_key_callback)
        
        tk.Button(self.frame_control, text = 'Ativos', command = self.abrir_gerenciador_de_ativos).pack(pady = 30)
        
        grupo_config_plot = tk.LabelFrame(self.frame_control, text = 'Gráfico')
        grupo_config_plot.pack(fill = 'both', expand = False, padx = 5)
        self.janela_grafica = tk.StringVar()
        self.janela_grafica.set('180 day')
        tk.Radiobutton(grupo_config_plot, text = '1 mês', variable = self.janela_grafica, value = '30 day').pack(anchor = 'w')
        tk.Radiobutton(grupo_config_plot, text = '3 meses', variable = self.janela_grafica, value = '90 day').pack(anchor = 'w')
        tk.Radiobutton(grupo_config_plot, text = '6 meses', variable = self.janela_grafica, value = '180 day').pack(anchor = 'w')
        tk.Radiobutton(grupo_config_plot, text = '1 ano', variable = self.janela_grafica, value = '365 day').pack(anchor = 'w')
        tk.Radiobutton(grupo_config_plot, text = '5 anos', variable = self.janela_grafica, value = '1825 day').pack(anchor = 'w')
        tk.Radiobutton(grupo_config_plot, text = 'Max.', variable = self.janela_grafica, value = 'max').pack(anchor = 'w')
    
    def init_frame_chart(self):
        self.msg = tk.StringVar()
        tk.Label(self.frame_chart, textvar = self.msg).pack()
        
        self.fig = Figure(figsize = (6, 5), dpi = 100)
        self.ax = self.fig.add_subplot(111)
        
        self.canvas = FigureCanvasTkAgg(self.fig, self.frame_chart)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill = 'both', expand = True)
        
        toolbar_miniframe = tk.Frame(self.frame_chart)
        toolbar_miniframe.pack(side = 'left', padx = 10)
        
        NavigationToolbar2Tk(self.canvas, toolbar_miniframe).pack(side = 'right')
        
        # TODO: plot cursor lines.
    
    def set_window(self, janela):
        self.janela_grafica = janela
    
    def importar_ativos_cadastrados(self):
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
    
    def entry_return_key_callback(self, event):
        self.msg.set('')
        
        ticker = self.txtvar_entry_ticker.get().upper()
        if ticker in self.ativos:
            fname = os.path.join(rec.historical_data_folder, ticker+'.csv')
            df = pd.read_csv(fname, parse_dates = ['Date'])
            if self.atualizar_cotacao(df):
                self.msg.set(rec.msg_atualizando_cotacao)
                df_novo = self.baixar_dados_historicos(ticker)
                if df_novo is None:
                    self.msg.set(rec.msg_erro_download)
                else:
                    self.msg.set(rec.msg_cotacao_atualizada)
                    
                    
                    
                    
                    ultima_data = df_novo['Date'].iloc[-1]
                    df.drop(df[df['Date'] >= ultima_data].index, inplace = True)
                    df = df_novo.append(df)
                    df.reset_index(drop = True, inplace = True)
                    df.to_csv(os.path.join(rec.historical_data_folder, ticker+'.csv'), index = False)
                    
                    
                    
                    self.plot(ticker, df)
            else:
                self.plot(ticker, df)
        else:
            self.msg.set(rec.msg_ativo_nao_cadastrado)
        
        self.entry_ticker.selection_range(0, 'end')
    
    def baixar_dados_historicos(self, ticker):
        '''Baixa os dados históricos de um ativo do yahoo finance. Retorna um 
        dataframe com os dados ou None caso ocorra erro no download.'''
        mercado = self.ativos[ticker]['mercado']
        if mercado == 'Brasil':
            url = 'https://finance.yahoo.com/quote/{}.SA/history?p={}.SA'.format(ticker, ticker)
        else:
            url = 'https://finance.yahoo.com/quote/{}/history?p={}'.format(ticker, ticker)
        try:
            lista_dfs = pd.read_html(url)
        except:
            return None
        df = lista_dfs[0].copy()
        if 'Close*' in df.columns:# Pagamento de dividendos.
            df.drop_duplicates(subset = 'Date', inplace = True)
            df.reset_index(drop = True, inplace = True)
            df.rename(columns = {'Close*': 'Close', 'Adj Close**': 'Adj Close'}, inplace = True)
            df.drop(df.index[-1], inplace = True)
        df['Date'] = df['Date'].apply(lambda d: pd.to_datetime(d))
        df['Close'] = df['Close'].apply(lambda n: float(n))
        
        return df
    
    def atualizar_cotacao(self, df):
        '''Verificar necessidade de atualizar cotação do ativo.'''
        data_ultima_cotacao = df['Date'][0]
        
        agora = pd.to_datetime('today')# datetime
        hora = agora.time()# time
        hoje = agora.date()# date
        
        dia_da_semana = hoje.weekday()
        
        if dia_da_semana == 5:# Sábado
            ultimo_pregao_fechado = hoje-pd.Timedelta('1 days')
        elif dia_da_semana == 6:# Domingo
            ultimo_pregao_fechado = hoje-pd.Timedelta('2 days')
        else:
            if hora > self.fechamento:
                ultimo_pregao_fechado = hoje
            else:
                if dia_da_semana == 0:# Segunda
                    ultimo_pregao_fechado = hoje-pd.Timedelta('3 days')
                else:
                    ultimo_pregao_fechado = hoje-pd.Timedelta('1 days')
        
        if data_ultima_cotacao == ultimo_pregao_fechado:
            return False# Não atualizar.
        else:
            return True# Atualizar dados.
    
    def plot(self, ticker, df):
        def aplicar_janela(df):
            if self.janela_grafica.get() == 'max':
                return df
            hoje = pd.to_datetime('today').normalize()
            ultima_data = hoje-pd.Timedelta(self.janela_grafica.get())
            return df[df['Date'] > ultima_data]
        
        dados = aplicar_janela(df)
        # TODO: exibir na tela valores OHLC no período
        self.ax.clear()
        self.ax.set_title('{}: {}'.format(ticker, self.ativos[ticker]['descr']))
        if self.ativos[ticker]['mercado'] == 'Brasil':
            self.ax.set_ylabel(rec.moeda_brasil)
        else:
            self.ax.set_ylabel(rec.moeda_eua)
        dados.plot(ax = self.ax, x = 'Date', y = 'Close', logy = True, legend = False)
        self.canvas.draw()

if not os.path.isdir(rec.historical_data_folder):
    # Importante garantir que a pasta existe mesmo vazia, ou o pd.to_csv 
    # não funciona.
    os.makedirs(rec.historical_data_folder)

app = Application()
app.state('zoomed')
app.bind_all('<Escape>', lambda event: app.destroy())
app.mainloop()
