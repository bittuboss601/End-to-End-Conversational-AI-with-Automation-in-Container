import nltk
import spacy

# essential entity models downloads
nltk.downloader.download('maxent_ne_chunker')
nltk.downloader.download('words')
nltk.downloader.download('treebank')
nltk.downloader.download('maxent_treebank_pos_tagger')
nltk.downloader.download('punkt')
nltk.download('averaged_perceptron_tagger')


import locationtagger

# initializing sample text
sample_text = "I am from Patna, Bihar."

# extracting entities.
place_entity = locationtagger.find_locations(text = sample_text)

# getting all countries
print("The countries in text : ")
print(place_entity.countries)

# getting all states
print("The states in text : ")
print(place_entity.regions)

# getting all cities
print("The cities in text : ")
print(place_entity.cities)
