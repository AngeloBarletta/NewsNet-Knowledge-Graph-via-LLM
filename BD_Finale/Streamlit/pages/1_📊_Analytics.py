import streamlit as st
import pandas as pd
import json
from neo4j import GraphDatabase
from streamlit_agraph import agraph, Node, Edge, Config
from streamlit_js_eval import streamlit_js_eval
import google.generativeai as genai
import folium
from streamlit_folium import st_folium
import geopandas as gpd
from shapely.geometry import Point
import os

#Configurazione della pagina
st.set_page_config(
    page_title="Analytics",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title(":bar_chart: Analytics")


#Configura i dettagli della connessione a Neo4j
NEO4J_URI = "bolt://localhost:7687"  
NEO4J_USER = "neo4j"  
NEO4J_PASSWORD = "password"

#Valore della larghezza della pagina per determinare la larghezza del grafo risultato della query
page_width = streamlit_js_eval(js_expressions='window.innerWidth', key='WIDTH',  want_output = True,)

#Funzione per ottenere il driver Neo4j
def get_neo4j_driver(uri, user, password):
    driver = GraphDatabase.driver(uri, auth=(user, password))
    return driver

#Funzione per eseguire una query su Neo4j
def run_query(driver, query, parameters=None):
    with driver.session() as session:
        result = session.run(query, parameters)
        return [record.data() for record in result]

#Connessione a Neo4j
driver = get_neo4j_driver(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

@st.cache_data
def get_parties():
    party_list = []
    query = "match (p:Party)-[:member_of]-(n:Politician) with p, count(n) as count where count>=1 return p order by count desc"
    results = run_query(driver, query)
    for result in results:
        party_list.append(result['p']['name'])
    return party_list


party_list = get_parties()          # lista di tutti i partiti del db


col1, col2 = st.columns(2)

#Filtro per selezionare i partiti da visualizzare e su cui eseguire la query
st.sidebar.write("Filters")
party_selected = st.sidebar.multiselect("Scegli i partiti da visualizzare", options=party_list, default=party_list[:3])

####################    PRIMA QUERY    ########################
query_1 = """MATCH (p:Politician)-[:member_of|leader_of]->(party:Party)
             WHERE party.name IN $party_selected
            RETURN party.name AS Partito, count(p) as NumeroPolitici
        """
with col1:
    st.subheader("Numero di Politici per Partito")
if party_selected:
    results_1 = run_query(driver, query_1, {'party_selected':party_selected})
    if results_1:
        with col1:
            col11, col12 = st.columns(2)
            with col11:
                st.bar_chart(results_1, x='Partito', y='NumeroPolitici')
            with col12:
                st.dataframe(results_1)
else:
    with col1:
        st.error("Nessun partito selezionato")


####################    TERZA QUERY    ########################
query_3 = """MATCH (leader:Politician)-[:leader_of]->(p:Party)<-[:member_of]-(m:Politician)
             where p.name IN $party_selected
             with p, collect(distinct leader.name) as Leader, collect(distinct m.name) as Members
             return p.name as Party, Leader, Members
        """

with col2:
    st.subheader("Leader e Membri per Partito")
    if party_selected:
        results_3 = run_query(driver, query_3, {'party_selected':party_selected})
        if results_3:
            st.dataframe(results_3, height=300)
    else:
        st.error("Nessun partito selezionato")


st.markdown("""---""")


col3, col4 = st.columns(2)
############################################    MAPPA   ####################################################
# Dizionario per la traduzione dei nomi delle nazioni da inglese a italiano
name_translation = {
    'Albania': 'Albania',
    'Andorra': 'Andorra',
    'Austria': 'Austria',
    'Belarus': 'Bielorussia',
    'Belgium': 'Belgio',
    'Bosnia and Herz.': 'Bosnia-Erzegovina',
    'Bulgaria': 'Bulgaria',
    'Croatia': 'Croazia',
    'Cyprus': 'Cipro',
    'Czechia': 'Repubblica Ceca',
    'Denmark': 'Danimarca',
    'Estonia': 'Estonia',
    'Finland': 'Finlandia',
    'France': 'Francia',
    'Germany': 'Germania',
    'Greece': 'Grecia',
    'Hungary': 'Ungheria',
    'Iceland': 'Islanda',
    'Ireland': 'Irlanda',
    'Italy': 'Italia',
    'Kosovo': 'Kosovo',
    'Latvia': 'Lettonia',
    'Liechtenstein': 'Liechtenstein',
    'Lithuania': 'Lituania',
    'Luxembourg': 'Lussemburgo',
    'Malta': 'Malta',
    'Moldova': 'Moldavia',
    'Monaco': 'Monaco',
    'Montenegro': 'Montenegro',
    'Netherlands': 'Paesi Bassi',
    'North Macedonia': 'Macedonia del Nord',
    'Norway': 'Norvegia',
    'Poland': 'Polonia',
    'Portugal': 'Portogallo',
    'Romania': 'Romania',
    'Russia': 'Russia',
    'San Marino': 'San Marino',
    'Serbia': 'Serbia',
    'Slovakia': 'Slovacchia',
    'Slovenia': 'Slovenia',
    'Spain': 'Spagna',
    'Sweden': 'Svezia',
    'Switzerland': 'Svizzera',
    'Ukraine': 'Ucraina',
    'United Kingdom': 'Regno Unito',
    'Vatican City': 'Città del Vaticano'
}

# Carica il dataset contenente la mappa dell'europa
shapefile_dir="ne_110m_admin_0_countries"
shapefile_name="ne_110m_admin_0_countries.shp"
shapefile_path = os.path.join(shapefile_dir, shapefile_name)  # percorso del file shapefile

gdf = gpd.read_file(shapefile_path)
europe = gdf[gdf['CONTINENT'] == 'Europe']  # vengono recuperate solo le nazioni europee

# Inizializza la lista delle nazioni selezionate nella sessione (inizializzata con dei valori de default)
if 'selected_countries' not in st.session_state:
    st.session_state.selected_countries = ["Italia", "Francia", "Germania"]

# Funzione per creare una mappa di Folium
def create_map():
    m = folium.Map(location=[54, 15], zoom_start=4)
    
    for _, row in europe.iterrows():
        folium.GeoJson(
            row['geometry'],
            name=row['NAME'],
            style_function=lambda x: {'fillColor': '#ffaf00', 'color': '#ffaf00', 'weight': 1},
            highlight_function=lambda x: {'fillColor': '#ffaf00', 'color': '#000000', 'weight': 3},
            tooltip=row['NAME'],
            interactive=True
        ).add_to(m)
    
    return m

with col3:
    # Visualizza la mappa con streamlit_folium
    st.subheader("Seleziona uno o più paesi dalla mappa")
    m = create_map()
    map_data = st_folium(m, width=700, height=450)

    #Tramite latitudine e longitudine del punto cliccato sulla mappa, reupera la nazione (last_object_clicked contiene le coordinate del click)
    if map_data['last_object_clicked'] is not None:
        lat = map_data['last_object_clicked']['lat']
        lon = map_data['last_object_clicked']['lng']
        clicked_point = Point(lon, lat)
        
        # Crea un GeoDataFrame per il punto cliccato
        clicked_point_gdf = gpd.GeoDataFrame(index=[0], crs=europe.crs, geometry=[clicked_point])
        
        # Esegui uno spatial join per trovare il paese che contiene il punto cliccato
        result = gpd.sjoin(clicked_point_gdf, europe, how='left', predicate='within')
        
        if not result.empty:
            # Recupero del nome originale della nazione, che viene poi tradotto in italiano (nel db i nomi dei paesi sono in italiano)
            selected_country = result.iloc[0]['NAME']
            # Traduzione del nome del paese
            translated_country = name_translation.get(selected_country, selected_country)

            # Se non abbiamo già aggiunto la nazione alla variabile selected_country
            if(translated_country not in st.session_state.selected_countries):
            
                st.write(f"Hai selezionato: {translated_country}")
                
                # Aggiungi il paese alla lista delle nazioni selezionate nella sessione
                st.session_state.selected_countries.append(translated_country)


# Creo una lista di nomi di tutte le nazioni europee (in italiano) da usare come possibili opzioni della multiselect
europe["NAME"] = europe["NAME"].apply(lambda x: name_translation[x])
# Creo una multiselect i cui valori possono essere settati o premento sulla mappa, oppure scegliendo tra le pzioni della multiselect.
# Il valore di default uguale alla variabile selected_countries serve a far si che la multiselect si aggiorni con la mappa
location_selected = st.sidebar.multiselect(label="Paesi selezionati", options=europe["NAME"], default=st.session_state.selected_countries)
# Serve a far si che se è stato selezionata una delle opzioni della multiselect (non dalla mappa), la variabile di stato sarà uguale alla nuova lista di nazioni
st.session_state.selected_countries = location_selected     

####################    SECONDA QUERY    ########################
query_2 = """MATCH (p:Politician)-[:is_from]->(country:Location)
             WHERE country.name in $location_selected
             RETURN country.name AS Paese, COUNT(p) AS NumeroPolitici
        """

with col4:
    st.subheader("Numero di Politici per paese di origine")
if location_selected:
    results_2 = run_query(driver, query_2, {'location_selected':location_selected})
    if results_2:
        with col4:
            col41, col42 = st.columns(2)
            with col41:
                st.bar_chart(results_2, x='Paese', y='NumeroPolitici')
            with col42:
                st.dataframe(results_2)
else:
    with col4:
        st.error("Nessun paese selezionato")


st.markdown("""---""")


col5, col6, col7 = st.columns([2,1,2])
####################    QUARTA QUERY    ########################
query_4 = """match (n:Politician)-[r:member_of|leader_of]-(p:Party) where p.name in $party_selected
             match (n)-[r3:supports]-(x)
             with n, count(x.name) as Supporters
             match (n)-[r4:opposition]-(y)
             return n.name as Name, Supporters, count(y.name) as Oppositori
        """

with col5:
    st.subheader("Numero di supporters per politico")
with col7:
    st.subheader("Numero di oppositori per politico")
if  party_selected:
    results_4 = run_query(driver, query_4, {'party_selected':party_selected})
    if results_4:
        with col5:
            st.bar_chart(results_4, x='Name', y='Supporters')
        with col6:
            st.dataframe(results_4)
        with col7:
            st.bar_chart(results_4, x='Name', y='Oppositori')
else:
    st.error("Nessun partito selezionato")


st.markdown("""---""")

        
col8, col9 = st.columns(2)
####################    QUINTA E SESTA QUERY    ########################
query_5 = """MATCH (p:Party)-[:supports]->(a:Agreement) 
             WHERE p.name in $party_selected
             RETURN p.name as Name, collect(a.name) AS Supported_agreements
        """
query_6 = """MATCH (party:Party)<-[:member_of|leader_of]-(p:Politician)-[:supports]->(a:Agreement) 
             WHERE party.name in $party_selected
             RETURN p.name as Name, party.name as Party, collect(a.name) AS Supported_agreements
        """

with col8:
    st.subheader("Accordi supportati da ciascun partito")
    if  party_selected:
        results_5 = run_query(driver, query_5, {'party_selected':party_selected})
        st.dataframe(results_5)
    else:
        st.error("Nessun partito selezionato")
with col9:
    st.subheader("Accordi supportati da ciascun politico")
    if  party_selected:
        results_6 = run_query(driver, query_6, {'party_selected':party_selected})
        if results_6:
            st.dataframe(results_6)
    else:
        st.error("Nessun partito selezionato")
