#In questo script viene interrogato il modello per verificare che le relazioni trovate precedentemente siano corrette
#Potrebbe infatti capitare che il modello inizialmente abbia trovato la seguente relazione: leader_of,Giuseppe Conte,Partito Democratico che è falsa e va quindi eliminata
import google.generativeai as genai
import json
from collections import defaultdict
import os
import pandas as pd
from google.cloud.aiplatform_v1beta1.types.content import SafetySetting
from vertexai.preview.generative_models import (
    HarmCategory, 
    HarmBlockThreshold )

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

#Leggiamo il file delle relazioni filtrate dallo script post_processing_relations.py
relations_csv_file = 'final_unique_relations.csv'
df_relations = pd.read_csv(relations_csv_file)

#Definizione percorso in cui salveremo il file di output
output_csv_path = 'neo4j_relations.csv'

#Percorso del file JSON dove verranno salvate le relazioni valutate dal modello con i rispettivi esiti
json_file_path = "check_relations.json"

#Funzione per inizializzare il file JSON con una struttura vuota se non esiste
def initialize_json_file(file_path):
    if not os.path.exists(file_path):
        with open(file_path, "w") as file:
            json.dump({"relazioni": []}, file, indent=4)

# Inizializza il file JSON se non esiste
initialize_json_file(json_file_path)


sexually_explicit_content_setting = SafetySetting(
    category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
    threshold=HarmBlockThreshold.BLOCK_NONE
)

hate_speech_content_setting = SafetySetting(
    category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
    threshold=HarmBlockThreshold.BLOCK_NONE
)

dangerous_content_setting = SafetySetting(
    category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
    threshold=HarmBlockThreshold.BLOCK_NONE
)

harassment_content_setting = SafetySetting(
    category=HarmCategory.HARM_CATEGORY_HARASSMENT,
    threshold=HarmBlockThreshold.BLOCK_NONE
)

#Vengono passate 10 relazioni alla volta in ingresso al modello per ricevere la verifica di ognuna di esse
# Create the model
# See https://ai.google.dev/api/python/google/generativeai/GenerativeModel
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "application/json"
    }

