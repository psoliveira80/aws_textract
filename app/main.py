from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import shutil
from dotenv import load_dotenv
from services.aws_textract import processar_pdf_textractor, exportar_tabelas_unificadas_csv, exportar_tabelas_unificadas_excel
from utils import cortar_pdf

load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.post("/processar_textract")
async def processar_endpoint(
    arquivo: UploadFile = File(...),
    intervalo: str = Form(...)
):
    temp_original = f"temp_{arquivo.filename}"
    export_file = None
    
    try:
        # Salva o upload
        with open(temp_original, "wb") as buffer:
            shutil.copyfileobj(arquivo.file, buffer)
        
        # 1. Corta o PDF (Usando sua função)
        pdf_cortado = cortar_pdf(temp_original, intervalo)
        
        # 2. Sobe para o S3 e Processa
        bucket = os.getenv("S3_BUCKET_NAME")
        # Aqui você pode adicionar um upload_file manual para o S3 antes 
        # ou deixar o Textractor lidar se o arquivo for local (ele subirá p/ um bucket padrão)
        
        doc = processar_pdf_textractor(bucket, pdf_cortado, os.getenv("AWS_REGION"))
        
        # 3. Gera o EXPORT FILE
        nome_base = arquivo.filename.replace(".pdf", "")
        #export_file = exportar_tabelas_unificadas_csv(doc, nome_base)
        #media_type = 'text/csv'
        export_file = exportar_tabelas_unificadas_excel(doc, nome_base)
        media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

        if export_file is None:
            # Retorna um erro amigável que o seu JS agora consegue ler
            raise HTTPException(
                status_code=400, 
                detail="Nenhuma tabela foi detectada no documento para o intervalo selecionado."
            )
        
        return FileResponse(
            path=export_file, 
            filename=os.path.basename(export_file),
            media_type=media_type
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Limpeza de arquivos temporários
        if os.path.exists(temp_original): os.remove(temp_original)

@app.get("/")
async def read_index():
    return FileResponse('static/index.html')