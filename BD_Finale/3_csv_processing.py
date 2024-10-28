#Questo script serve a:
#1) Filtrare tra tutte le entità e le relazioni solamente quelle consentite ed elimina i duplicati.
#2) Fare in modo che gli acronimi vengano estesi con il loro nome completo, ad esempio "m5s" diventa "movimento 5 stelle", "pd" diventa "partito democratico"
#3) Fare in modo che entità con nomi simili tra loro diventino la stessa entità, ad esempio "Alleanza Verdi e Sinistra" diventa "Alleanza Verdi Sinistra"
#Allo stesso modo vengono modificate le relazioni per fare coincidere i nomi presenti in queste ultime con le entità modificate

import json
import pandas as pd
from fuzzywuzzy import process, fuzz   
import json
import csv
from collections import defaultdict
import os
import google.generativeai as genai
from vertexai.preview.generative_models import (
    HarmCategory, 
    HarmBlockThreshold )
from google.cloud.aiplatform_v1beta1.types.content import SafetySetting
#from gemini import SafetySettings

genai.configure(api_key="AIzaSyDJRoK47eh89MVGCZ0SCyV0-mxWR-NNraA")


#Funzione utile a verificare se il nome di un'entità di tipo Person è contenuto all'interno di un'altra entità, in caso positivo viene mappato al nome completo.
#Esempio: "Meloni" diventa "Giorgia Meloni", "Le Pen" diventa "Marine Le Pen", "Ursula von Der leyen" diventa "Ursula Von Der Leyen"
def create_name_mapping(names):
    """
    Crea una mappa di nomi dove ogni nome parziale è sostituito dal nome completo corrispondente.
    Parameters: names (list): Lista di nomi da mappare.
    Returns: dict: Dizionario con i nomi originali come chiavi e i nomi sostituiti come valori.
    """
    name_mapping = {}
    for name in names:
        for other_name in names:
            #Se il nome che stiamo valutando è diverso da quello confrontato ed è contenuto in quest'ultimo oppure è diverso da quello confrontato solo per le lettere maiuscole/minuscole
            #Mappiamo questo nome al nome che lo include
            if (name != other_name and name.lower() in other_name.lower()) or (name != other_name and name.lower() == other_name.lower()):
                name_mapping[name] = other_name
                break
        if name not in name_mapping:
            name_mapping[name] = name
    return name_mapping

#Queste due liste sono utili a verificare che le entità e le relazioni trovate siano effettivamente quelle che vogliamo
entities_list = ["Person","Organization","Location","Politician","Party","Event","Agreement"]
relationship_list = ["leader_of","is_from","part_of","located_in","member_of","supports","president_of","opposition","colleague"]

# Carica i file CSV
df_entities = pd.read_csv("entities.csv")
df_relations = pd.read_csv("relations.csv")

#Vogliamo eliminare tutti i duplicati indipendentemente dalle lettere maiuscole/minuscole, quindi creiamo una nuova colonna che contiene tutti i nomi in minuscolo
#Effettuiamo il drop dei duplicati per nome (minuscolo) e tipo uguali
#Verifichiamo che i tipi siano quelli indicati nella lista entities_list e poi eliminiamo la colonna aggiunta
df_entities['Entity_lower'] = df_entities['Name'].str.lower()
df_entities = df_entities.drop_duplicates(subset=['Entity_lower', 'Type'])
df_entities = df_entities[df_entities['Type'].isin(entities_list)]
df_entities = df_entities.drop(columns=['Entity_lower'])

df_relations = df_relations.drop_duplicates()
df_relations = df_relations[df_relations['Relation'].isin(relationship_list)]


