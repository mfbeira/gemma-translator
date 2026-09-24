import os
import uuid
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory, Response
from docling.document_converter import DocumentConverter
import ollama
import markdown
from xhtml2pdf import pisa

app = Flask(__name__)

# Configurações de pastas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'outputs')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/extract', methods=['POST'])
def extract_file():
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
        
    filename = file.filename
    temp_filename = f"{uuid.uuid4()}_{filename}"
    temp_path = os.path.join(UPLOAD_FOLDER, temp_filename)
    file.save(temp_path)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir_name = f"output_extract_{timestamp}"
    output_dir_path = os.path.join(OUTPUT_FOLDER, output_dir_name)
    os.makedirs(output_dir_path, exist_ok=True)
    
    try:
        converter = DocumentConverter()
        doc_result = converter.convert(temp_path)
        md_content = doc_result.document.export_to_markdown()
        
        original_basename = os.path.splitext(filename)[0]
        md_filename = f"{original_basename}_extraido.md"
        md_filepath = os.path.join(output_dir_path, md_filename)
        
        with open(md_filepath, "w", encoding="utf-8") as f:
            f.write(md_content)
            
        return jsonify({
            'success': True,
            'output_folder': output_dir_name,
            'md_file': md_filename,
            'preview_text': md_content
        })
    except Exception as e:
        print(f"Erro na extração: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass


@app.route('/api/translate_stream', methods=['POST'])
def translate_stream():
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['file']
    target_lang = request.form.get('language', 'Português')
    target_model = request.form.get('model', 'translategemma:4b')
    
    if file.filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
        
    filename = file.filename
    temp_filename = f"{uuid.uuid4()}_{filename}"
    temp_path = os.path.join(UPLOAD_FOLDER, temp_filename)
    file.save(temp_path)
    
    def generate():
        try:
            yield json.dumps({"status": "info", "message": "Iniciando extração do documento com Docling..."}) + "\n"
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_dir_name = f"output_{timestamp}"
            output_dir_path = os.path.join(OUTPUT_FOLDER, output_dir_name)
            os.makedirs(output_dir_path, exist_ok=True)
            
            # 1. Extração
            converter = DocumentConverter()
            doc_result = converter.convert(temp_path)
            md_content = doc_result.document.export_to_markdown()
            
            yield json.dumps({"status": "info", "message": f"Extração concluída. Carregando modelo {target_model}..."}) + "\n"
            
            # 2. Tradução via Ollama (Streaming)
            prompt = f"Translate the following text to {target_lang}. Preserve all markdown formatting, tables, and structure. Only output the translated text.\n\n{md_content}"
            
            response_stream = ollama.generate(model=target_model, prompt=prompt, stream=True)
            
            translated_md = ""
            for chunk in response_stream:
                text_chunk = chunk.get('response', '')
                translated_md += text_chunk
                yield json.dumps({"status": "chunk", "text": text_chunk}) + "\n"
            
            yield json.dumps({"status": "info", "message": "Tradução concluída. Gerando arquivos finais..."}) + "\n"
            
            # 3. Salvar Markdown
            original_basename = os.path.splitext(filename)[0]
            md_filename = f"{original_basename}_{target_lang}.md"
            md_filepath = os.path.join(output_dir_path, md_filename)
            with open(md_filepath, "w", encoding="utf-8") as f:
                f.write(translated_md)
                
            # 4. Salvar PDF
            pdf_filename = f"{original_basename}_{target_lang}.pdf"
            pdf_filepath = os.path.join(output_dir_path, pdf_filename)
            
            html_body = markdown.markdown(translated_md, extensions=['tables', 'fenced_code'])
            html_content = f"""
            <html>
            <head>
                <meta charset='utf-8'>
                <style>
                    @page {{ margin: 2cm; }}
                    body {{ font-family: Helvetica, Arial, sans-serif; line-height: 1.6; font-size: 12pt; }}
                    table {{ border-collapse: collapse; width: 100%; margin-bottom: 15px; }}
                    th, td {{ border: 1px solid #dddddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; font-weight: bold; }}
                    h1, h2, h3 {{ color: #333333; }}
                    pre {{ background-color: #f8f8f8; padding: 10px; border: 1px solid #ddd; }}
                    code {{ font-family: "Courier New", Courier, monospace; }}
                </style>
            </head>
            <body>
                {html_body}
            </body>
            </html>
            """
            
            try:
                with open(pdf_filepath, "wb") as pdf_file:
                    pisa_status = pisa.CreatePDF(html_content, dest=pdf_file)
                    pdf_success = not pisa_status.err
            except Exception as e:
                pdf_success = False
                
            yield json.dumps({
                "status": "done", 
                "output_folder": output_dir_name, 
                "md_file": md_filename, 
                "pdf_file": pdf_filename if pdf_success else None,
                "pdf_error": not pdf_success
            }) + "\n"
            
        except Exception as e:
            yield json.dumps({"status": "error", "message": str(e)}) + "\n"
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
                    
    return Response(generate(), mimetype='application/x-ndjson')

@app.route('/download/<folder>/<filename>')
def download_file(folder, filename):
    folder_path = os.path.join(OUTPUT_FOLDER, folder)
    return send_from_directory(folder_path, filename, as_attachment=True)

if __name__ == '__main__':
    print("Iniciando Translator & Extractor App...")
    print("Acesse http://127.0.0.1:5000 no seu navegador.")
    app.run(debug=True, port=5000)
