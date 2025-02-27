import os
import sys
import time
import pandas as pd
from io import StringIO
import json
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from huggingface_hub import login

from transformers import AutoModelForCausalLM, AutoTokenizer
from auto_gptq import AutoGPTQForCausalLM

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Define import keys 
from Define import SourceCode

# Estensione dei file di codice da analizzare
CODE_EXTENSIONS = {".py", ".js", ".java", ".cpp", ".cs", ".ts", ".c"}

MAXFILE = 50

huggingface_token = keys.HUG_FACE_TOKEN

def remove_first_last_line(text):
    lines = text.strip().split("\n")  # Rimuove spazi e divide in righe
    return "\n".join(lines[1:-1]) if len(lines) > 2 else ""


def parse_chatgpt_response(response):
    
    res = remove_first_last_line(response)
    #res = response
    
    print(res)

    try:
        # Carica il JSON se è in formato stringa
        data = json.loads(res)

        # Estrai metriche e issue in modo sicuro
        metriche = data.get("Metriche", [])
        issue = data.get("Issue", [])
        
        metriche_list = []
        for m in metriche:
            met = []
            met.append(m.get("Filename", "Unknown"))
            met.append(m.get("Manutenibilità", "Unknown"))
            met.append(m.get("Leggibilità", "Unknown"))
            met.append(m.get("Performance", "Unknown"))
            met.append(m.get("Sicurezza", "Unknown"))
            met.append(m.get("Modularità", "Unknown"))
            metriche_list.append(met)
        
        issue_list = []
        for m in issue:
            met = []
            met.append(m.get("Filename", "Unknown"))
            met.append(m.get("Line", 0))
            met.append(m.get("Tipo", "N/A"))
            met.append(m.get("Severità", "N/A"))
            met.append(m.get("Descrizione", "N/A"))
            met.append(m.get("Suggestion", "N/A"))
            issue_list.append(met)
        
        return metriche_list, issue_list
    
    except json.JSONDecodeError:
        print("Errore nel parsing del JSON: Formato non valido.")
        return [], []
    except Exception as e:
        print(f"Errore inatteso: {e}")
        return [], []
        
        
def analyze_code(code, max_retries=5, wait_time=10, max_tokens=20000):
    """Analizza il codice con chatGpt e restituisce le valutazioni e le issues."""

    prompt = f"""
    Agisci come un revisore di codice esperto. Analizza il seguente codice e in output rispettando le seguenti regole
    
    Regole:
    1. Assicurati che la risposta sia un **JSON valido** senza alcun testo aggiuntivo.
    2. Calcola le seguenti metriche: Manutenibilità, Leggibilità, Performance, Sicurezza, Modularità
    3. Per ogni issue rilevata indica 
    4. Usa solo valori realistici:
        - Riga del codice in cui si trova l'issue
        - Tipo di issue (es. potenziale bug, vulnerabilità, cattiva pratica)
        - Severità (es. alta, media, bassa)
        - Descrizione dell'issue
        - Suggerimento per la correzione
    - I punteggi delle metriche devono essere compresi tra **1 e 5**.
    - La linea del codice deve essere un numero positivo.
    - La severità può essere **"Bassa", "Media", "Alta"**.
    
    Esempio di output corretto:

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

    Non aggiungere alcuna spiegazione o testo extra, restituisci solo il JSON.:
   
    ```python
    {code}
    ```
    """

    attempt = 0
    while attempt < max_retries:
        try:
            #response = code_quality_model(prompt, max_new_tokens=max_tokens, do_sample=True)
            inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
            response = model.generate(**inputs, max_new_tokens=2000000)
            
            response_text = response[0]['generated_text']

            valutazioni, issues = parse_chatgpt_response(response_text)
            
            if response:  # Check if response is valid
                return valutazioni, issues

            print(f"Attempt {attempt + 1}: No response received. Retrying...")
        
        except Exception as e:
            print(f"Error: {e}. Retrying in {wait_time} seconds...")

        attempt += 1
        time.sleep(wait_time)  # Wait before retrying


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
                strDebug = str(fileCount) + " di " + str(filesTot) + " :" + file_name 
                print(strDebug)
                
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

                        strDebug = "Issue: " + str(len(issues_list)) + " Evaluation: "  + str(len(valutazioni_list)) 
                        print(strDebug)
                
                except Exception as e:
                    print(f"analyze_code Error: {e}")

    return valutazioni_list, issues_list

folder_path = SourceCode.PANDA_SLIM

login(huggingface_token)

#model_name = "bigcode/starcoder"
#tokenizer = AutoTokenizer.from_pretrained(model_name, use_auth_token=True)
#model = AutoModelForCausalLM.from_pretrained(model_name, use_auth_token=True)
#code_quality_model = pipeline("text-generation", model=model, tokenizer=tokenizer)

model_name = "TheBloke/StarCoder-GPTQ"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoGPTQForCausalLM.from_quantized(model_name, device="cuda")

filesTot = conta_file(folder_path)
valutazioni_list, issues_list = process_folder(folder_path)

cartella_destinazione = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Report"))
os.makedirs(cartella_destinazione, exist_ok=True)

# Crea i DataFrame e salva le tabelle in file CSV
valutazioni_df = pd.DataFrame(valutazioni_list, columns=["File", "Manutenibilità", "Leggibilità", "Performance", "Sicurezza", "Modularità", "FullPath"])
file_path = os.path.join(cartella_destinazione, "Valutazioni_hf_startcoder.csv")
valutazioni_df.to_csv(file_path, index=False)

issues_df = pd.DataFrame(issues_list, columns=["File", "Riga", "Tipo", "Severità", "Descrizione", "Suggerimento", "FullPath"])
file_path = os.path.join(cartella_destinazione, "Issues_hf_startcoder.csv")
issues_df.to_csv(file_path, index=False)

print("done!")
