#Pagina dedicata all'esecuzione di query da parte dell'utente sul database neo4j 
import streamlit as st
import pandas as pd
from neo4j import GraphDatabase
from streamlit_agraph import agraph, Node, Edge, Config
from streamlit_js_eval import streamlit_js_eval

#Configurazione della pagina
st.set_page_config(
    page_title="Make your query",
    page_icon=":desktop_computer:",
    layout="wide",
    initial_sidebar_state="expanded"
)


#Configura i dettagli della connessione a Neo4j
NEO4J_URI = "bolt://localhost:7687"  
NEO4J_USER = "neo4j"  
NEO4J_PASSWORD = "password"  

#Questo dizionario è utile a definire un colore per ogni tipo di entità
#In questo modo saranno più facilmente visualizzabili nel momento in cui andremo a vedere il grafo risultato della query
#lista_colori = ["lightblue", "lightred", "lightgreen", "lightred", "orange", "lightgray", "lightbrown"]
lista_colori = ['#ADD8E6', '#90EE90', '##F08080', '#FFA07A', '#FFB6C1', '#FAFAD2', '#B0C4DE', '#E0FFFF', '#778899']
lista_entities = ["Person", "Politician", "Organization", "Location", "Party", "Event", "Agreement"]
lista_relations = ["leader_of", "is_from", "part_of", "located_in", "member_of", "supports", "president_of", "opposition", "colleague"]

#Valore della larghezza della pagina per determinare la larghezza del grafo risultato della query
page_width = streamlit_js_eval(js_expressions='window.innerWidth', key='WIDTH',  want_output = True,)

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
st.title(":desktop_computer: Make your own query")

#Filtro per applicare o meno la fisica al grafo
physics = True
st.sidebar.write("Graph options")
if not st.sidebar.checkbox(label="Apply physics on graph", value=True):
    physics = False

#Utili a mostrare possibili tipi di entità e relazioni uno di fianco all'altro
col1,col2 = st.columns(2)

with col1:
    expander_entities = st.expander("Click to show possibile entity types")
    for entity in lista_entities:
        expander_entities.write(entity)

with col2:
    expander_relations = st.expander("Click to show possible relationship types")
    for relation in lista_relations:
        expander_relations.write(relation)

#Casella di testo all'interno della quale l'utente può inserire la query
query = st.text_area(label="Inserisci una query cypher per interrogare il database Neo4j", placeholder="MATCH (n:Politician)-[r:member_of]-(m:Party) WHERE m.name='Movimento 5 Stelle' return n,r,m")

#Variabile booleana utile a capire se sono contenute parole vietate nella query (es. delete o create)
esegui_query=True

#Bottone per eseguire la query
if st.button("Esegui la query"):
    #Per evitare che venga modificato il db, sono state vietate le istruzioni di create o delete
    if("delete" in str(query.lower()) or "create" in str(query.lower())):
        st.write(query)
        st.error("Operazione di creazione/eliminazione non consentita")
        esegui_query=False
    else:
        esegui_query=True
        
        

    nodes = []              #lista di entità
    edges = []              #lista di relazioni
    lista_id = []           #lista utile a verificare che le entità create siano uniche           
    righe_list = []         #lista di output, serve a conservare gli output ritornati da una query (se non sono nodi) per essere inseriti in un dataframe

    if (esegui_query == True):

        try:
            #esecuzione della query
            results = run_query(driver, query)

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
                                width =page_width-100,
                                height=1000,
                                nodeHighlightBehavior=True,
                                directed=True, 
                                collapsible=True, 
                                physics=physics,
                                edgeMinimization=False
                                )
                    
                    #Mostra il grafo
                    result = agraph(nodes=nodes, edges=edges, config=config)

        except:
            st.error("Neo4j Error: Verifica la correttezza della query")

#Chiudi la connessione a Neo4j quando l'app viene terminata
driver.close()
