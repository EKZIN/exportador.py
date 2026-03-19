import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from collections import Counter

BG = "#1e1e1e"
FG = "white"
ENTRY_BG = "#2b2b2b"
BTN_BG = "#3c3f41"
BTN_ACTIVE = "#5a5a5a"

root = tk.Tk()
root.title("EXPORTADOR TXT PARA JSON")
root.configure(bg=BG)
root.geometry("900x600")
root.resizable(False, False)

fonte = ("Segoe UI", 10)

json_var = tk.StringVar()
txt_var = tk.StringVar()
saida_json_var = tk.StringVar()
chave_var = tk.StringVar(value="IDPECA")
chaves_disponiveis = []

root.grid_rowconfigure(6, weight=1)
root.grid_columnconfigure(1, weight=1)


def normalizar(valor):
    if not valor:
        return ""
    return str(valor).strip().replace(" ", "").upper()

def selecionar_json():
    caminho = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if caminho:
        json_var.set(caminho)
        carregar_chaves(caminho)

def selecionar_txt():
    caminho = filedialog.askopenfilename(filetypes=[("TXT files", "*.txt")])
    if caminho:
        txt_var.set(caminho)

def salvar_json():
    caminho = filedialog.asksaveasfilename(defaultextension=".json")
    if caminho:
        saida_json_var.set(caminho)

def coletar_chaves(obj, chaves=None):
    if chaves is None:
        chaves = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            chaves.add(k)
            coletar_chaves(v, chaves)
    elif isinstance(obj, list):
        for item in obj:
            coletar_chaves(item, chaves)
    return chaves

def carregar_chaves(caminho_json):
    global chaves_disponiveis
    try:
        with open(caminho_json, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        chaves_disponiveis = sorted(coletar_chaves(dados))
        combo_chaves['values'] = chaves_disponiveis
        if "IDPECA" in chaves_disponiveis:
            chave_var.set("IDPECA")
        elif chaves_disponiveis:
            chave_var.set(chaves_disponiveis[0])
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível carregar chaves do JSON:\n{e}")

def coletar_valores(obj, chave):
    
    chave_normalizada = normalizar(chave)

    if isinstance(obj, dict):
        for k, v in obj.items():
            if normalizar(k) == chave_normalizada:
                yield normalizar(v)
            if isinstance(v, (dict, list)):
                yield from coletar_valores(v, chave)

    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, (dict, list)):
                yield from coletar_valores(item, chave)

def filtrar_json(obj, chave, valores_validos):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.upper() == chave.upper() and normalizar(v) in valores_validos:
                return obj

        novo = {}
        for k, v in obj.items():
            filtrado = filtrar_json(v, chave, valores_validos)
            if filtrado:
                novo[k] = filtrado

        return novo if novo else None

    elif isinstance(obj, list):
        nova_lista = [filtrar_json(i, chave, valores_validos) for i in obj]
        nova_lista = [i for i in nova_lista if i]
        return nova_lista if nova_lista else None

    return None

