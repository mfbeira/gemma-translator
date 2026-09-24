# 🌐 Gemma Translator

Um aplicativo web local construído em **Python (Flask)** projetado para traduzir documentos inteiros utilizando modelos de Inteligência Artificial rodando localmente via **Ollama**.

O objetivo principal é extrair textos de documentos de forma estruturada (tabelas, títulos) e traduzir com qualidade utilizando o modelo `translategemma:4b` ou similares, preservando a formatação original em Markdown e exportando o resultado final em PDF.

---

## ✨ Como Funciona

O fluxo do aplicativo acontece em 4 etapas:
1. **Extração Avançada:** O arquivo enviado pelo usuário (PDF, Word, etc.) é processado pela biblioteca `Docling`, convertendo tudo perfeitamente para formato Markdown bruto (preservando tabelas, imagens e estruturas de texto).
2. **Streaming via Ollama:** O Markdown extraído é enviado em formato de prompt para o Ollama local, solicitando a tradução para o idioma escolhido. O retorno é exibido ao vivo na tela (Stream).
3. **Conversão de Formato:** O Markdown final traduzido é salvo na pasta `outputs/`.
4. **Geração do PDF:** O Markdown é renderizado em HTML puro e convertido em um novo PDF lindamente formatado usando `xhtml2pdf`.

---

## 🚀 Como Rodar Localmente

1. Certifique-se de ter o **Python 3.10+** instalado, além do [Ollama](https://ollama.com/) rodando no seu computador.
2. É recomendável já ter baixado o modelo através do Ollama (ex: `ollama run translategemma:4b`).
3. Crie seu ambiente virtual (opcional, mas recomendado) e instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
4. Inicie o servidor Flask:
   ```bash
   python app.py
   # Ou use o script bat: start_translator.bat
   ```
5. Acesse no navegador: `http://localhost:5000`

---

## 📁 Estrutura do Projeto

- `app.py`: O coração da aplicação (API em Flask, rotas de upload e WebSockets de stream).
- `templates/`: Arquivos HTML (interface web).
- `uploads/`: Pasta temporária onde o documento original é guardado antes de ser processado (limpa automaticamente).
- `outputs/`: Pasta onde os relatórios Markdown e PDFs traduzidos são gerados e ficam disponíveis para download.