############################################### SCRIPT PER TROVARE I RISPETTIVI NOMI COMPLETI DEGLI ACRONIMI DI ENTITIES.CSV #####################################################################################


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
  system_instruction = """
                    Dato un elenco di entità, estratte a partire da news relative alle elezioni europee 2024, espandi gli acronimi alla loro forma estesa in lingua ital. Per ogni entità che è un acronimo, sostituisci l'acronimo con la sua forma completa.
                    Devi generare un file .json
                    
                    ESEMPIO INPUT:
                    Name,Type
                    PD, Party
                    Paolo Gentiloni,Person
                    Commissione Ue,Organization
                    Italia,Location
                    Unione Europea,Organization
                    Patto di stabilità,Agreement
                    USA, Location
                    Parlamento europeo,Organization
                    Francia,Location
                    Assemblea nazionale,Organization
                    M5S, Party
                    Pvv, Party

                    ESEMPIO OUTPUT:
                    {
                    "name_changes": [
                        {"Old_Name": "PD", "New_Name": "Partito Democratico"},
                        {"Old_Name": "Paolo Gentiloni", "New_Name": "Paolo Gentiloni"},
                        {"Old_Name": "Commissione Ue", "New_Name": "Commissione dell'Unione Europea"},
                        {"Old_Name": "Italia", "New_Name": "Italia"},
                        {"Old_Name": "Unione Europea", "New_Name": "Unione Europea"},
                        {"Old_Name": "Patto di stabilità", "New_Name": "Patto di stabilità"},
                        {"Old_Name": "USA", "New_Name": "Stati Uniti d'America"},
                        {"Old_Name": "Parlamento europeo", "New_Name": "Parlamento europeo"},
                        {"Old_Name": "Francia", "New_Name": "Francia"},
                        {"Old_Name": "Assemblea nazionale", "New_Name": "Assemblea nazionale"},
                        {"Old_Name": "M5S", "New_Name": "Movimento 5 Stelle"},
                        {"Old_Name": "Pvv", "New_Name": "Partij voor de Vrijheid"}
                        ]
                    }

                    JSON:
                    """
              )


chat_session = model.start_chat()


#Indice utile a tener conto di quante relazioni già sono state elaborate
with open ("offset_processing.txt", "r") as file:
    offset = int(file.readline())
    print(offset)


#Viene interrogato il modello llm gemini al quale viene chiesto tramite prompt di trovare i rispettivi nomi completi per ogni entità
#A causa dei limiti del modello passiamo 30 entità alla volta, perciò abbiamo bisogno di iterare le richieste
for i in range(offset,len(df_entities),50):
    print(f"Entities da {i} a {i+50}")
    print(df_entities[i:i+50])
    response = chat_session.send_message(str(df_entities.iloc[i:i+50]))


    #Prendiamo il contenuto della risposta fornitaci dal modello, ne estraiamo le righe per inserirle in un dataframe
    response_data = json.loads(response.text)
    name_changes = response_data.get('name_changes', [])

    # Creazione del DataFrame dei risultati
    results = []
    for change in name_changes:
        old_name = change.get('Old_Name', '')
        new_name = change.get('New_Name', '')
        results.append({'Old_Name': old_name, 'New_Name': new_name})

    df_results = pd.DataFrame(results)
    df_results.to_csv("check_entities.csv", mode='a', header=False, index=False, lineterminator='\n')

    #Aggiornamento del file contenente l'offset delle relazioni già processate
    offset = offset + 50
    with open ("offset_processing.txt", "w") as file:
        file.write(str(offset))


    print(f'len df_entities: {len(df_entities)}')

###########################################################################################################################################################################################################################################

df_acronimi = pd.read_csv("check_entities.csv")

#Trovate le corrispondenze agli acronimi, le andiamo a sostituire all'interno dei dataframe contenenti le entità e le relazioni
#Creare il dizionario di mapping
mapping_dict = dict(zip(df_acronimi['Old_Name'].apply(lambda x: str(x).lower()), df_acronimi['New_Name']))
#Viene usata la funzione .lower() per far sì che la condizione di sostituzione non sia case sensitive
df_entities['Name'] = (df_entities['Name'].apply(lambda x: str(x).lower())).replace(mapping_dict)
df_relations['Source'] = (df_relations['Source'].apply(lambda x: str(x).lower())).replace(mapping_dict)
df_relations['Target'] = (df_relations['Target'].apply(lambda x: str(x).lower())).replace(mapping_dict)


#Soglia per la similarità
similarity_threshold = 85

#Lista di nomi unici necessaria per la costruzione del dizionario name_map
unique_names = df_entities['Name'].unique()

#Dizionario utile a mappare i nomi simili agli stessi valori secondo la treshold definita. Ad esempio "Alleanza Verdi e Sinistra" diventa "Alleanza Verdi Sinistra"
name_map = {}

#Funzione per trovare il nome canonico, ovvero il nome più simile al nome considerato (name) tra quelli presenti in names_list (name list sono le chiavi del dizionario name_map)
#Il valore ritornato match[0] è il nome con la similarità maggiore. Nel caso in cui in name_list non ci sia nessun nome simile a quello considerato, viene ritornato il nome stesso.
def find_canonical_name(name, names_list, threshold=85):
    match = process.extractOne(name, names_list, scorer=fuzz.token_sort_ratio)
    if match and match[1] >= threshold:
        return match[0]
    return name

