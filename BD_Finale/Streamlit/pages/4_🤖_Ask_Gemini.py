import streamlit as st
import pandas as pd
import json
from neo4j import GraphDatabase
from streamlit_agraph import agraph, Node, Edge, Config
from streamlit_js_eval import streamlit_js_eval
import google.generativeai as genai
import os

#Configurazione della pagina
st.set_page_config(
    page_title="Ask Gemini",
    page_icon=":robot_face:",
    layout="wide",
    initial_sidebar_state="expanded"
)

#Valore della larghezza della pagina per determinare la larghezza del grafo risultato della query
page_width = streamlit_js_eval(js_expressions='window.innerWidth', key='WIDTH',  want_output = True,)

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

#Filtri per modificare i parametri del modello LLM
st.sidebar.write("Model Parameter")
temperature = st.sidebar.slider(label='temperature', min_value=0.0, max_value=2.0, value=1.0, step=0.05)
top_p = st.sidebar.slider(label='top_p', min_value=0.0, max_value=1.0, value=0.0, step=0.05)
top_k = st.sidebar.slider(label='top_k', min_value=1, max_value=100, value=64, step=1)

#Filtro per applicare o meno la fisica al grafo
physics = True
st.sidebar.write("Graph options")
if not st.sidebar.checkbox(label="Apply physics on graph", value=True):
    physics = False

generation_config = {
  "temperature": 1,
  "top_p": 0,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "application/json",
}


model = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  generation_config=generation_config,
  system_instruction = """
                    Sei un agente che ha il compito di eseguire query in linguaggio cypher sul database a grafo Neo4j.

                    I nodi possono essere di questo tipo:

                    - Person: Un individuo umano specifico, generalmente identificato per nome. Può includere nomi di persone famose, autori, artisti, scienziati, sportivi, ecc.
                    Esempi: "Albert Einstein", "Leonardo da Vinci", "Marie Curie"

                    - Organization: Un gruppo strutturato di persone che lavorano insieme per un obiettivo comune. Può includere aziende, enti governativi, istituzioni educative, ONG, gruppi sportivi, ecc.
                    Esempi: "Google", "Nazioni Unite", "Università di Oxford"

                    - Location: Un luogo geografico specifico, che può essere una città, uno stato, un continente, un punto di interesse, ecc. Può includere anche indirizzi specifici, aree naturali e strutture.
                    Esempi: "Roma", "Monte Everest", "Stati Uniti", "Piazza San Marco"

                    - Politician: Un individuo coinvolto in attività politiche, spesso eletto o nominato a una carica governativa. Può includere presidenti, primi ministri, senatori, sindaci e altri funzionari pubblici.
                    Esempi: "Angela Merkel", "Barack Obama", "Giuseppe Conte"
                                        
                    - Party: Un'organizzazione politica che rappresenta un gruppo di persone con ideologie e obiettivi comuni, solitamente con l'intento di ottenere e mantenere il potere politico attraverso elezioni.
                    Esempi: "Partito Democratico", "Movimento 5 Stelle", "Partito Repubblicano"

                    - Event: Un'occasione particolare, spesso significativa, che può essere pianificata o spontanea. Include conferenze, guerre, catastrofi naturali, festival, eventi sportivi e celebrazioni.
                    Esempi: "Giochi Olimpici", "Guerra Civile Americana", "Conferenza sul Clima di Parigi", "Festival di Cannes"

                    - Agreement: Un'intesa formalmente riconosciuta tra due o più parti, che stabilisce diritti e doveri reciproci.
                    Esempi: "Accordo di Parigi", "Trattato di Maastricht", "Contratto di lavoro collettivo"


                    Le relazioni possono essere di questo tipo:

                    - leader_of: rapporto tra i leader politici e le entità o i gruppi che guidano. Fondamentale per comprendere la leadership e le affiliazioni politiche.

                    - is_from: Indica l'origine nazionale degli individui coinvolti in politica, importante per geolocalizzare i personaggi politici.

                    - part_of: mostra l'appartenenza di entità (come paesi, organizzazioni, dipartimenti) a gruppi più ampi come l'Unione Europea o il Parlamento Europeo.

                    - located_in: specifica la posizione geografica di entità politiche o geografiche, utile per mappare la posizione di istituzioni ed eventi.

                    - member_of: indica l'appartenenza di individui (come politici o persone) a gruppi o organizzazioni politiche, fornendo approfondimenti sulle alleanze politiche.

                    - supports: rappresenta il sostegno politico dato da una figura o organizzazione a un'altra, rivelando alleanze e coalizioni.

                    - president_of: identifica i soggetti che ricoprono la carica di presidente di enti politici o istituzionali.

                    - opposition: Indica opposizione politica tra figure o gruppi, utile per comprendere le dinamiche dei conflitti politici.

                    - colleague: Indica i rapporti professionali tra individui in politica, evidenziando collaborazioni e collegamenti.


                    Solo le relazioni tra i seguenti tipo di nodi sono consentite:
                    Relazione,Tipo1,Tipo2
                    leader_of,Person,Organization
                    leader_of,Person,Party
                    leader_of,Politician,Organization
                    leader_of,Politician,Party
                    is_from,Person,Location
                    is_from,Politician,Location
                    part_of,Organization,Organization
                    part_of,Party,Organization
                    part_of,Organization,Party
                    part_of,Party,Party
                    part_of,Location,Location
                    part_of,Organization,Event
                    part_of,Party,Event
                    located_in,Organization,Location
                    located_in,Party,Location
                    located_in,Event,Location
                    located_in,Person,Location
                    located_in,Location,Location
                    member_of,Politician,Organization
                    member_of,Person,Organization
                    member_of,Politician,Party
                    member_of,Person,Party
                    member_of,Person,Event
                    member_of,Politician,Event
                    supports,Person,Person
                    supports,Politician,Person
                    supports,Organization,Person
                    supports,Party,Person
                    supports,Event,Person
                    supports,Agreement,Person
                    supports,Person,Politician
                    supports,Politician,Politician
                    supports,Organization,Politician
                    supports,Party,Politician
                    supports,Event,Politician
                    supports,Agreement,Politician
                    supports,Person,Organization
                    supports,Politician,Organization
                    supports,Organization,Organization
                    supports,Party,Organization
                    supports,Event,Organization
                    supports,Agreement,Organization
                    supports,Person,Party
                    supports,Politician,Party
                    supports,Organization,Party
                    supports,Party,Party
                    supports,Event,Party
                    supports,Agreement,Party
                    supports,Person,Event
                    supports,Politician,Event
                    supports,Organization,Event
                    supports,Party,Event
                    supports,Event,Event
                    supports,Agreement,Event
                    supports,Person,Agreement
                    supports,Politician,Agreement
                    supports,Organization,Agreement
                    supports,Party,Agreement
                    supports,Event,Agreement
                    supports,Agreement,Agreement
                    president_of,Politician,Organization
                    president_of,Politician,Party
                    president_of,Politician,Event
                    president_of,Person,Organization
                    president_of,Person,Party
                    president_of,Person,Event
                    opposition,Person,Person
                    opposition,Politician,Person
                    opposition,Organization,Person
                    opposition,Party,Person
                    opposition,Event,Person
                    opposition,Agreement,Person
                    opposition,Person,Politician
                    opposition,Politician,Politician
                    opposition,Organization,Politician
                    opposition,Party,Politician
                    opposition,Event,Politician
                    opposition,Agreement,Politician
                    opposition,Person,Organization
                    opposition,Politician,Organization
                    opposition,Organization,Organization
                    opposition,Party,Organization
                    opposition,Event,Organization
                    opposition,Agreement,Organization
                    opposition,Person,Party
                    opposition,Politician,Party
                    opposition,Organization,Party
                    opposition,Party,Party
                    opposition,Event,Party
                    opposition,Agreement,Party
                    opposition,Person,Event
                    opposition,Politician,Event
                    opposition,Organization,Event
                    opposition,Party,Event
                    opposition,Event,Event
                    opposition,Agreement,Event
                    opposition,Person,Agreement
                    opposition,Politician,Agreement
                    opposition,Organization,Agreement
                    opposition,Party,Agreement
                    opposition,Event,Agreement
                    opposition,Agreement,Agreement
                    colleague,Person,Person
                    colleague,Politician,Person
                    colleague,Person,Politician
                    colleague,Politician,Politician

                    Esempi:
                    input: Voglio un query che mi mostri tutti i politici appartenenti al partito Movimento 5 Stelle
                    output: MATCH (p:Politician)-[r:member_of]-(party:Party) WHERE p.name='Movimento 5 Stelle' RETURN n,r,m

                    input: Chi è il leader del Partito Democratico?
                    output: MATCH (p:Politician)-[:leader_of]->(party:Party {name: 'Partito Democratico'}) RETURN p

                    input: Qual è l'evento più bello?
                    output: MATCH (e:Event)-[:member_of]-(p:Person) WITH e, count(p) AS member_count RETURN e.name, member_count ORDER BY member_count DESC LIMIT 1

                    input: Quale partito guida Giuseppe Conte?
                    output: MATCH (p:Politician {name:'Giuseppe Conte'})-[r:leader_of]-(party:Party) return p,r,party
                    """
              )

