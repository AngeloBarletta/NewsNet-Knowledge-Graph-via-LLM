#In questo script interroghiamo il modello llm per ricavare entità e relazioni dalle news
from groq import Groq
import json
import csv
from collections import defaultdict
import os
import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

#Lista che conterrà tutte le notizie e verrà passata al modello come prompt
messages_prompt = []

#Leggo file json da news.json
try:
    with open('news.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
except FileNotFoundError:
    print("Errore: Il file 'news.json' non è stato trovato.")
except json.JSONDecodeError:
    print("Errore: Il file 'news.json' contiene dati non validi.")
except Exception as e:
    print(f"Errore inaspettato: {e}")

#Indice utile a tener conto di quante news già sono state elaborate
with open ("offset_main.txt", "r") as file:
    offset = int(file.readline())
    print(offset)

#Popolamento della lista da passare al modello contenente le news
for i, article in enumerate(data):
    if (i >= offset):
        messages_prompt.append(article['text'])

#Definizione dei percorsi dei file .csv da creare
entities_csv_file = 'entities.csv'
relations_csv_file = 'relations.csv'

#Creo i file se non esistono già
if not os.path.exists(entities_csv_file):
    with open(entities_csv_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Name', 'Type']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

if not os.path.exists(relations_csv_file):
    with open(relations_csv_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Relation', 'Source', 'Target']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()


# Create the model
# See https://ai.google.dev/api/python/google/generativeai/GenerativeModel
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "application/json",
}

model = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  generation_config=generation_config,
  system_instruction = """
                    Esegui NER e RE su testo non strutturato relativo a news sulle elezioni europee 2024, individua entità e relazioni i cui possibili tipi sono elencati di seguito: 

                    Le entità devono essere di queste tipologie: 'Person', 'Organization', 'Location', 'Politician', 'Party', 'Event', 'Agreement'
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

                    Le relazioni devono essere di questi tipi:
                    leader_of: rapporto tra i leader politici e le entità o i gruppi che guidano. Fondamentale per comprendere la leadership e le affiliazioni politiche.

                    is_from: Indica l'origine nazionale degli individui coinvolti in politica, importante per geolocalizzare i personaggi politici.

                    part_of: mostra l'appartenenza di entità (come paesi, organizzazioni, dipartimenti) a gruppi più ampi come l'Unione Europea o il Parlamento Europeo.

                    located_in: specifica la posizione geografica di entità politiche o geografiche, utile per mappare la posizione di istituzioni ed eventi.

                    member_of: indica l'appartenenza di individui (come politici o persone) a gruppi o organizzazioni politiche, fornendo approfondimenti sulle alleanze politiche.

                    supports: rappresenta il sostegno politico dato da una figura o organizzazione a un'altra, rivelando alleanze e coalizioni.

                    president_of: identifica i soggetti che ricoprono la carica di presidente di enti politici o istituzionali.

                    opposition: Indica opposizione politica tra figure o gruppi, utile per comprendere le dinamiche dei conflitti politici.

                    colleague: Indica i rapporti professionali tra individui in politica, evidenziando collaborazioni e collegamenti.

                    L'output deve essere in JSON:
                    {
                        "entities": [
                            {"Name": "Entità1", "Type": "TipoEntità1"},
                            {"Name": "Entità2", "Type": "TipoEntità2"}
                        ],
                        "relations": [
                            {"Relation": "TypeOfRelation1", "Source": "Entità1", "Target": "Entità2"},
                            {"Relation": "TypeOfRelation2", "Source": "Entità2", "Target": "Entità2"}
                        ]
                    }

                    JSON:
                    """
              )


chat_session = model.start_chat()


#Ciclo per interrogare il modello con una news alla volta
#Al modello vengono passate le informazioni relative a quali tipologie di entità e relazioni trovare
for i in range(0,len(messages_prompt)):
    print("\n" + messages_prompt[i])

    response = chat_session.send_message(messages_prompt[i])

    #La risposta del modello viene messa nella variabile content
    data = json.loads(response.text)

    print(f"Article {i}:")
    print(data)

    #Sia per le entità che per le relazioni è necessario che non esistano chiavi duplicate
    unique_entities = []
    seen_entities = set()
    for entity in data.get("entities", []):
        filtered_entity = {key: entity[key] for key in ['Name', 'Type'] if key in entity}
        entity_tuple = tuple(filtered_entity.items())
        if entity_tuple not in seen_entities:
            seen_entities.add(entity_tuple)
            unique_entities.append(filtered_entity)

    #Filtra i campi necessari e rimuovi duplicati nelle relazioni
    unique_relations = []
    seen_relations = set()
    for relation in data.get("relations", []):
        filtered_relation = {key: relation[key] for key in ['Relation', 'Source', 'Target'] if key in relation}
        relation_tuple = tuple(filtered_relation.items())
        if relation_tuple not in seen_relations:
            seen_relations.add(relation_tuple)
            unique_relations.append(filtered_relation)

    #creazione dizionario dei dati unici
    filtered_data = {
        "entities": unique_entities,
        "relations": unique_relations
    }


    #Scrittura file json
    with open('output.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    #Leggi il file JSON
    with open('output.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    #Estrazione e filtraggio delle entità, il filtraggio serve a verificare che vengano presi i campi corretti del file
    entities = data['entities']
    filtered_entities = []
    for entity in entities:
        filtered_entity = {key: entity[key] for key in ['Name', 'Type'] if key in entity}
        filtered_entities.append(filtered_entity)

    #Estrazione e filtraggio delle relazioni
    relations = data['relations']
    filtered_relations = []
    for relation in relations:
        filtered_relation = {key: relation[key] for key in ['Relation', 'Source', 'Target'] if key in relation}
        filtered_relations.append(filtered_relation)

    #print(filtered_entities)
    #print(filtered_relations)

    #Aggiungiamo al file entities.csv, le nuove entità trovate dal modello 
    with open(entities_csv_file, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Name', 'Type']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        for entity in filtered_entities:
            writer.writerow(entity)

    #Aggiungiamo al file relations.csv, le nuove relazioni trovate dal modello
    with open(relations_csv_file, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Relation', 'Source', 'Target']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        for relation in filtered_relations:
            writer.writerow(relation)

    print(f"Entities written to {entities_csv_file}")
    print(f"Relations written to {relations_csv_file}")

    #Aggiornamento del file contenente l'offset delle notizie già processate
    with open ("offset_main.txt", "w") as file:
        file.write(str(offset+i+1))
