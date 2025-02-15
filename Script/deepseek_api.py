import os
import sys
import time
import pandas as pd
import openai
from io import StringIO
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Define import keys 
from Define import SourceCode

# Estensione dei file di codice da analizzare
CODE_EXTENSIONS = {".py", ".js", ".java", ".cpp", ".cs", ".ts", ".c"}

MAXFILE = 50

client = openai.OpenAI(api_key=keys.DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

def remove_first_last_line(text):
    lines = text.strip().split("\n")  # Rimuove spazi e divide in righe
    return "\n".join(lines[1:-1]) if len(lines) > 2 else ""

def parse_deepseek_response(response):
    res = remove_first_last_line(response)
    print(res)

    try:
        data = json.loads(res)
        metriche = data.get("Metriche", [])
        issue = data.get("Issue", [])
        
        metriche_list = []
        for m in metriche:
            metriche_list.append([
                m.get("Filename", "Unknown"),
                m.get("Manutenibilità", "Unknown"),
                m.get("Leggibilità", "Unknown"),
                m.get("Performance", "Unknown"),
                m.get("Sicurezza", "Unknown"),
                m.get("Modularità", "Unknown")
            ])
        
        issue_list = []
        for m in issue:
            issue_list.append([
                m.get("Filename", "Unknown"),
                m.get("Line", 0),
                m.get("Tipo", "N/A"),
                m.get("Severità", "N/A"),
                m.get("Descrizione", "N/A"),
                m.get("Suggestion", "N/A")
            ])
        
        return metriche_list, issue_list
    
    except json.JSONDecodeError:
        print("Errore nel parsing del JSON: Formato non valido.")
        return [], []
    except Exception as e:
        print(f"Errore inatteso: {e}")
        return [], []
        

def analyze_code(code, max_retries=5, wait_time=10):
    """Analizza il codice con DeepSeek e restituisce le valutazioni e le issues."""

    prompt = f"""
    Agisci come un revisore di codice esperto. Analizza il seguente codice e restituisci un output in **JSON valido** secondo le seguenti regole:

    1. Calcola le seguenti metriche: Manutenibilità, Leggibilità, Performance, Sicurezza, Modularità
    2. Per ogni issue rilevata, indica:
       - Riga del codice
       - Tipo di issue (es. potenziale bug, vulnerabilità, cattiva pratica)
       - Severità (Alta, Media, Bassa)
       - Descrizione e suggerimento per la correzione
    3. I punteggi delle metriche devono essere compresi tra **1 e 5**.

    Restituisci solo il JSON, senza testo aggiuntivo:
    
    ```python
    {code}
    ```
    """

    attempt = 0
    while attempt < max_retries:
        try:
            response = client.chat.completions.create(
                model = "deepseek-chat",
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.choices[0].message.content  # Recupera il testo della risposta
            valutazioni, issues = parse_deepseek_response(response_text)
            
            if response:
                return valutazioni, issues

            print(f"Tentativo {attempt + 1}: Nessuna risposta ricevuta. Riprovo...")
        
        except Exception as e:
            print(f"Errore: {e}. Riprovo tra {wait_time} secondi...")

        attempt += 1
        time.sleep(wait_time)

def conta_file(cartella):
    totale_file = 0
    for _, _, files in os.walk(cartella):
        totale_file += len(files)
    return totale_file

def process_folder(folder_path):
    """Elabora una cartella contenente codice sorgente."""

    valutazioni_list = []
    issues_list = []
    fileCount = 0

    for root, _, files in os.walk(folder_path):
        for file_name in files:
            if any(file_name.endswith(ext) for ext in CODE_EXTENSIONS):
                file_path = os.path.join(root, file_name)
                fileCount += 1
                print(f"{fileCount} di {filesTot} : {file_name}")
                
                try:
                    if fileCount > MAXFILE:
                        break 

                    with open(file_path, "r") as f:
                        code = f.read()
                        valutazioni, issues = analyze_code(code)
                        
                        for val in valutazioni:
                            val.append([os.path.abspath(file_name)])
                            valutazioni_list.append(val)
                        
                        for issue in issues:
                            issue.append([os.path.abspath(file_name)])
                            issues_list.append(issue)

                        print(f"Issue: {len(issues_list)} - Evaluation: {len(valutazioni_list)}")
                
                except Exception as e:
                    print(f"Errore in analyze_code: {e}")

    return valutazioni_list, issues_list

folder_path = SourceCode.PANDA_SLIM

models = client.models.list()
print("Modelli disponibili nel tuo account:")
print(models)

filesTot = conta_file(folder_path)
valutazioni_list, issues_list = process_folder(folder_path)

cartella_destinazione = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Report"))
os.makedirs(cartella_destinazione, exist_ok=True)

# Crea i DataFrame e salva i report in CSV
valutazioni_df = pd.DataFrame(valutazioni_list, columns=["File", "Manutenibilità", "Leggibilità", "Performance", "Sicurezza", "Modularità", "FullPath"])
valutazioni_df.to_csv(os.path.join(cartella_destinazione, "Valutazioni_deepseek.csv"), index=False)

issues_df = pd.DataFrame(issues_list, columns=["File", "Riga", "Tipo", "Severità", "Descrizione", "Suggerimento", "FullPath"])
issues_df.to_csv(os.path.join(cartella_destinazione, "Issues_deepseek.csv"), index=False)

print("done!")