#Configura i dettagli della connessione a Neo4j
NEO4J_URI = "bolt://localhost:7687"  
NEO4J_USER = "neo4j"  
NEO4J_PASSWORD = "password" 

lista_colori = ['#ADD8E6', '#90EE90', '##F08080', '#FFA07A', '#FFB6C1', '#FAFAD2', '#B0C4DE', '#E0FFFF', '#778899']

#Funzione per ottenere il driver Neo4j
def get_neo4j_driver(uri, user, password):
    driver = GraphDatabase.driver(uri, auth=(user, password))
    return driver

#Funzione per eseguire una query su Neo4j
def run_query(driver, query):
    with driver.session() as session:
        result = session.run(query)
        return [record.data() for record in result]
    
#Connessione a Neo4j
driver = get_neo4j_driver(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

#Titolo della pagina
st.title(":robot_face: Ask Gemini")

col1,col2 = st.columns(2)

# Inizializza il session state per la query
if 'query' not in st.session_state:
    st.session_state.query = ''

with col1:
    question = st.text_area(label="Fai una domanda a Gemini per farti generare una query", placeholder="Chi è il leader del Partito Democratico?")

    if st.button("Generate query"):
        try:
            chat_session = model.start_chat()
            #domanda inviata al modello
            response = chat_session.send_message(question)
            #risposta del modello
            data = json.loads(response.text)
            st.session_state.query = data.get('query', [])
        except:
            st.error("""LLM Error: errore nella generazione della query.\n
- Verificare la correttezza della richiesta
- Verificare che la VPN sia attiva""")

with col2:
    answer = st.text_area(label="Query chypher prodotta da Gemini", value=st.session_state.query)
    query_button = st.button("Execute query")


if query_button:

    nodes = []              #lista di entità
    edges = []              #lista di relazioni
    lista_id = []           #lista utile a verificare che le entità create siano uniche           
    righe_list = []         #lista di output, serve a conservare gli output ritornati da una query (se non sono nodi) per essere inseriti in un dataframe

    try:
        #esegui query su Neo4j
        results = run_query(driver, answer)

        #se la query non ha prodotto risultati
        if not results:
            st.error('La query non ha prodotto risultati')

        #variabile booleana utile a capire se deve essere mostrato il grafo o la tabella
        show_df = True

        if results:
            #si itera su tutti i risultati ottenuti dalla query
            for result in results:
                #indice utile a scegliere il colore da assegnare al nodo del grafo, tutti i nodi con la stessa chiave avranno lo stesso colore
                i=0
                #st.write(result)

                #vettore di appoggio per salvare tutte le informazioni relative ad una singola istanza ritornata            
                risultati = []

                #le chiavi sono le stringhe utilizzate come valori di ritorno nella query, ad esempio n,r,m
                #voglio verificare se almeno uno degli elementi ritornati non è un nodo, se si mostro l'output attraverso una dataframe, altriemtni attraverso il grafo
                #(un elemento è un nodo se riusciamo ad accedere a result[key]['name'])
                for key in result.keys():
                    try:
                        #verfico se l'elemento tornato è un nodo
                        temp = result[key]['name']
                        show_df = False
                    except:
                        try:
                            #verfico se l'elemento tornato è una relazione (devono esistere nodo sorgente e destinazione)
                            temp = result[key][0]['name']
                            temp = result[key][2]['name']
                            show_df = False
                        except:
                            #se sono arrivato qui allora l'elememto non era nè un nodo nè una relazione, devo quindi mostrare l'output attraverso un dataframe
                            show_df = True
                            break


                for key in result.keys():

                    #Se devo mostrare l'output con un df, allora inserisco la singola istanza della risposta in una lista (ovvero i valori assegnati ad ogni chiave)
                    if show_df == True:
                        risultati.append(result[key]) 
                    else:
                        #Se sono qui allora l'output è mostrato con un grafo

                        #Nel caso in cui il numero di entità ritornate dalla query sono maggiori dei colori previsti, si ritorna al primo colore
                        if (i>=len(lista_colori)):              
                            i=0
                        
                        try:
                            #se riusciamo ad accedre a result[key][1] allora siamo in una relazione
                            rel = result[key][1]

                            #vengono aggiunti gli archi relativi alla relazione, recuperando le entità sorgente e destinazione relative a quest'ultima
                            edges.append( Edge(source=result[key][0]['name'],     #source
                                                label=result[key][1],             #relation
                                                target=result[key][2]['name']     #target
                                            ) 
                                        )
                                
                        except(KeyError):

                            #se non esite il campo result[key][1], allora siamo in un nodo e accediamo al campo result[key]['name']
                            nodo = Node(id=result[key]['name'],               #l'id del nodo è la stringa contenuta nel suo campo name
                                        label=result[key]['name'],
                                        size=25,
                                        color = lista_colori[i]
                                        )

                            #solamente nel caso in cui il nodo corrente non è precedentemente stato creato, ne creiamo uno e lo aggiungiamo alla lista di nodi unici
                            if(nodo.id not in lista_id):
                                nodes.append(nodo)
                                lista_id.append(nodo.id)

                            #aggiorniamo il contatore relativo ai colori dei nodi
                            i = i+1

                #Nel caso in cui l'output è un dataframe, popolo la lista con la riga 'risultati' che contiene la singola istanza della risposta
                #Questa lista conterrà alla fine del ciclo for l'intero dataframe
                if show_df:
                    righe_list.append(risultati)

            if show_df:
                #Configurazione del dataframe
                chiavi = list(result.keys())                        #colonne del dataframe da mostrare
                df = pd.DataFrame(righe_list, columns=chiavi)       #creazione del dataframe da mostrare
                st.dataframe(df)
            else:                                    
                #Configurazione del grafo
                config = Config(
                            width=page_width-100,
                            height=1000,
                            nodeHighlightBehavior=True,
                            directed=True, 
                            collapsible=True, 
                            physics=physics, 
                            hierarchical=False,
                            edgeMinimization=False
                            )
                
                #Mostra il grafo
                result = agraph(nodes=nodes, edges=edges, config=config)
    
    except:    
        st.error("Neo4j Error: Verifica la correttezza della query")

#Chiudi la connessione a Neo4j quando l'app viene terminata
driver.close()
