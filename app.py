#!/usr/bin/env python
# coding: utf-8

# In[1]:


#Imports
import spacy, nltk
from flask import Flask, request, render_template
from spacy.matcher import Matcher
from hunspell import Hunspell
from nltk.corpus import wordnet as wn
from markupsafe import escape

#Load nlp vocab
nlp = spacy.load("en_core_web_sm")
#Initialize matcher to nlp vocab
matcher = Matcher(nlp.vocab)
#Initialize hunspell object
h = Hunspell()
#Download nltk WordNet vocabulary
nltk.download('wordnet')

#As a <user>
user_pattern = [
    [{"POS":"ADP"},{"POS":"DET"},{"POS":"NOUN"}],
    [{"POS":"ADP"},{"POS":"DET"},{"POS":"NOUN"},{"POS":"NOUN"}]
]

#I want <something>
something_pattern = [
    [{"POS":"PRON"},{"POS":"VERB"},{"POS":"PRON"}],
    [{"POS":"PRON"},{"POS":"VERB"},{"POS":"DET"},{"POS":"NOUN"}],
    [{"POS":"PRON"},{"POS":"VERB"},{"POS":"DET"},{"POS":"NOUN"},{"POS":"NOUN"}],
    [{"POS":"PRON"},{"POS":"VERB"},{"POS":"DET"},{"POS":"PROPN"},{"POS":"PROPN"},{"POS":"NOUN"}],
    [{"POS":"PRON"},{"POS":"VERB"},{"POS":"DET"},{"POS":"ADJ"},{"POS":"NOUN"}],
    [{"POS":"PRON"},{"POS":"AUX"},{"POS":"VERB"},{"POS":"PART"}]
]

#to <benefit>
benefit_pattern = [
    [{"POS":"PART"},{"POS":"VERB"}],
    [{"POS":"PART"},{"POS":"VERB"},{"POS":"NOUN"}],
    [{"POS":"PART"},{"POS":"VERB"},{"POS":"NOUN"},{"POS":"PART","OP":"?"},{"POS":"NOUN"}],
    [{"POS":"PART"},{"POS":"VERB"},{"POS":"PRON"}],
    [{"POS":"PART"},{"POS":"VERB"},{"POS":"NOUN"},{"POS":"PRON"},{"POS":"NOUN"},{"POS":"PART", "OP":"?"},{"POS":"NOUN"}],
    [{"POS":"ADP"},{"POS":"NOUN"},{"POS":"NOUN"}],
    [{"POS":"SCONJ"},{"POS":"SCONJ"},{"POS":"PRON"},{"POS":"AUX"},{"POS":"VERB"}]
]

#Add matcher
matcher.add("USER_SOMETHING_BENEFIT", [*user_pattern,*something_pattern,*benefit_pattern])

app = Flask(__name__)

#Page to render
@app.route('/')
def my_form():
    return render_template('index.html')

@app.route('/about.html', methods=['GET'])
def about():
    return render_template('about.html')

@app.route('/Contact.html', methods=['GET'])
def contact():
    return render_template('Contact.html')

@app.route('/index.html', methods=['GET'])
def index():
    return render_template('index.html')

#Does something if there is an incoming POST method
@app.route('/index.html', methods=['POST'])
@app.route('/', methods=['POST'])
def my_form_post():
    #Takes uses query from html page and passes it in doc, an NLP object.
    doc = nlp(request.form['us_text'])
    #Apply matcher to doc
    matches = matcher(doc)
    #Obtain all matches
    spans = [doc[start:end] for _, start, end in matches]
    #The following empty lists are initialized: none duplicates, suggestions for mistakes, words and their part of speech
    #and a list of integers for synonym set counts for every captured noun or verb
    no_dupes = []
    suggestions = []
    words_pos = []
    net_synonym_set = []
    #The for loop matches non duplicates and checks for words's POS (ignores 's tokens)
    for span in spacy.util.filter_spans(spans):
        no_dupes.append(span.text)
        for i in span:
            if i.text != "'s":
                if i.pos_ == "NOUN":
                    words_pos.append([i.text,"n"])
                elif i.pos_ == "VERB":
                    words_pos.append([i.text,"v"])
                if h.spell(i.text) == True:
                    print(h.spell(i.text))
                else:
                    suggestions.append(h.suggest(i.text))
                    print(h.suggest(i.text))
            
        
    
    #CONSOLE STUFF---------------
    print(no_dupes, len(no_dupes))
    for suggestion in suggestions:
        print(suggestion)

    for coll in words_pos:
        print(coll)
        print(len(wn.synsets(coll[0],coll[1])))
        net_synonym_set.append(len(wn.synsets(coll[0],coll[1])))

    print(net_synonym_set)
    
    #Function to calculate avg in a collection of synonym sets (for polysemies)
    def Avg_Polysemies(words_synsets):
        return sum(words_synsets)/len(words_synsets)
        
    #Assigns and prints the avg polysemy count
    avg_poly_in_text = Avg_Polysemies(net_synonym_set)
    print(avg_poly_in_text)
    #CONSOLE STUFF---------------
    
    #Determines whether user story is complete
    us_completeness_re = "Not yet complete, "
    if len(no_dupes) >= 3:
        us_completeness_re = "Complete, "
    
    #Determines whether user story is useful (length restriction)
    us_usefulness_re = "Not quite useful :("
    if len(doc) >= 13 and len(doc) < 18:
        us_usefulness_re = "It has good length"
    elif len(doc) >= 18:
        us_usefulness_re = "A bit to verbose..."
    elif len(doc) < 13:
        us_usefulness_re = "It lacks some words..."
    
    #Check for an average number of polysemy counts or if a synonym set count is zero (words does not exist in dictionary) 
    us_polysemies = "There doesn't seem to be polysemies in your text, "
    for synonym_set in net_synonym_set:
        if synonym_set == 0:
            us_polysemies = "Some words might have no neaning at all, check for errors, "
        elif avg_poly_in_text >= 6:
            us_polysemies = "There might be some polysemies in your text, "
        
    #Notify the user of spellinf mistakes (without suggestions yet)
    errors = "There might be some spelling errors"
    if not suggestions:
        errors = "No spelling errors detected"
        flag=True
    
    #Save previous output strings in one variable to display as a result
    us_final_re = us_completeness_re + us_polysemies + us_usefulness_re
    
    # templateData = {
    #     'system':'System responds...',
    #     'text': 'Your text was: ' + doc.text + '\n' + 'User Story is...' + us_final_re + '\n' + errors #+ processed_text
    # }
    templateData = {
        'system':'System responds...',
        'us': 'Your text was: ' + doc.text, 
        'evaluation': 'User Story is...' + us_final_re,
        'errors': errors,
        'flag':flag
    }
    
    return render_template('index.html', **templateData)

if __name__ == "__main__":
   app.run()


# In[ ]:




