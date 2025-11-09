import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from ttkbootstrap import (
    Style, Frame, Button, Label, Entry, Combobox, Treeview, Scrollbar
)
from ttkbootstrap.constants import *

class ParquetEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Editor Parquet")
        self.root.geometry("1100x720")

        self.style = Style("flatly")
        self.df = None
        self.view_df = None
        self.file_path = None
        self.page_size = 100
        self.current_page = 0

        # ---------- TOPO: BOTÕES ----------
        btn_frame = Frame(self.root)
        btn_frame.pack(fill=X, padx=10, pady=5)

        Button(btn_frame, text="Abrir", command=self.abrir, bootstyle="primary").pack(side=LEFT, padx=5)
        Button(btn_frame, text="Salvar", command=self.salvar, bootstyle="success").pack(side=LEFT, padx=5)
        Button(btn_frame, text="Adicionar Linha", command=self.adicionar_linha, bootstyle="info").pack(side=LEFT, padx=5)
        Button(btn_frame, text="Excluir Linha", command=self.excluir_linha, bootstyle="danger").pack(side=LEFT, padx=5)
        Button(btn_frame, text="Filtrar por Coluna", command=self.abrir_filtro, bootstyle="warning").pack(side=LEFT, padx=5)
        Button(btn_frame, text="Sair", command=self.root.quit, bootstyle="secondary").pack(side=LEFT, padx=5)

        # ---------- BUSCA GLOBAL ----------
        search_frame = Frame(self.root)
        search_frame.pack(fill=X, padx=10, pady=(0, 5))

        Label(search_frame, text="Busca global:").pack(side=LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = Entry(search_frame, textvariable=self.search_var, width=40)
        self.search_entry.pack(side=LEFT)
        self.search_entry.bind("<KeyRelease>", self.on_search_change)
        Button(search_frame, text="Limpar", command=self.limpar_busca, bootstyle="secondary-outline").pack(side=LEFT, padx=5)

        # ---------- TREEVIEW ----------
        self.tree = Treeview(self.root, show="headings", bootstyle="info")
        self.tree.pack(fill=BOTH, expand=True, padx=10, pady=10)
        self.tree.bind("<Double-1>", self.editar_celula)
        self.tree.bind("<Delete>", self.excluir_linha)

        yscroll = Scrollbar(self.root, orient="vertical", command=self.tree.yview)
        yscroll.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=yscroll.set)

        # ---------- PAGINAÇÃO ----------
        pag_frame = Frame(self.root)
        pag_frame.pack(fill=X, padx=10, pady=(0, 5))

        self.prev_btn = Button(pag_frame, text="← Anterior", command=self.pag_anterior, bootstyle="secondary-outline")
        self.prev_btn.pack(side=LEFT, padx=5)

        self.page_label = Label(pag_frame, text="Página 0/0")
        self.page_label.pack(side=LEFT, padx=5)

        self.next_btn = Button(pag_frame, text="Próxima →", command=self.pag_proxima, bootstyle="secondary-outline")
        self.next_btn.pack(side=LEFT, padx=5)

        # ---------- STATUS RODAPÉ ----------
        status_frame = Frame(self.root)
        status_frame.pack(fill=X, padx=10, pady=(0, 8))
        self.status_label = Label(status_frame, text="Nenhum arquivo carregado.")
        self.status_label.pack(side=LEFT)

    # ---------- ABRIR ----------
    def abrir(self):
        file = filedialog.askopenfilename(filetypes=[("Arquivos Parquet", "*.parquet")])
        if not file:
            return
        try:
            self.df = pd.read_parquet(file)
            self.view_df = self.df
            self.file_path = file
            self.current_page = 0
            self.search_var.set("")
            self.carregar_tabela()
            self.update_status()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao abrir arquivo:\n{e}")

    # ---------- SALVAR ----------
    def salvar(self):
        if self.df is None:
            messagebox.showwarning("Aviso", "Nenhum arquivo aberto.")
            return
        try:
            file = filedialog.asksaveasfilename(
                initialfile=(self.file_path if self.file_path else ""),
                defaultextension=".parquet",
                filetypes=[("Arquivos Parquet", "*.parquet")]
            )
            if not file:
                return
            self.df.to_parquet(file)
            self.file_path = file
            messagebox.showinfo("Sucesso", f"Arquivo salvo em:\n{file}")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar arquivo:\n{e}")

    # ---------- CARREGAR ----------
    def carregar_tabela(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if self.view_df is None or self.view_df.empty:
            self.tree["columns"] = []
            self.page_label.config(text="Página 0/0")
            return

        total = len(self.view_df)
        total_pages = max(1, (total + self.page_size - 1) // self.page_size)
        start = self.current_page * self.page_size
        end = start + self.page_size
        df_page = self.view_df.iloc[start:end]

        self.tree["columns"] = list(df_page.columns)
        for col in df_page.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")
        for _, row in df_page.iterrows():
            self.tree.insert("", "end", values=list(row))

        self.page_label.config(text=f"Página {self.current_page + 1}/{total_pages}")
        self.prev_btn.config(state=(DISABLED if self.current_page == 0 else NORMAL))
        self.next_btn.config(state=(DISABLED if self.current_page >= total_pages - 1 else NORMAL))
        self.update_status()

    # ---------- STATUS ----------
    def update_status(self):
        if self.df is None:
            self.status_label.config(text="Nenhum arquivo carregado.")
        else:
            rows, cols = self.df.shape
            self.status_label.config(text=f"Total: {rows} linhas • {cols} colunas")

    # ---------- NAVEGAÇÃO ----------
    def pag_anterior(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.carregar_tabela()

    def pag_proxima(self):
        total_pages = max(1, (len(self.view_df) + self.page_size - 1) // self.page_size)
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.carregar_tabela()

    # ---------- EDITAR ----------
    def editar_celula(self, event):
        if self.view_df is None:
            return
        item = self.tree.identify_row(event.y)
        coluna = self.tree.identify_column(event.x)
        if not item or not coluna:
            return
        col_index = int(coluna.replace("#", "")) - 1
        col_name = self.view_df.columns[col_index]
        idx_local = int(self.tree.index(item))
        idx_view = self.current_page * self.page_size + idx_local
        valor_antigo = self.view_df.iloc[idx_view, col_index]
        entry = tk.Entry(self.root)
        entry.insert(0, str(valor_antigo))
        entry.focus()

        def salvar_edicao(e):
            novo_valor = entry.get()
            row_index = self.view_df.index[idx_view]
            self.df.at[row_index, col_name] = novo_valor
            self.view_df.at[row_index, col_name] = novo_valor
            self.tree.set(item, column=col_name, value=novo_valor)
            entry.destroy()
            self.update_status()

        entry.bind("<Return>", salvar_edicao)
        entry.bind("<Escape>", lambda e: entry.destroy())
        entry.place(x=event.x_root - self.root.winfo_rootx(), y=event.y_root - self.root.winfo_rooty())

    # ---------- BUSCA GLOBAL ----------
    def on_search_change(self, event=None):
        if self.df is None:
            return
        query = self.search_var.get().strip()
        if query == "":
            self.view_df = self.df
        else:
            df_str = self.df.astype(str)
            mask = df_str.apply(lambda col: col.str.contains(query, case=False, na=False)).any(axis=1)
            self.view_df = self.df[mask]
        self.current_page = 0
        self.carregar_tabela()

    def limpar_busca(self):
        if self.df is None:
            return
        self.search_var.set("")
        self.view_df = self.df
        self.current_page = 0
        self.carregar_tabela()

    # ---------- FILTRAR ----------
    def abrir_filtro(self):
        if self.df is None:
            messagebox.showwarning("Aviso", "Abra um arquivo primeiro.")
            return
        win = tk.Toplevel(self.root)
        win.title("Filtrar por Coluna")
        win.geometry("320x220")

        Label(win, text="Coluna:").pack(pady=5)
        coluna_cb = Combobox(win, values=list(self.df.columns), state="readonly")
        coluna_cb.pack(pady=5)
        Label(win, text="Valor contém:").pack(pady=5)
        valor_entry = Entry(win)
        valor_entry.pack(pady=5)

        def aplicar():
            col, val = coluna_cb.get(), valor_entry.get()
            if not col or val == "":
                messagebox.showwarning("Aviso", "Informe coluna e valor.")
                return
            mask = self.df[col].astype(str).str.contains(val, case=False, na=False)
            self.view_df = self.df[mask]
            self.current_page = 0
            self.search_var.set("")
            self.carregar_tabela()
            win.destroy()

        Button(win, text="Aplicar", command=aplicar, bootstyle="success").pack(pady=10)

    # ---------- ADICIONAR ----------
    def adicionar_linha(self):
        if self.df is None:
            messagebox.showwarning("Aviso", "Abra um arquivo primeiro.")
            return
        nova = {}
        for col in self.df.columns:
            val = simpledialog.askstring("Nova Linha", f"{col}:")
            if val is None:
                return
            nova[col] = val
        self.df = pd.concat([self.df, pd.DataFrame([nova])], ignore_index=True)
        self.view_df = self.df
        self.search_var.set("")
        self.current_page = (len(self.df) - 1) // self.page_size
        self.carregar_tabela()

    # ---------- EXCLUIR ----------
    def excluir_linha(self, event=None):
        if self.df is None or self.view_df is None:
            messagebox.showwarning("Aviso", "Abra um arquivo primeiro.")
            return
        selecionado = self.tree.selection()
        if not selecionado:
            return
        if not messagebox.askyesno("Confirmar", "Excluir linha(s) selecionada(s)?"):
            return
        indices = []
        for item in selecionado:
            idx_local = int(self.tree.index(item))
            idx_view = self.current_page * self.page_size + idx_local
            if idx_view < len(self.view_df):
                row_index = self.view_df.index[idx_view]
                indices.append(row_index)
        if indices:
            self.df = self.df.drop(indices).reset_index(drop=True)
            self.view_df = self.df
            self.search_var.set("")
            self.current_page = 0
            self.carregar_tabela()

if __name__ == "__main__":
    root = tk.Tk()
    app = ParquetEditor(root)
    root.mainloop()
