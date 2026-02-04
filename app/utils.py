import fitz
import tempfile
import os
import re

def cortar_pdf(caminho_original: str, intervalo: str):
    """
    Recebe o caminho do PDF e o intervalo.
    Retorna o CAMINHO do arquivo PDF recortado.
    """
    path_recorte = None
    try:
        # 1. Validação com Regex
        padrao = r"^\d+(?:-\d+)?(?:[;,]\d+(?:-\d+)?)*$"
        intervalo_limpo = intervalo.replace(" ", "")
        
        if not re.match(padrao, intervalo_limpo):
            raise ValueError(f"Formato de intervalo inválido: '{intervalo}'")

        # 2. Abrir Documentos
        doc = fitz.open(caminho_original)
        total_paginas = len(doc)
        doc_novo = fitz.open()

        # 3. Processar a string de intervalo
        partes = re.split(r'[;,]', intervalo_limpo)
        paginas_selecionadas = []

        for parte in partes:
            if '-' in parte:
                inicio, fim = map(int, parte.split('-'))
                p_start, p_end = min(inicio, fim), max(inicio, fim)
                for p in range(p_start, p_end + 1):
                    paginas_selecionadas.append(p)
            else:
                paginas_selecionadas.append(int(parte))

        # 4. Inserir páginas (removendo duplicatas e respeitando o limite do PDF)
        # Usamos set() para evitar que o usuário peça a mesma página duas vezes
        paginas_unicas = sorted(list(set(paginas_selecionadas)))
        
        for p in paginas_unicas:
            idx = p - 1 # Humano (1) para Máquina (0)
            if 0 <= idx < total_paginas:
                doc_novo.insert_pdf(doc, from_page=idx, to_page=idx)

        # 5. Salvar em um local temporário persistente para o Textract ler
        # Criamos o nome baseado no original para facilitar debug
        dir_temp = tempfile.gettempdir()
        path_recorte = os.path.join(dir_temp, f"recorte_{os.path.basename(caminho_original)}")
        
        doc_novo.save(path_recorte)
        
        doc.close()
        doc_novo.close()

        # 6. Limpeza do ORIGINAL (já que já temos o recorte)
        if os.path.exists(caminho_original):
            os.remove(caminho_original)

        return path_recorte

    except Exception as e:
        if path_recorte and os.path.exists(path_recorte):
            os.remove(path_recorte)
        raise e