#Costruzione della mappa dei nomi
#Dato il nome ritornato dalla funzione find_canonical_names, verifichiamo se quest'ultimo è già parte del dizionario 
#in caso positivo assegniamo alla chiave 'nome corrente' il value associato alla chiave ritornataci da find_canonical_names
#in caso negativo assegniamo alla chiave 'nome corrente' il value 'nome corrente'
#Esempio: Se inizialmente viene eseguito questo mapping: (Assocazione Verdi e Sinistra : Associazione Verdi Sinistra)
#         E abbiamo un nome come "Associazione, Verdi e sinistra" a cui viene associata come chiave più simile "Assocazione Verdi e Sinistra"
#         Per essere consistenti, vogliamo che il valore da associare a "Associazione, Verdi e sinistra" non sia la chiave ritornata, ma il valore associato a quest'ultima, 
#         e quindi avere la seguente corrispondenza: ("Associazione, Verdi e sinistra":"Associazione Verdi Sinistra")
#Questo è il motivo per cui viene assegnato a name_map[name], name_map[canonical_name]
for name in unique_names:
    canonical_name = find_canonical_name(name, name_map.keys(), similarity_threshold)
    name_map[name] = name_map[canonical_name] if canonical_name in name_map else name

#Dato che è possibile che le entità Person si presentino con solo nome, solo cognome o entrambe, vogliamo fare diventare la stessa entità
#Per questo motivo si usa la funzione create_name_mapping 
df_person = df_entities[df_entities['Type'] == 'Person']
df_person_names = df_person['Name'].unique()

name_map_person = create_name_mapping(df_person_names)

#Questo ciclo è utile a aggiornare il dizionario name_map precedentemente creato, con i mapping dei nomi trovato dalla funzione create_name_mapping
for k,value in name_map_person.items():
    if k in name_map.keys():
        name_map[k] = value

#Rendo unici i nomi delle entità Source e Target presenti nelle relazioni 
unique_sources = df_relations['Source'].unique()
unique_target = df_relations['Target'].unique()

#Questi due cicli for servono per trovare i nomi simili per Source e Target delle relazioni, allo stesso modo di quanto fatto per le entità.
#Infatti potrebbe capitare che nella relazione uno dei nomi Source o Target sono simili ma non uguali ai nomi delle entità, e quindi alle chiavi presenti in name_map
#In questo modo siamo in grado di mantenere la corrispondenza tra nomi di Source e Target con i nomi delle entità
#Esempio: Se abbiamo Source = Alleanza Verdi e Sinistra (AVS) e questo nome non è presente tra quelli delle entità, perderemmo questa relazione.
#         Eseguendo il mapping però riusciamo a trasformare Source in "Alleanza Verdi Sinistra" che è una delle entità e quindi riusciamo a mantenere questa relazione.
for name in unique_sources:
    name = str(name)
    canonical_name = find_canonical_name(name, name_map.keys(), similarity_threshold)
    name_map[name] = name_map[canonical_name] if canonical_name in name_map else name

for name in unique_target:
    name = str(name)
    canonical_name = find_canonical_name(name, name_map.keys(), similarity_threshold)
    name_map[name] = name_map[canonical_name] if canonical_name in name_map else name

#Qui viene creato un dizionario uguale a name_map, con la differenza che le chiavi sono tutte in minuscolo, per fare in modo che la condizione di sostituzione non sia case sensitive
lower_name_map = {k.lower():v for k,v in name_map.items()}

#Applicazione della mappa ai nomi delle entità
df_entities['Name'] = df_entities['Name'].apply(lambda x: lower_name_map[str(x).lower()])

#Applica della mappa a Source e Target delle relazioni
df_relations['Source'] = df_relations['Source'].apply(lambda x: lower_name_map.get(str(x).lower(), x))
df_relations['Target'] = df_relations['Target'].apply(lambda x: lower_name_map.get(str(x).lower(), x))

#Rendiamo uniche le righe dei dataframe di entità e relazioni perchè dopo la sostituzione potrebbero essersi generati dei duplicati
df_unique_entities = df_entities.drop_duplicates()
df_unique_relations = df_relations.drop_duplicates()

with open("dizionario.txt", "w") as file:
    file.write(json.dumps(name_map))

#Salvataggio del dataframe delle entità prodotto nel file unique_entities.csv
output_path = 'unique_entities.csv'
df_unique_entities.to_csv(output_path, index=False)

#Salvataggio del dataframe delle relazioni prodotto nel file unique_relations.csv
output_relations_file = 'unique_relations.csv'
df_unique_relations.to_csv(output_relations_file, index=False)

print(f'File con righe uniche (nomi simili gestiti) salvati come {output_path} e {output_relations_file}')

print(name_map)
