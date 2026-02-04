import csv
import re
import io
import os
import pandas as pd
from textractor import Textractor
from textractor.data.constants import TextractFeatures

def processar_pdf_textractor(bucket, caminho_local_arquivo, regiao='us-east-2'):
    
    extractor = Textractor(region_name=regiao)

    #nome_arquivo = os.path.basename(caminho_local_arquivo)
    #s3_path = f"s3://{bucket}/{nome_arquivo}"

    print(f"--- Fazendo upload e iniciando análise de: {caminho_local_arquivo} ---")
    
    document = extractor.start_document_analysis(
        file_source=caminho_local_arquivo,
        s3_upload_path=f"s3://{bucket}/",
        features=[TextractFeatures.TABLES],
        save_image=False 
    )
    return document

def tratar_valor_numerico(texto):
    if not texto: return ""
    texto_limpo = str(texto).strip().replace('\n', ' ')
    if re.match(r'^-?\d+([\d\.]*,\d+)?$', texto_limpo):
        return texto_limpo.replace('.', '')
    return texto_limpo

def exportar_tabelas_unificadas_csv(doc, nome_base="resultado"):
    if not doc or not hasattr(doc, 'tables'):
        print("ERRO: Documento não contém tabelas.")
        return

    print(f"DEBUG: O Textract encontrou {len(doc.tables)} tabela(s).")
    todas_as_linhas = []
    
    for i, table in enumerate(doc.tables):
        try:
            # 1. Convertemos para um DataFrame do Pandas (Caminho oficial da lib)
            df = table.to_pandas()
            
            # 2. Agora usamos o to_csv do PANDAS, que aceita index=False
            # Usamos index=False para remover a numeração
            # Usamos header=False se você não quiser repetir o cabeçalho em cada tabela
            conteudo_csv_bruto = df.to_csv(index=False, header=False)
            
            f = io.StringIO(conteudo_csv_bruto)
            reader = csv.reader(f)
            dados_tabela = list(reader)
            
            print(f"DEBUG: Tabela {i+1} processada via Pandas.")
            
            # O restante da sua lógica de tratamento e fusão segue igual...
            for linha_bruta in dados_tabela:
                # Aplicamos sua limpeza numérica
                celulas = [tratar_valor_numerico(item) for item in linha_bruta]
                
                # Lógica de fusão de linhas órfãs (quando a primeira célula é vazia)
                if todas_as_linhas and celulas[0] == "" and any(celulas[1:]):
                    ultima_linha = todas_as_linhas[-1]
                    for idx in range(min(len(celulas), len(ultima_linha))):
                        if celulas[idx]:
                            espaco = " " if ultima_linha[idx] else ""
                            ultima_linha[idx] += espaco + celulas[idx]
                else:
                    if any(celulas):
                        todas_as_linhas.append(celulas)
        except Exception as e:
            print(f"AVISO: Falha ao processar a tabela {i+1}: {e}")

    if todas_as_linhas:
        filename = f"{nome_base}_unificado.csv"
        caminho_completo = os.path.join(os.getcwd(), filename)
        
        # Salvamos no formato final (Ponto e vírgula + UTF-8-SIG)
        with open(caminho_completo, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile, delimiter=';') 
            writer.writerows(todas_as_linhas)
        
        print(f"\nSUCESSO: Arquivo unificado gerado em: {caminho_completo}")
        return filename
    else:
        print("\nAVISO: Nenhuma linha foi extraída para o CSV.")
        return None

def exportar_tabelas_unificadas_excel(doc, nome_base="resultado"):
    if not doc or not hasattr(doc, 'tables'):
        print("ERRO: Documento não contém tabelas.")
        return None

    print(f"DEBUG EXCEL: O Textract encontrou {len(doc.tables)} tabela(s).")
    todas_as_linhas = []
    
    # 1. REPLICANDO EXATAMENTE A LÓGICA DO SEU CSV
    for i, table in enumerate(doc.tables):
        try:
            df = table.to_pandas()
            conteudo_csv_bruto = df.to_csv(index=False, header=False)
            f = io.StringIO(conteudo_csv_bruto)
            reader = csv.reader(f)
            dados_tabela = list(reader)
            
            for linha_bruta in dados_tabela:
                celulas = [tratar_valor_numerico(item) for item in linha_bruta]
                
                if todas_as_linhas and celulas[0] == "" and any(celulas[1:]):
                    ultima_linha = todas_as_linhas[-1]
                    for idx in range(min(len(celulas), len(ultima_linha))):
                        if celulas[idx]:
                            espaco = " " if ultima_linha[idx] else ""
                            ultima_linha[idx] += espaco + celulas[idx]
                else:
                    if any(celulas):
                        todas_as_linhas.append(celulas)
        except Exception as e:
            print(f"AVISO: Falha na tabela {i+1} para Excel: {e}")

    if todas_as_linhas:
        df_final = pd.DataFrame(todas_as_linhas)

        # 2. CONVERSÃO SELETIVA PARA EXCEL (Padrão 2026)
        def converter_apenas_precos(valor):
            if not valor: return ""
            # Sua Regex para identificar preços (ex: 139,62)
            if re.match(r'^-?\d+([\d\.]*,\d+)?$', str(valor)):
                return float(str(valor).replace('.', '').replace(',', '.'))
            return str(valor)

        # MUDANÇA AQUI: .applymap() virou .map() no Pandas 2.1+
        df_final = df_final.map(converter_apenas_precos)

        filename = f"{nome_base}_unificado.xlsx"
        caminho_completo = os.path.join(os.getcwd(), filename)
        
        # 3. SALVAMENTO FINAL
        df_final.to_excel(caminho_completo, index=False, header=False, engine='openpyxl')
        
        print(f"SUCESSO EXCEL: Gerado em {caminho_completo}")
        return caminho_completo
    else:
        return None