def processar():
    arquivo_json = json_var.get()
    arquivo_txt = txt_var.get()
    saida_json = saida_json_var.get()
    chave = chave_var.get().strip()

    if not arquivo_json or not arquivo_txt:
        messagebox.showwarning("Aviso", "Selecione JSON e TXT.")
        return
    if not chave:
        messagebox.showwarning("Aviso", "Selecione o campo para filtro.")
        return

    try:
        with open(arquivo_txt, 'r', encoding='utf-8') as f:
            ids_txt = [normalizar(linha) for linha in f if linha.strip()]
        ids_unicos_txt = set(ids_txt)

        with open(arquivo_json, 'r', encoding='utf-8') as f:
            dados = json.load(f)

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao carregar arquivos:\n{e}")
        return

    valores_json = list(coletar_valores(dados, chave))
    ids_json = set(valores_json)

    validos = ids_unicos_txt & ids_json
    invalidos = ids_unicos_txt - ids_json

    contador = Counter(ids_txt)
    total_repeticoes = sum(v - 1 for v in contador.values() if v > 1)
    qtd_ids_repetidos = sum(1 for v in contador.values() if v > 1)

    dados_filtrados = filtrar_json(dados, chave, ids_unicos_txt)

    resultado_text.delete(1.0, tk.END)

    resultado_text.insert(tk.END, "===== RESUMO =====\n")
    resultado_text.insert(tk.END, f"Campo usado para filtro: {chave}\n")
    resultado_text.insert(tk.END, f"Total de valores no TXT: {len(ids_txt)}\n")
    resultado_text.insert(tk.END, f"Valores únicos no TXT: {len(ids_unicos_txt)}\n")
    resultado_text.insert(tk.END, f"Valores encontrados no JSON: {len(validos)}\n")
    resultado_text.insert(tk.END, f"Valores NÃO encontrados no JSON: {len(invalidos)}\n")

    if invalidos:
        resultado_text.insert(tk.END, "\nLista de valores NÃO encontrados:\n")
        for cod in sorted(invalidos):
            resultado_text.insert(tk.END, f"{cod}\n")

    resultado_text.insert(tk.END, "\n===== REPETIDOS =====\n")
    resultado_text.insert(tk.END, f"Valores repetidos no TXT: {qtd_ids_repetidos}\n")
    resultado_text.insert(tk.END, f"Total de repetições excedentes: {total_repeticoes}\n")

    repetidos = {k: v for k, v in contador.items() if v > 1}
    if repetidos:
        resultado_text.insert(tk.END, "\nLista de valores repetidos:\n")
        for cod, qtd in sorted(repetidos.items()):
            resultado_text.insert(tk.END, f"{cod} (x{qtd})\n")

    #resultado_text.insert(tk.END, "\n===== JSON COMPLETO (Preview limitado) =====\n")
    #try:
    #    preview = json.dumps(dados, indent=2, ensure_ascii=False)
    #    resultado_text.insert(tk.END, preview[:5000])  # limita tamanho
    #    if len(preview) > 5000:
    #        resultado_text.insert(tk.END, "\n... (JSON cortado para preview)\n")
    #except:
    #    resultado_text.insert(tk.END, "Erro ao exibir JSON")

    if saida_json and dados_filtrados:
        try:
            with open(saida_json, 'w', encoding='utf-8') as f:
                json.dump(dados_filtrados, f, indent=4, ensure_ascii=False)
            resultado_text.insert(tk.END, f"\nJSON filtrado e salvo em:\n{saida_json}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar JSON:\n{e}")


def label(texto, row):
    tk.Label(root, text=texto, bg=BG, fg=FG, font=fonte)\
        .grid(row=row, column=0, sticky="e", padx=5, pady=5)

def entry(var, row):
    tk.Entry(root, textvariable=var, width=60,
             bg=ENTRY_BG, fg=FG, insertbackground=FG, font=fonte)\
        .grid(row=row, column=1, padx=5, pady=5)

def button(texto, comando, row, col):
    tk.Button(root, text=texto, command=comando,
              bg=BTN_BG, fg=FG, activebackground=BTN_ACTIVE,
              font=fonte)\
        .grid(row=row, column=col, padx=5, pady=5)

label("Arquivo JSON:", 0)
entry(json_var, 0)
button("Selecionar", selecionar_json, 0, 2)

label("Arquivo TXT:", 1)
entry(txt_var, 1)
button("Selecionar", selecionar_txt, 1, 2)

label("Salvar JSON filtrado:", 2)
entry(saida_json_var, 2)
button("Salvar como", salvar_json, 2, 2)

label("Campo para filtro:", 3)
combo_chaves = ttk.Combobox(root, textvariable=chave_var, values=chaves_disponiveis, width=57)
combo_chaves.grid(row=3, column=1, padx=5, pady=5)

tk.Button(root,
          text="Executar Tudo",
          command=processar,
          bg="#4CAF50",
          fg="white",
          font=("Segoe UI", 11, "bold"))\
    .grid(row=4, column=0, columnspan=3, pady=10)

resultado_text = tk.Text(
    root,
    bg=BG,
    fg=FG,
    insertbackground=FG,
    font=("Consolas", 10),
    wrap="word"
)
resultado_text.grid(row=6, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

root.mainloop()