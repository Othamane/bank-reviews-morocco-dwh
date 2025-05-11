import pandas as pd
from transformers import pipeline
from langdetect import detect
import psycopg2
from sqlalchemy import create_engine
import nltk
from nltk.corpus import stopwords
import string
import gensim
import logging
import re

logging.basicConfig(level=logging.INFO)

# Téléchargement des stopwords si nécessaire
nltk.download('punkt')
nltk.download('stopwords')

# Initialize sentiment analysis pipeline
sentiment_pipeline = pipeline('sentiment-analysis', model='nlptown/bert-base-multilingual-uncased-sentiment')

# Connect to PostgreSQL
db_engine = create_engine('postgresql://postgres:azerty@localhost:5432/Data_Warehouse_Project')
connection = db_engine.connect()


def column_exists(connection, table_name, column_name):
    """Check if a column exists in the given table."""
    query = f"""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = '{table_name}' AND column_name = '{column_name}';
    """
    result = connection.execute(query).fetchall()
    return len(result) > 0

# Définir les stopwords pour chaque langue
stopwords_dict = {
    "fr": set(stopwords.words('french')),
    "en": set(stopwords.words('english')),
    "es": set(stopwords.words('spanish'))
}

# Function to preprocess text
def preprocess(text, lang):
    if lang not in stopwords_dict:
        raise ValueError(f"Langue non supportée : {lang}")
    
    tokens = nltk.word_tokenize(text.lower())  # Tokenisation
    tokens = [word for word in tokens if word not in stopwords_dict[lang]]  # Retirer les stopwords
    tokens = [word for word in tokens if word not in string.punctuation]  # Retirer la ponctuation
    return tokens

# Function to extract common topics using LDA
def extract_common_topics(reviews, lang, n_topics=5):
    preprocessed_reviews = [preprocess(review, lang) for review in reviews]
    dictionary = gensim.corpora.Dictionary(preprocessed_reviews)
    corpus = [dictionary.doc2bow(text) for text in preprocessed_reviews]
    lda = gensim.models.LdaModel(corpus, num_topics=n_topics, id2word=dictionary, passes=15, alpha='auto', eta='auto')
    topic_words = {i: [word for word, _ in lda.show_topic(i, topn=5)] for i in range(n_topics)}
    return topic_words



# Function to detect language
def detect_language(text):
    try:
        return detect(text)
    except:
        return None  # En cas d'échec de la détection

# Function to classify sentiment
def classify_sentiment(text):
    result = sentiment_pipeline(text)
    sentiment = result[0]['label']
    
    # Map the sentiment labels to the corresponding numeric values
    if sentiment == '5 stars' or sentiment == '4 stars':
        return "Positive"  # Positive
    elif sentiment == '1 star' or sentiment == '2 stars':
        return "Negative"  # Negative
    else:
        return "Neutral"  # Neutral

def assign_topic(review, topic_words, lang):
    review_words = preprocess(review, lang)  # Passer la langue ici
    topic_counts = {topic_id: sum(1 for word in review_words if word in words) for topic_id, words in topic_words.items()}
    
    if max(topic_counts.values()) > 0:
        return max(topic_counts, key=topic_counts.get)  # Retourne le topic avec le plus de mots correspondants
    else:
        return 0  # Assigne un topic par défaut s'il n'y a pas de correspondance


# Extract topic meaning
def extract_topic_meaning(topic_words):
    topic_descriptions = {}

    for topic_id, top_words in topic_words.items():
        if any(word in top_words for word in ["service", "bon", "avis", "accompagner"]):
            meaning = "Qualité du service et relation client"
        elif any(word in top_words for word in ["frais", "carte", "guichet", "plus"]):
            meaning = "Frais bancaires et gestion des comptes"
        elif any(word in top_words for word in ["dattente", "minutes", "agent", "sécurité"]):
            meaning = "Temps d'attente et gestion en agence"
        elif any(word in top_words for word in ["personnel", "chef", "commerciaux", "sympathique"]):
            meaning = "Expérience avec le personnel"
        elif any(word in top_words for word in ["encore", "pire", "nulle", "ouverture"]):
            meaning = "Problèmes et insatisfactions"
        else:
            meaning = "Autre sujet bancaire"

        topic_descriptions[topic_id] = meaning

    return topic_descriptions

def contains_arabic(text):
    # This regex matches any Arabic characters
    arabic_pattern = re.compile(r'[\u0600-\u06FF]+')
    return bool(arabic_pattern.search(text))

# Example function to filter out comments with Arabic characters
def filter_arabic_comments(df):
    df = df[~df['review_text'].apply(contains_arabic)]  # Keep rows that do not contain Arabic
    return df


# Main function
def main():
    # Vérifiez si les colonnes existent, sinon ajoutez-les
    columns_to_add = {
        'language': 'VARCHAR(10)',
        'sentiment': 'VARCHAR(50)',
        'relative_topic': 'INT',
        'topic_meaning': 'TEXT'
    }
    for col, dtype in columns_to_add.items():
        if not column_exists(connection, 'cleaned_reviews', col):
            connection.execute(f"ALTER TABLE cleaned_reviews ADD COLUMN {col} {dtype};")
            logging.info(f"Added '{col}' column.")

    # Récupérer les données
    query = "SELECT bank_name, branch_name, location, review_text, rating, review_date FROM cleaned_reviews;"
    df = pd.read_sql(query, connection)

    # Filter out reviews containing Arabic script (Franco-Arabic)
    df = filter_arabic_comments(df)

    # Appliquer la détection de la langue et l'analyse des sentiments
    df['language'] = df['review_text'].apply(detect_language)
    # Supprimer les lignes où 'language' est null ou vide
    df = df[df['language'].notnull() & (df['language'] != '')]
     # Filtrer uniquement les reviews en français et en anglais
    df = df[df['language'].isin(['fr', 'en'])]
    df['sentiment'] = df['review_text'].apply(classify_sentiment)

    # Filtrer les reviews pour chaque langue
    for lang in ['fr', 'en', 'es']:
        lang_reviews = df[df['language'] == lang]
        if not lang_reviews.empty:
            # Extraire les topics pour les reviews dans la langue actuelle
            common_topics = extract_common_topics(lang_reviews['review_text'].tolist(), lang, n_topics=5)
            topic_meanings = extract_topic_meaning(common_topics)

            lang_reviews = lang_reviews.copy()  # Create a copy to avoid the warning
            lang_reviews.loc[:, 'relative_topic'] = lang_reviews['review_text'].apply(lambda text: assign_topic(text, common_topics, lang))
            lang_reviews.loc[:, 'topic_meaning'] = lang_reviews['relative_topic'].map(topic_meanings)

            # Mettre à jour la table
            for index, row in lang_reviews.iterrows():
                update_query = """
                UPDATE cleaned_reviews
                SET language = %s, sentiment = %s, relative_topic = %s, topic_meaning = %s
                WHERE bank_name = %s AND branch_name = %s AND location = %s AND review_text = %s;
                """
                connection.execute(update_query, (row['language'], row['sentiment'], row['relative_topic'], row['topic_meaning'], row['bank_name'], row['branch_name'], row['location'], row['review_text']))

    # Delete rows where language is NULL or empty
    delete_query = """
    DELETE FROM cleaned_reviews
    WHERE language IS NULL OR language = '';
    """
    connection.execute(delete_query)
    connection.close()

# Exécuter la fonction principale
if __name__ == "__main__":
    main()
