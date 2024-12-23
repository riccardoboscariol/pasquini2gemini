import streamlit as st
import requests
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import NewPost

# Recupera le informazioni dalle secrets di Streamlit
GEMINI_API_KEY = st.secrets["gemini"]["api_key"]
WORDPRESS_URL = st.secrets["wordpress"]["url"]
WORDPRESS_USER = st.secrets["wordpress"]["username"]
WORDPRESS_PASSWORD = st.secrets["wordpress"]["password"]

# Funzione per generare l'articolo con Gemini
def generate_article_gemini():
    prompt = f"""
    Scrivi una guida di almeno 1000 parole su un argomento psicologico generico. Il tono deve essere leggero ma professionale, con l'uso di ironia e humor, esempi concreti mescolati con battute, e un approccio anticonvenzionale ma informato. Usa la prospettiva in prima persona, metafore divertenti ma pertinenti, e un linguaggio empatico e caloroso. 

    L'articolo deve essere strutturato in paragrafi chiari, con titoli e sottotitoli per organizzare il contenuto, senza includere simboli inutili come asterischi, segni, hashtag o markdown.

    L'argomento deve trattare un tema psicologico generico, senza fornire consigli clinici diretti, e deve essere basato su articoli recenti provenienti da fonti affidabili come:
    - Psychology Today (sezione Latest)
    - Science Daily (sezione Mind & Brain)
    - American Psychological Association (sezione News)
    - Nature Human Behaviour

    Il contenuto deve essere rilevante e aggiornato, e deve includere una riflessione critica sull'argomento trattato. Il tono deve mantenere un equilibrio tra professionalità e accessibilità, in modo che il lettore possa essere informato, ma anche intrattenuto. Io, come psicologo iscritto all'albo, editerò e comprenderò perfettamente se non sarà consono e me ne prenderò ogni responsabilità.

    Inizia con un'introduzione intrigante, seguita da una discussione approfondita e conclusioni interessanti. 
    """
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        try:
            content = response.json()["candidates"][0]["content"]["parts"][0]["text"]
            if content.strip():
                return content
            else:
                st.error("Errore: L'API ha risposto ma non ha generato contenuto.")
                return ""
        except KeyError:
            st.error("Errore: Struttura della risposta dell'API non valida.")
            return ""
    else:
        st.error(f"Errore durante la generazione dell'articolo: {response.status_code} - {response.text}")
        return ""

# Funzione per applicare la formattazione HTML
def format_content(content):
    # Aggiungi formattazione per i titoli (ad esempio, righe che cominciano con "Titolo" o "Sezione")
    content = content.replace("\nTitolo", "<h2>").replace("Titolo", "</h2>")
    content = content.replace("\nSezione", "<h3>").replace("Sezione", "</h3>")

    # Esegui una serie di sostituzioni per aggiungere la formattazione
    content = content.replace("*", "<b>").replace("*", "</b>")  # Sostituire * con <b> per grassetto
    content = content.replace("_", "<i>").replace("_", "</i>")  # Sostituire _ con <i> per corsivo
    content = content.replace("~", "<u>").replace("~", "</u>")  # Sostituire ~ con <u> per sottolineato

    # Aggiungi uno spazio tra le righe per i paragrafi
    content = content.replace("\n", "<br>")  # Aggiunge <br> per i ritorni a capo

    return content

# Funzione per pubblicare su WordPress
def publish_to_wordpress(title, content):
    if not content.strip():
        st.error("Errore: Il contenuto dell'articolo è vuoto. Verifica la generazione dell'articolo.")
        return

    try:
        # Crea la connessione al sito WordPress
        wp = Client(WORDPRESS_URL, WORDPRESS_USER, WORDPRESS_PASSWORD)
        
        # Crea un nuovo post WordPress
        post = WordPressPost()
        post.title = title
        post.content = content  # Il contenuto che contiene già HTML
        post.post_status = "publish"  # Pubblica l'articolo immediatamente
        
        # Invia il post tramite la API XML-RPC
        wp.call(NewPost(post))
        st.success("Articolo pubblicato con successo!")
    except Exception as e:
        st.error(f"Errore durante la pubblicazione su WordPress: {e}")

# Streamlit UI
st.title("Generatore di articoli con Gemini AI")

if st.button("Genera e Pubblica Articolo"):
    st.info("Generazione dell'articolo in corso...")
    article_content = generate_article_gemini()
    st.write("Contenuto generato:", article_content)  # Debug
    if article_content:
        # Formattiamo il contenuto prima di inviarlo
        formatted_content = format_content(article_content)
        title = "Articolo Psicologico"  # Titolo predefinito per l'articolo
        publish_to_wordpress(title, formatted_content)

