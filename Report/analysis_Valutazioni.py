import pandas as pd
import plotly.express as px
import os

def load_and_analyze_files(directory):
    """
    Legge tutti i file nella cartella che contengono "Valutazioni" nel nome,
    calcola la media delle metriche e crea un grafico interattivo.
    
    :param directory: Percorso della cartella contenente i file CSV
    """
    files = [f for f in os.listdir(directory) if "Valutazioni" in f and f.endswith(".csv")]
    
    all_data = []
    
    for file in files:

        print(file)
        
        file_path = os.path.join(directory, file)
        df = pd.read_csv(file_path, encoding='utf-8')
        metriche_media = df.select_dtypes(include=['number']).mean()
        df_media = pd.DataFrame({"Metrica": metriche_media.index, "Media": metriche_media.values})
        df_media["File"] = file
        all_data.append(df_media)
    
    if all_data:
        df_final = pd.concat(all_data)
        fig = px.bar(df_final, x="Metrica", y="Media", color="File", title="Media delle Metriche per File",
                     text="Media", barmode='group')
        fig.show()
    else:
        print("Nessun file trovato.")

load_and_analyze_files(os.path.dirname(os.path.abspath(__file__)))
