#Questo script serve a recuperare le news e quindi creare il database su cui opereremo. 
#Usiamo le API di WorldNewsApi per recuperare notizie di tipo politico, in particolare relative alle elezioni europee
import worldnewsapi
import json
from worldnewsapi.rest import ApiException
import re

#Funzione utile a suddividere le notizie recuperate in chunk (con sovrapposizione) a causa dei limiti del modello
def split_text_into_chunks(text, max_length):
    chunks = []
    current_chunk = ""
    last_chunk = ""

    #Dividi il testo utilizzando espressioni regolari per trovare il punto seguito da una lettera maiuscola
    sentences = re.split(r"(?<=\.)\s+(?=[A-Z])", text)

    for sentence in sentences:
        #Verifica se il chunk corrente, concatenato con la prossima frase, supera la lunghezza massima
        if len(current_chunk) + len(sentence) <= max_length:
            current_chunk += ('. ' if current_chunk else '') + sentence.strip()
            last_chunk = sentence
        else:
            chunks.append(current_chunk)
            current_chunk = last_chunk.strip() + sentence.strip() #PER ELIMINARE LA SOVRAPPOSIZIONE ELIMINARE LAST_CHUNK.STRIP()

    #Aggiungi l'ultimo chunk rimasto
    if current_chunk:
        chunks.append(current_chunk)

    return chunks

#Utile a mantenere traccia delle notizie prese da una singola fonte
with open("offset_news.txt", "r") as file:
    offset_news = int(file.readline())

all_results = []
newsapi_configuration = worldnewsapi.Configuration(api_key={'apiKey': "89ad4009733446ab8220c9c67eb7d208"})
max_length = 5000
key_word = 'Elezioni europee'
number_news = 100


try:
    newsapi_instance = worldnewsapi.NewsApi(worldnewsapi.ApiClient(newsapi_configuration))

    response = newsapi_instance.search_news(
            text=key_word,
            language='it',
            news_sources='repubblica.it', #Già usate: ilmattino.it, ilmessaggero.it, ilsole24ore.com, iltempo.it, repubblica.it, liberoquotidiano.it, lastampa.it, notiziegeopolitiche.net
            earliest_publish_date='2024-06-01',
            latest_publish_date='2024-06-25',
            sort="publish-time",
            sort_direction="desc",
            min_sentiment=-1,
            max_sentiment=1,
            offset=offset_news,
            number=number_news)

except ApiException as e:
    print("Exception when calling NewsApi->search_news: %s\n" % e)

try:
    with open('news.json', 'r', encoding='utf-8') as f:
        existing_data = json.load(f)
except FileNotFoundError:
    existing_data = []

#Vengono aggiunti in questa lista tutte le notizie già recuperate
all_results.extend(existing_data)

#Per ogni notizia la si divide in chunk
for article in response.news:
    chunks = split_text_into_chunks(article.text, max_length)

    #Struttura utile per il file .json
    for chunk in chunks:
        article_data = {
            'title': article.title,
            'url': article.url,
            'text': chunk
        }
        #Aggiungiamo alle vecchie news i nuovi chunk
        all_results.append(article_data)

# Salva all_results come file 'news.json'
with open('news.json', 'w', encoding='utf-8') as f:
    json.dump(all_results, f, ensure_ascii=False, indent=4)
    print(f"Risultati salvati correttamente in news_results.json. Numero di articoli: {len(all_results)}")

#Scrivo in un file di testo quante notizie ho preso    
with open("offset_news.txt", "w") as file:
    file.write(str(offset_news+len(response.news)))