model = genai.GenerativeModel(
model_name="gemini-1.5-flash",
generation_config=generation_config,
system_instruction = 
                    """Sei un agente che deve verificare se le relazioni estratte con la NER a partire da notizie relative alla politica e elezioni europee 2024 sono vere oppure no.
                    Le relazioni fornite sono nella forma RelationType, Source, Target
                    Per ogni relazione in ingresso devi fornire una risposta "SI" oppure "NO". Devi anche fornire una breve motivazione della scelta.

                    Le entità sono di queste tipologie: 'Person', 'Organization', 'Location', 'Politician', 'Party', 'Event', 'Agreement'
                    Person: Un individuo umano specifico, generalmente identificato per nome. Può includere nomi di persone famose, autori, artisti, scienziati, sportivi, ecc.
                    Esempi: "Albert Einstein", "Leonardo da Vinci", "Marie Curie"

                    Organization: Un gruppo strutturato di persone che lavorano insieme per un obiettivo comune. Può includere aziende, enti governativi, istituzioni educative, ONG, gruppi sportivi, ecc.
                    Esempi: "Google", "Nazioni Unite", "Università di Oxford"

                    Location: Un luogo geografico specifico, che può essere una città, uno stato, un continente, un punto di interesse, ecc. Può includere anche indirizzi specifici, aree naturali e strutture.
                    Esempi: "Roma", "Monte Everest", "Stati Uniti", "Piazza San Marco"

                    Politician: Un individuo coinvolto in attività politiche, spesso eletto o nominato a una carica governativa. Può includere presidenti, primi ministri, senatori, sindaci e altri funzionari pubblici.
                    Esempi: "Angela Merkel", "Barack Obama", "Giuseppe Conte"
                    
                    Party: Un'organizzazione politica che rappresenta un gruppo di persone con ideologie e obiettivi comuni, solitamente con l'intento di ottenere e mantenere il potere politico attraverso elezioni.
                    Esempi: "Partito Democratico", "Movimento 5 Stelle", "Partito Repubblicano"

                    Event: Un'occasione particolare, spesso significativa, che può essere pianificata o spontanea. Include conferenze, guerre, catastrofi naturali, festival, eventi sportivi e celebrazioni.
                    Esempi: "Giochi Olimpici", "Guerra Civile Americana", "Conferenza sul Clima di Parigi", "Festival di Cannes"

                    Agreement: Un'intesa formalmente riconosciuta tra due o più parti, che stabilisce diritti e doveri reciproci.
                    Esempi: "Accordo di Parigi", "Trattato di Maastricht", "Contratto di lavoro collettivo"

                    Le relazioni sono di questi tipi:
                    leader_of: rapporto tra i leader politici e le entità o i gruppi che guidano. Fondamentale per comprendere la leadership e le affiliazioni politiche.

                    is_from: Indica l'origine nazionale degli individui coinvolti in politica, importante per geolocalizzare i personaggi politici.

                    part_of: mostra l'appartenenza di entità (come paesi, organizzazioni, dipartimenti) a gruppi più ampi come l'Unione Europea o il Parlamento Europeo.

                    located_in: specifica la posizione geografica di entità politiche o geografiche, utile per mappare la posizione di istituzioni ed eventi.

                    member_of: indica l'appartenenza di individui (come politici o persone) a gruppi o organizzazioni politiche, fornendo approfondimenti sulle alleanze politiche.

                    supports: rappresenta il sostegno politico dato da una figura o organizzazione a un'altra, rivelando alleanze e coalizioni.

                    president_of: identifica i soggetti che ricoprono la carica di presidente di enti politici o istituzionali.

                    opposition: Indica opposizione politica tra figure o gruppi, utile per comprendere le dinamiche dei conflitti politici.

                    colleague: Indica i rapporti professionali tra individui in politica, evidenziando collaborazioni e collegamenti.

                    
                    Output: L'output deve essere un file in formato JSON dove per ogni relazione sono definiti i campi Answer, [Relation, Source, Target], Motivazione.
                    
                   Esempio:
                    member_of, Giorgia Meloni, Partito Democtarico
                    member_of, Berlusconi, Forza Italia

                    JSON:
                    {
                        "relazioni": [
                            {
                                "Answer": "NO",
                                "Relation": "member_of",
                                "Source": "Giorgia Meloni",
                                "Target": "Partito Democratico",
                                "Motivazione": "Giorgia Meloni è membro del partito Fratelli d’Italia e quindi non è membro del Partito Democratico"
                            },
                            {
                                "Answer": "SI",
                                "Relation": "member_of",
                                "Source": "Berlusconi",
                                "Target": "Forza Italia",
                                "Motivazione": "Silvio Berlusconi è stato leader di Forza Italia e quindi anche membro"
                            }
                        ]
                    }

                    JSON:"""
                    
              )


chat_session = model.start_chat()

#Indice utile a tener conto di quante relazioni già sono state elaborate
with open ("offset_relations.txt", "r") as file:
    offset = int(file.readline())
    print(offset)

for i in range(offset,len(df_relations),25):
    print(f"Relations da {i} a {i+25}")
    response = chat_session.send_message(str(df_relations.iloc[i:i+25]))
    response_data = json.loads(response.text)
    relazioni = response_data.get('relazioni', [])

    #Aggiungi le nuove relazioni al file JSON
    with open(json_file_path, "r+") as file:
        data = json.load(file)
        data["relazioni"].extend(relazioni)
        file.seek(0)
        json.dump(data, file, indent=4)
        file.truncate()


    offset = offset+25
    with open ("offset_relations.txt", "w") as file:
        file.write(str(offset))

#Carica il JSON in un dataframe Pandas
with open(json_file_path, "r") as file:
    data = json.load(file)

#Generazione del dataframe contentente tutte le relazioni con esito
df = pd.DataFrame(data["relazioni"])

#Eliminazione colonne inutili
df = df.drop(columns="Motivazione")

#Filtra le relazioni dove la risposta è "NO", sono quelle relazioni che vogliamo eliminare dal file originale
df_no_answers = df[df['Answer'] == 'NO']

# Effettua il merge per rimuovere le relazioni presenti in df_no_answers da df_relations
merged_df = pd.merge(df_relations, df_no_answers, on=['Relation', 'Source', 'Target'], how='left', indicator=True)

#Seleziona solo le righe che non sono presenti in df_no_answers
df_updated = merged_df[merged_df['_merge'] == 'left_only'].drop(columns=['_merge', 'Answer'])

#Scrittura del dataframe contenente le relazioni in un file .csv
df_updated.to_csv(output_csv_path, index=False)
