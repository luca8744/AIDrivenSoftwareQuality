import os
import sys
import time
import pandas as pd
import anthropic
from io import StringIO
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Define import keys 
from Define import SourceCode

# Estensione dei file di codice da analizzare
CODE_EXTENSIONS = {".py", ".js", ".java", ".cpp", ".cs", ".ts", ".c"}

MAXFILE = 50

# Configura Claude (Anthropic API)
client = anthropic.Anthropic(api_key=keys.CLAUDE_API_KEY)

def remove_first_last_line(text):
    lines = text.strip().split("\n")  # Rimuove spazi e divide in righe
    return "\n".join(lines[1:-1]) if len(lines) > 2 else ""

def parse_claude_response(response):
    #res = remove_first_last_line(response)
    res = response
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


def analyze_code_with_claude(code, max_retries=5, wait_time=10):
    prompt = f"""
    Sei un revisore esperto di codice. Analizza il seguente codice e genera un output JSON valido con queste regole:
    
    - Includi metriche: Manutenibilità, Leggibilità, Performance, Sicurezza, Modularità (valori 1-5).
    - Identifica eventuali issue con dettagli: Riga, Tipo (bug, vulnerabilità, cattiva pratica), Severità (Alta, Media, Bassa), Descrizione, Suggerimento.
    - Rispondi solo con il JSON senza testo aggiuntivo.
    
    Esempio di output:
    {{
        "Metriche": [
            {{
                "Filename": "main.py",
                "Manutenibilità": 4,
                "Leggibilità": 3,
                "Performance": 5,
                "Sicurezza": 3,
                "Modularità": 4
            }}
        ],
        "Issue": [
            {{
                "Filename": "main.py",
                "Line": 32,
                "Tipo": "Cattiva Pratica",
                "Severità": "Alta",
                "Descrizione": "Uso di una variabile non inizializzata",
                "Suggestion": "Dichiarare e inizializzare la variabile prima dell'uso."
            }}
        ]
    }}
    
    Codice:
    ```python
    {code}
    ```
    """

    attempt = 0
    while attempt < max_retries:
        try:
            response = client.messages.create(
                #model="claude-3-opus-20240229",
                model = "claude-3-haiku-20240307",
                #model = "claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            response_text = response.content[0].text
            valutazioni, issues = parse_claude_response(response_text)
            
            if response_text:
                return valutazioni, issues
            print(f"Tentativo {attempt + 1}: Nessuna risposta. Ritento...")
        except Exception as e:
            print(f"Errore: {e}. Riprovo in {wait_time} secondi...")

        attempt += 1
        time.sleep(wait_time)

def process_folder(folder_path):
    valutazioni_list = []
    issues_list = []
    fileCount = 0
    for root, _, files in os.walk(folder_path):
        for file_name in files:
            if any(file_name.endswith(ext) for ext in CODE_EXTENSIONS):
                file_path = os.path.join(root, file_name)
                fileCount += 1
                strDebug = str(fileCount) + " di " + str(filesTot) + " :" + file_name 
                print(strDebug)

                if fileCount > MAXFILE:
                    break 
                try:
                    with open(file_path, "r") as f:
                        code = f.read()
                        valutazioni, issues = analyze_code_with_claude(code)
                        for val in valutazioni:
                            val.append([os.path.abspath(file_name)])
                            valutazioni_list.append(val)
                        for issue in issues:
                            issue.append([os.path.abspath(file_name)])
                            issues_list.append(issue)
                    
                        strDebug = "Issue: " + str(len(issues_list)) + " Evaluation: "  + str(len(valutazioni_list)) 
                        print(strDebug)
                        
                        time.sleep(10)
                    
                except Exception as e:
                    print(f"Errore: {e}")
    return valutazioni_list, issues_list

models = client.models.list()
print("Modelli disponibili su Claude:")
print(models)

folder_path = SourceCode.PANDA_FULL
filesTot = sum(len(files) for _, _, files in os.walk(folder_path))
valutazioni_list, issues_list = process_folder(folder_path)

cartella_destinazione = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Report"))
os.makedirs(cartella_destinazione, exist_ok=True)

valutazioni_df = pd.DataFrame(valutazioni_list, columns=["File", "Manutenibilità", "Leggibilità", "Performance", "Sicurezza", "Modularità", "FullPath"])
valutazioni_df.to_csv(os.path.join(cartella_destinazione, "Valutazioni_claude-haiku_v3.csv"), index=False)

issues_df = pd.DataFrame(issues_list, columns=["File", "Riga", "Tipo", "Severità", "Descrizione", "Suggerimento", "FullPath"])
issues_df.to_csv(os.path.join(cartella_destinazione, "Issues_claude-haiku_v3.csv"), index=False)

print("Analisi completata con Claude!")