# -*- coding: utf-8 -*-
#from datetime import datetime

import os

#import pandas as pd
import tkinter as tk

from recursos import arq_ativos, historical_data_folder

class Gerenciador_de_Ativos(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.contr = controller
        
        self.container = tk.Frame(parent, borderwidth = 1, relief = 'groove')
        self.container.pack(side = 'top', fill = 'both', expand = True)
        
        self.init_window()
        
        self.listar_ativos_cadastrados()
        self.e1.focus_set()
        
        # TODO: Exibir número de ativos cadastrados.
    
    def init_window(self):
        tk.Label(self.container, text = 'Código').pack(pady = 5)
        self.txtvar_entry_ticker = tk.StringVar()
        self.e1 = tk.Entry(self.container, textvar = self.txtvar_entry_ticker)
        self.e1.pack()
        
        tk.Label(self.container, text = 'Descrição').pack(pady = 5)
        self.txtvar_entry_descr = tk.StringVar()
        self.e2 = tk.Entry(self.container, textvar = self.txtvar_entry_descr)
        self.e2.pack()
        
        tk.Label(self.container, text = 'País').pack(pady = 5)
        mercados = ['-Escolher-', 'Brasil', 'EUA']
        self.txtvar_mercado = tk.StringVar()
        self.txtvar_mercado.set(mercados[0])
        tk.OptionMenu(self.container, self.txtvar_mercado, *mercados).pack()
        
        self.e1.bind('<Return>', lambda e: self.check_entry_info())
        self.e2.bind('<Return>', lambda e: self.check_entry_info())

        tk.Button(self.container, text = 'Adicionar', command = self.check_entry_info).pack(pady = 5)
        
        self.msg = tk.StringVar()
        tk.Label(self.container, textvar = self.msg).pack()
        
        self.lbox = tk.Listbox(self.container, width = 30, height = 13)
        self.lbox.pack(padx = 5, pady = 5)
    
    def listar_ativos_cadastrados(self):
        for a in sorted(list(self.contr.ativos.keys())):
            self.lbox.insert('end', '{}: {}'.format(a, self.contr.ativos[a]['descr']))
    
    def check_entry_info(self):
        if self.txtvar_entry_ticker.get() == '':
            tk.messagebox.showerror('Erro', 'Indicar o código do ativo.')
        else:
            ativo = self.txtvar_entry_ticker.get().upper()
            descricao = self.txtvar_entry_descr.get()
            mercado = self.txtvar_mercado.get()
            if ('~' in ativo) or ('~' in descricao):
                tk.messagebox.showwarning('Ops', 'Texto não deve conter caracter "~".')
            elif mercado == '-Escolher-':
                tk.messagebox.showwarning('Ops', 'Escolha um país.')
            elif ativo in self.contr.ativos:
                tk.messagebox.showwarning('Ops', 'Ativo já cadastrado.')
            else:
                df = self.contr.baixar_dados_historicos(ativo, mercado)
                if df is None:
                    tk.messagebox.showerror('Erro de download', 'Não foi possível baixar dados, tente mais tarde.')
                else:
                    self.msg.set('Dados de {} baixados.'.format(ativo))
                    self.atualizar_ativos(ativo, descricao, mercado)
                    self.salvar_ativos()
                    df.to_csv(os.path.join(historical_data_folder, ativo+'.csv'), index = False)
    
    def atualizar_ativos(self, ativo, descricao, mercado):
        '''Atualiza dicionário de ativos atualmente na memória.'''
        self.lbox.insert(0, '{}: {}'.format(ativo, descricao))
        self.contr.ativos[ativo] = {'descr':descricao, 'mercado':mercado}
        
        self.txtvar_entry_ticker.set('')
        self.txtvar_entry_descr.set('')
        self.txtvar_mercado.set('-Escolher-')
        self.e1.focus_set()
    
    def salvar_ativos(self):
        '''Exporta dicionário de ativos cadastrados.'''
        with open(arq_ativos, 'w', encoding = 'utf8') as f:
            for a in sorted(list(self.contr.ativos.keys())):
                d = self.contr.ativos[a]['descr']
                m = self.contr.ativos[a]['mercado']
                f.write('{}~{}~{}\n'.format(a, d, m))

if __name__ == '__main__':
    root = tk.Tk()
    
    try:
        with open(arq_ativos, 'r', encoding = 'utf8') as f:
            txt = f.read()
            root.ativos = {}
            for line in txt.split('\n'):
                if len(line) == 0:
                    continue
                a, d, m = line.split('~')
                root.ativos[a] = {'descr':d, 'mercado':m}
    except:
        root.ativos = {}
    
    Gerenciador_de_Ativos(root, root)
    root.bind_all('<Escape>', lambda event: root.destroy())
    root.mainloop()
