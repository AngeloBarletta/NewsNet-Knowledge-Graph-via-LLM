import pandas as pd
import streamlit as st
import os
from neo4j import GraphDatabase

def entity_query(type):
    df = pd.DataFrame(columns=['Name', 'Type'])
    results = run_query(driver, f'match (n:{type}) return n')
    for result in results:
        df.loc[len(df)] = [result['n']['name'], type]
    return df

def relation_query(type):
    df = pd.DataFrame(columns=['Source', 'Relation', 'Target'])
    results = run_query(driver, f'match (n)-[r:{type}]->(m) return n,r,m')
    for result in results:
        source = result['r'][0]['name']
        relation = result['r'][1]
        target = result['r'][2]['name']
        df.loc[len(df)] = [source, relation, target]
    return df   

#Configura i dettagli della connessione a Neo4j
NEO4J_URI = "bolt://localhost:7687"  
NEO4J_USER = "neo4j"  
NEO4J_PASSWORD = "password"  

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

st.set_page_config(
    page_title="Make your query",
    page_icon=":mag:",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title(":mag: Explore Dataset")

#st.write(df_entities)
#st.write(df_relations)

col1,col2 = st.columns(2, gap="large")
with col1:

    st.write("Selezionare le entità da visualizzare")
    person = st.checkbox("Person", help='''Un individuo specifico, generalmente identificato per nome. Può includere nomi di persone famose, autori, artisti, scienziati, sportivi, ecc.\n
                        Esempi: "Albert Einstein, "Leonardo da Vinci", "Marie Curie"''')
    organization = st.checkbox("Organization", help='''Un gruppo strutturato di persone che lavorano insieme per un obiettivo comune. Può includere aziende, enti governativi, istituzioni educative, ONG, gruppi sportivi, ecc.\n
                        Esempi: "Google", "Nazioni Unite", "Università di Oxford"''')
    location = st.checkbox("Location", help='''Un luogo geografico specifico, che può essere una città, uno stato, un continente, un punto di interesse, ecc. Può includere anche indirizzi specifici, aree naturali e strutture.\n
                        Esempi: "Roma", "Monte Everest", "Stati Uniti", "Piazza San Marco"''')
    politician = st.checkbox("Politician", help='''Un individuo coinvolto in attività politiche, spesso eletto o nominato a una carica governativa. Può includere presidenti, primi ministri, senatori, sindaci e altri funzionari pubblici.\n
                        Esempi: "Angela Merkel", "Barack Obama", "Giuseppe Conte"''')
    party = st.checkbox("Party", help='''Un'organizzazione politica che rappresenta un gruppo di persone con ideologie e obiettivi comuni, solitamente con l'intento di ottenere e mantenere il potere politico attraverso elezioni.\n
                        Esempi: "Partito Democratico", "Movimento 5 Stelle", "Partito Repubblicano"''')
    event = st.checkbox("Event", help='''Un'occasione particolare, spesso significativa, che può essere pianificata o spontanea. Include conferenze, guerre, catastrofi naturali, festival, eventi sportivi e celebrazioni.\n
                        Esempi: "Giochi Olimpici", "Guerra Civile Americana", "Conferenza sul Clima di Parigi", "Festival di Cannes"''')
    agreement = st.checkbox("Agreement", help='''Un'intesa formalmente riconosciuta tra due o più parti, che stabilisce diritti e doveri reciproci.\n
                        Esempi: "Accordo di Parigi", "Trattato di Maastricht", "Contratto di lavoro collettivo"''')
    

    if person:
        df_person = entity_query("Person")
        st.dataframe(df_person, hide_index=True)

    if organization:
        df_organization = entity_query("Organization")
        st.dataframe(df_organization, hide_index=True)

    if location:
        df_location = entity_query("Location")
        st.dataframe(df_location, hide_index=True)

    if politician:
        df_politician = entity_query("Politician")
        st.dataframe(df_politician, hide_index=True)

    if party:
        df_party = entity_query("Party")
        st.dataframe(df_party, hide_index=True)

    if event:
        df_event = entity_query("Event")
        st.dataframe(df_event, hide_index=True)

    if agreement:
        df_agreement = entity_query("Agreement")
        st.dataframe(df_agreement, hide_index=True)


with col2:
    st.write("Selezionare le relazioni da visualizzare")
    leader_of = st.checkbox("Leader_of", help = '''rapporto tra i leader politici e le entità o i gruppi che guidano. Fondamentale per comprendere la leadership e le affiliazioni politiche.\n
                            Esempio: leader_of, Giorgia Meloni, Fratelli d'Italia''')

    is_from =  st.checkbox("Is_from", help = '''Indica l'origine nazionale degli individui coinvolti in politica, importante per geolocalizzare i personaggi politici.\n
                            Esempio: is_from, Giorgia Meloni, Italia''')

    part_of = st.checkbox("Part_of", help = '''mostra l'appartenenza di entità (come paesi, organizzazioni, dipartimenti) a gruppi più ampi come l'Unione Europea o il Parlamento Europeo.\n
                            Esempio: part_of, Italia, G7''')

    located_in = st.checkbox("Located_in", help = '''specifica la posizione geografica di entità politiche o geografiche, utile per mappare la posizione di istituzioni ed eventi.\n
                            Esempio: located_in, Colosseo, Italia''')

    member_of = st.checkbox("Member_of", help = '''indica l'appartenenza di individui (come politici o persone) a gruppi o organizzazioni politiche, fornendo approfondimenti sulle alleanze politiche.\n
                            Esempio: member_of, Giorgia Meloni, Fratelli d'Italia''')

    supports = st.checkbox("Supports", help = '''rappresenta il sostegno politico dato da una figura o organizzazione a un'altra, rivelando alleanze e coalizioni.\n
                            Esempio: supports, Matteo Salvini, Giorgia Meloni''')

    president_of = st.checkbox("President_of", help = '''identifica i soggetti che ricoprono la carica di presidente di enti politici o istituzionali.\n
                            Esempio: president_of, Sergio Mattarella, Repubblica Italiana''')

    opposition = st.checkbox("Opposition", help = '''Indica opposizione politica tra figure o gruppi, utile per comprendere le dinamiche dei conflitti politici.\n
                            Esempio: opposition, Giuseppe Conte, Giorgia Meloni''')

    colleague = st.checkbox("Colleague", help = '''Indica i rapporti professionali tra individui in politica, evidenziando collaborazioni e collegamenti.\n
                            Esempio: colleague, Giuseppe Conte, Beppe Grillo''')

    if leader_of:
        df_leader_of = relation_query('leader_of')
        st.dataframe(df_leader_of, hide_index=True)
        

    if is_from:
        df_is_from = relation_query('is_from')
        st.dataframe(df_is_from, hide_index=True)

    if part_of:
        df_part_of = relation_query('part_of')
        st.dataframe(df_part_of, hide_index=True)

    if located_in:
        df_located_in = relation_query('located_in')
        st.dataframe(df_located_in, hide_index=True)

    if member_of:
        df_member_of = relation_query('member_of')
        st.dataframe(df_member_of, hide_index=True)

    if supports:
        df_supports = relation_query('supports')
        st.dataframe(df_supports, hide_index=True)

    if president_of:
        df_president_of = relation_query('president_of')
        st.dataframe(df_president_of, hide_index=True)

    if opposition:
        df_opposition = relation_query('opposition')
        st.dataframe(df_opposition, hide_index=True)

    if colleague:
        df_colleague = relation_query('colleague')
        st.dataframe(df_colleague, hide_index=True)


