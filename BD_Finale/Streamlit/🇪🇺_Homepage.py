import streamlit as st
import base64

#Configurazione della pagina
st.set_page_config(
    page_title="Homepage",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title(":flag-eu: Benvenuto nell'Applicazione di Analisi delle Elezioni Europee 2024")

st.markdown("""
## Introduzione
Questa applicazione ti permette di esplorare e analizzare i dati relativi alle Elezioni Europee 2024. Puoi creare query personalizzate, utilizzare un modello di linguaggio per generare query automaticamente, e visualizzare tutte le entità e le relazioni nel database.
            

## Guida Rapida
1. Vai alla pagina **":bar_chart: Analytics"** per consultare una serie di analytics sui dati.
2. Vai alla pagina **":mag: Explore Dataset"** per vedere tutte le entità e le relazioni attualmente nel database.
3. Vai alla pagina **":desktop_computer: Make your query"** per iniziare a interrogare il database.
4. Vai alla pagina **":robot_face: Ask Gemini"** per chiedere al modello di linguaggio di creare una query per te.
            
## Panoramica delle Funzionalità
- **:bar_chart: Analytics**: Visualizza una serie di analitiche sui dati, inclusi istogrammi e tabelle, per comprendere meglio la distribuzione dei politici per partito e luogo, la struttura dei partiti in termini di leader e membri, e le relazioni di opposizione e supporto tra politici. Tramite filtri e mappe è possibile scegliere i dati da visualizzare.
- **:mag: Explore Dataset**: Ti permette di visualizzare tutti gli elementi presenti nel database organizzati per tipo di entità e relazioni.
- **:desktop_computer: Make your query**: Costruisci query cypher personalizzate per ottenere i dati che ti interessano.
- **:robot_face: Ask Gemini**: Fai una domanda al modello LLM Gemini e questo genererà una query cypher. Utilizza poi la query generata per interrogare il database.        
                            
      - Input: Chi è il leader del Partito Democratico?  
      - Output: MATCH (p:Politician)-[:leader_of]->(party:Party {name: 'Partito Democratico'}) RETURN p

## Esempi di Query
Ecco alcuni esempi di query che puoi utilizzare:
- **Trova tutti i politici di un determinato partito**: `MATCH (p:Politician)-[:member_of]->(party:Party {name: 'Partito Democratico'}) RETURN p`
- **Elenca tutti gli eventi in una specifica location**: `MATCH (e:Event)-[:located_in]->(loc:Location {name: 'Roma'}) RETURN e`

""")

#Legge il PDF e codifica in base64
with open("documentazione.pdf", "rb") as f:
    pdf_data = f.read()
    b64_pdf = base64.b64encode(pdf_data).decode()

#Crea link di download
download_link = f'<a href="data:application/octet-stream;base64,{b64_pdf}" download="documentazione.pdf">Scarica la Documentazione</a>'

#Crea la sezione 'Informazioni Utili' con il link di downlaad della documentazione e il link al manuale Cypher
st.markdown(f"""
## Informazioni Utili
- {download_link}
- [Manuale Cypher](https://neo4j.com/docs/cypher-manual/current/introduction/)
""", unsafe_allow_html=True)

