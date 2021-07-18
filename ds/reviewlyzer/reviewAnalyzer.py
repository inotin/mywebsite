#!/usr/bin/env python
# coding: utf-8

# In[184]:


from youtube_transcript_api import YouTubeTranscriptApi
from bs4 import BeautifulSoup
from bs4.element import Comment
import urllib.request
import numpy as np
from . import charwords, googleCreds
from tqdm import tqdm
import nltk
from nltk.corpus import wordnet
from nltk.corpus import opinion_lexicon
#nltk.download('opinion_lexicon')
from nltk.sentiment import vader
#nltk.download('vader_lexicon')
from nltk.tokenize import treebank
from nltk.corpus import stopwords
from deepsegment import DeepSegment
from scipy.stats import hmean
import pandas as pd
from collections import defaultdict
from sklearn.preprocessing import MinMaxScaler
import warnings
warnings.filterwarnings('ignore')
from youtubesearchpython import VideosSearch
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from IPython.core.display import display,HTML
from google_images_search import GoogleImagesSearch
from scipy.stats import ttest_ind
from plotly.subplots import make_subplots
# In[218]:


def getYouTubeLinksFromSearch(query, maxNumber = 5):
    """
    The function returns a list of youtube urls from the query results

    Input:
    query:      str
                a string for searching youtube videos

    maxNumber:  int, default: 5
                number of urls for output,

    Output:
    list(str): list of urls

    """
    videosSearch = VideosSearch(query, limit = maxNumber, region='US')
    ids = []
    for i in videosSearch.result()['result']:
        ids.append('https://www.youtube.com/watch?v='+i['id'])
        #print(i['title'])
    return ids

#Test
# getYouTubeIDsFromSearch('iphone 11 pro')


# ## Fetching textual data

# In[210]:


def getTextFromYoutubeCaptions(vidId):
    """
    The function gets text from captions in the YouTube video, ID of which is given as an input.

    Input:
    vidId: str
           YouTube Video ID

    Output:
    str: list of words from the captions
    """
    # try:
    transcript_list = YouTubeTranscriptApi.list_transcripts(vidId)
    captions = ["NoText"]
    try:
        captions = YouTubeTranscriptApi.get_transcript(vidId, languages=['en'])
    except:
        #print("!Translating captions to English")
        transcript = transcript_list.find_transcript(['ru','it'])
        captions = transcript.translate('en').fetch()
        #print(captions)
        #input()
    text = ""

    for element in captions:
        text+=element['text']+" "
    text = text.replace("\n"," ")
    # print(text)
    return text
    # except:
    #     print('Captions are not available')
    #     return 'Captions are not available'

#Testing function
# getTextFromYoutubeCaptions("eOW9jgCahnk")[:100]


# In[174]:


def tag_visible(element):
    """
    The function defines if element is visible

    Input:
    html element

    Output:
    bool: True if visible, False otherwise
    """

    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True

def getTextFromUrl(url):
    """
    The function returns visible text from html

    Input:
    html

    Output:
    str: text
    """
    html = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(html, 'html.parser')
    texts = soup.findAll(text=True)
    visible_texts = filter(tag_visible, texts)
    return u" ".join(t.strip() for t in visible_texts)
#Testing
# getTextFromUrl('https://www.ilpost.it/2021/03/19/cina-stati-uniti-alaska-blinken/')[:1000]


# ## Scoring functions
# In this sections scoring functions are defined. They return score for a given piece of text. The higher the score the more positive text is. Further these functions will be used to assess pieces of text around keywords.

# In[175]:
import nltk
nltk.download('opinion_lexicon')
nltk.download('vader_lexicon')
def assessPolarity(text):
    """
    Polarity assessment based on Liu and Hu opinion lexicon
    """
    stop_words = set(stopwords.words('english'))
    tokenizer = treebank.TreebankWordTokenizer()
    wordsList = [word.lower() for word in tokenizer.tokenize(text)]
    wordsList = [word for word in wordsList if not word in stop_words]
    scores = []

    for word in wordsList:
        if word in set(opinion_lexicon.positive()):
            score = 1
        elif word in set(opinion_lexicon.negative()):
            score=-1
        else:
            score=0
        scores.append(score)
#     print(words)
#     print(scores)
    return np.sum(scores)

#Testing
# text = getTextFromYoutubeCaptions("eOW9jgCahnk")
# assessPolarity(text)


# In[176]:


def assessPolarityVader(text, split_sentences = False):
    """
    Polarity assessment based on Vader
    """
    sia = vader.SentimentIntensityAnalyzer()
    #it's better to feed vader with phrases or sentences
    #but as soon as caption text does not contain punctuation i used deepsegment library
    #to split the caption text into sentences
    score = 0
    if split_sentences:
        segmenter = DeepSegment('en')
        sentenceList = segmenter.segment_long(text)

        for sentence in sentenceList:
            s = sia.polarity_scores(sentence)['compound']
#             print(sentence)
#             print('Score:', s)
#             print('-'*20)
            score+=s
    else:
        score+=sia.polarity_scores(text)['compound']
    return score

#testing
# text = getTextFromYoutubeCaptions("eOW9jgCahnk")
# assessPolarityVader(text, split_sentences = True)


# In[177]:


def antiScore(score):
    """
    A function that returns a penalyzing score for word "not" according to the function

    Input:
    score (float): input score

    Output:
    float: a penalty to be added to the initial score if word "not" is present in the word list

    """

    return 0.58 - 1.15*score


def assessPolarityCustom(text, dictScores=None):
    """
    The function returns score for the piece of text given as input list of words according to dictScores

    Input:
    pieceOfText (list(str)): keywords to search for
    dictScores (dict): a dictionary of words and corresponding scores in form:
             {"A":[5,["very", "extremely", "surprisingly","great", "much", "incredibly"]],
              "B":[4,["pretty","good", "nice"]],
              "C":[3, ["enough","inexpensive", "cheap", "affordable","low","decent", "quite"]],
              "D":[-2,["weak","minimum","little"]]}

    Output:
    float: score
    """
    if dictScores == None:
        dictScores = {"A":[5,["very", "extremely", "surprisingly","great", "much", "plenty","incredibly"]+charwords.veryWords],
              "B":[4,["pretty","good", "nice"]+charwords.prettyWords],
              "C":[3, ["enough", "affordable","low","decent", "quite"]+charwords.enoughWords],
              "D":[-2,["weak","minimum","little"]+charwords.weakWords]}

    stop_words = set(stopwords.words('english'))
    tokenizer = treebank.TreebankWordTokenizer()
    wordsList = [word.lower() for word in tokenizer.tokenize(text)]
    wordsList = [word for word in wordsList if not word in stop_words]

    score = 0
    lastScore = 0
    wordsList = list(set(wordsList))
    #print(wordsList)
    for word in wordsList:
        for key in dictScores:
            if word in dictScores[key][1]:
                lastScore = dictScores[key][0]
                #print(word,":",lastScore)
        if word == "not":
            lastScore = lastScore + antiScore(lastScore)
        score += lastScore
        lastScore=0
    return score

#Testing
# text = getTextFromYoutubeCaptions("eOW9jgCahnk")
# assessPolarityCustom(text)


# ## Working with keywords
# In this section the function is defined which allows to extract a set amount of words around a key word.

# In[178]:
# import nltk
# nltk.download('stopwords')

def getPieceByKeyWords(text, keyWords, backward=5, forward=5):
    """
    The function returns a piece of caption text in a form of list with a given range.

    Input:
    text (str): input list of the caption text
    keyWords (list(str)): keywords to search for
    backward (int): number of words to include before found keyword
    forward (int): number of words to include before found keyword

    Output:
    list(str): list of words close to a given keyword
    """

    #stop_words = set(stopwords.words('english'))
    tokenizer = treebank.TreebankWordTokenizer()
    wordsList = [word.lower() for word in tokenizer.tokenize(text)]

    lst = []
    i = 0

    for word in wordsList:
        if word in set(keyWords):
            rear = max(0, i - backward)
            front = min(len(wordsList)-1, i+forward)
            lst.append(" ".join(wordsList[rear:front]))
        i+=1
    return lst

#Testing
# text = getTextFromYoutubeCaptions("eOW9jgCahnk")
# getPieceByKeyWords(text, ['engine'])


# In[207]:



def getScores(dct, keyWords):
    scoresDict = defaultdict()
    dctForHist = {'name':[],'keyword':[], 'aP':[], 'aPV':[],'aPC':[]}
    for url in tqdm(dct['urls']):
        # try:
        if 'youtube' in url:
            text = getTextFromYoutubeCaptions(url.split('=')[1])
        else:
            text = getTextFromUrl(url)

        for keyWord in keyWords:
            textList = getPieceByKeyWords(text,[keyWord])
            aP, aPV, aPC = 0, 0, 0
            for t in textList:
                aP+=assessPolarity(t)
                aPV+=assessPolarityVader(t)
                aPC+=assessPolarityCustom(t)
            scoresDict[keyWord] = [aP,aPV,aPC]
            #print(keyWord,aP,aPV,aPC)
            dctForHist['name'].append(dct['name'])
            dctForHist['keyword'].append(keyWord)
            dctForHist['aP'].append(aP)
            dctForHist['aPV'].append(aPV)
            dctForHist['aPC'].append(aPC)
        # except:
        #     print(f'Captions were not obtained for {url}')
        #     pass
    df3 = pd.DataFrame(dctForHist)
    df3['mean']=np.mean(df3[['aP', 'aPV', 'aPC']],axis=1)

    df = pd.DataFrame(scoresDict)
    #print(df)
    df = df.T
    #mms = MinMaxScaler()
    #df = mms.fit_transform(df)
    df = pd.DataFrame(df.T, columns=keyWords)
    df2 = pd.DataFrame({'name':[dct['name']]})
    df2 = pd.concat([df2,pd.DataFrame(np.mean(df)).T],axis = 1)

    return df2, df3

#Testing
# dct = {'name':"Honda CB650R",'urls':["https://www.youtube.com/watch?v=PO2uFDS1P3A",
#            "https://www.youtube.com/watch?v=GQK79vCohC4",
#            "https://www.youtube.com/watch?v=5AR5PwffLzI",
#            "https://www.youtube.com/watch?v=c0SL4pBJP4Y",
#            "https://ridermagazine.com/2020/06/05/2020-husqvarna-vitpilen-701-road-test-review/"]}

# print(getScores(dct, ['comfort','engine', 'design', 'handling']))


# In[179]:


def getSynonimList(word):
    """
    The function returns list of synonims base on wordnet.synsets of nltk library
    for the text provide by urlList based on key words and dictScores

    Input:
    word (str): input word

    Output:
    list(str)
    """

    synonyms = []

    for syn in wordnet.synsets(word):
        for l in syn.lemmas():
            synonyms.append(l.name().lower())
    print(synonyms)
    return (list(set(synonyms)))
#Testing
#getSynonimList('cost')


# In[214]:


def getSetScores(productNames, productKeyWords, plot = False):
    """
    The function returns a dataframe with scores for products according to key words.

    Input:
    productNames    (list): input list of strings with product names
    productKeyWords (list): input list of strings with key words
    plot            (bool): default=False, if true plots barplots with scores and saves them to HTML ("result.html")

    Output:
    pandas dataframe with scores
    """
    productSet = []
    for product in productNames:
        dct = defaultdict()
        dct['name']=product
        dct['urls']=getYouTubeLinksFromSearch(product)
        productSet.append(dct)

    df = pd.DataFrame()
    for m in productSet:
        df = pd.concat([df, getScores(m,productKeyWords)])

    df['total']=np.mean(df.iloc[:,1:], axis = 1)
    if plot:
        numOfPlots = int(np.sum([np.sum(df[x].sum()!=0)>0 for x in df.columns[1:]]))

        fig = make_subplots(rows=numOfPlots, cols=1,
                    vertical_spacing=0.04)

        r=1
        for n in df.columns[1:]:
            if np.sum(df[n].sum()!=0)>0:
                fig.add_trace(go.Bar(x=df['name'], y=df[n], name = n),
                              row=r, col=1,)
                r+=1
        fig.update_layout(height=200*numOfPlots)
        fig.show()
        fig.write_html("static/reviewlizer/result.html")

    df.to_html('static/reviewlizer/df.html')
    return df


# In[223]:


def getSetScoresText(productNames, productKeyWords, plot = False, maxNumber = 5, api_key=googleCreds.GOOGLE_API_KEY2, cx = googleCreds.GOOGLE_CX):
    """
    The function returns a dataframe with scores for products according to key words.

    Input:
    productNames    (str): input string with product names separated by \n
    productKeyWords (str): input string with key words separated by \n
    plot            (bool): default=False, if true plots barplots with scores and saves them to HTML ("result.html")

    Output:
    pandas dataframe with scores
    """
    #global fig
    fig = None

    productNames = productNames.replace('\r','')
    productKeyWords = productKeyWords.replace('\r','')

    productNames = productNames.split('\n')
    productKeyWords = productKeyWords.split('\n')
    print(productNames)
    print(productKeyWords)
    # input()
    productSet = []
    for product in productNames:
        dct = defaultdict()
        dct['name']=product
        dct['urls']=getYouTubeLinksFromSearch(product, maxNumber)
        productSet.append(dct)

    df = pd.DataFrame()
    df2 = pd.DataFrame()
    for m in productSet:
        dfT = getScores(m,productKeyWords)
        df = pd.concat([df, dfT[0]])
        df2 = pd.concat([df2, dfT[1]])

    # df = pd.DataFrame()
    # for m in productSet:
    #     dfT = getScores(m,productKeyWords)
    #     print(dfT)
    #     df = pd.concat([df, dfT])

    df['total']=np.mean(df.iloc[:,1:], axis = 1)
    print(df2)
    if plot:
        numOfPlots = int(np.sum([np.sum(df[x].sum()!=0)>0 for x in df.columns[1:]]))
        if numOfPlots!=0:
            fig = make_subplots(rows=numOfPlots, cols=1,
                        vertical_spacing=0.06)

            r=1
            for n in df.columns[1:]:
                if np.sum(df[n].sum()!=0)>0:
                    fig.add_trace(go.Bar(x=df['name'], y=df[n], name = n),
                                  row=r, col=1,)
                    r+=1

            fig.update_layout(height=200*numOfPlots)
            fig.write_html("static/reviewlizer/reviewlizerResult.html")
            with open('static/reviewlizer/reviewlizerResult.html', 'r') as file:
                data = file.read()
            data = data.replace('<table border="1" class="dataframe">', '<meta http-Equiv="Cache-Control" Content="no-cache" /> <meta http-Equiv="Pragma" Content="no-cache" /> <meta http-Equiv="Expires" Content="0" /> <table class="table">')
            data = data.replace("style=\"text-align: right;\"", "style=\"text-align: left;\"")
            data = '<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.0-beta2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-BmbxuPwQa2lc/FVzBcNJ7UAyJxM6wuqIj61tLrc4wSX0szH/Ev+nYRRuWlolflfl" crossorigin="anonymous">\n' + data
            # with open("InstaSeerDf2.html", "w") as file:
            #      file.write("<link href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.0.0-beta2/dist/css/bootstrap.min.css\" rel=\"stylesheet\" integrity=\"sha384-BmbxuPwQa2lc/FVzBcNJ7UAyJxM6wuqIj61tLrc4wSX0szH/Ev+nYRRuWlolflfl\" crossorigin=\"anonymous\">")
            with open("static/reviewlizer/reviewlizerResult.html", "w") as file:
                file.write(data)


        #Histograms
        px.histogram(df2[df2['mean']!=0],x='mean', facet_col='keyword', facet_row='name', labels={'mean':'mean score'}).write_html("static/reviewlizer/reviewlizerHistograms.html")


        thresholdPvalue = 0.1
#df5 = pd.DataFrame()
        # c = 0
        dct2 = {'name_pair':[],
        'keyword':[],
        'result':[],
        'pvalue':[],
        'score1':[],
        'score2':[]}
        for k in df2['keyword'].unique():
        #     c+=1
            pvalues = []
            for n1 in df2['name'].unique():
                pv = []
                for n2 in df2['name'].unique():
                    a = df2[(df2['name']==n1) & (df2['keyword']==k)]['mean']
                    b = df2[(df2['name']==n2) & (df2['keyword']==k)]['mean']
                    pv.append(ttest_ind(a,b,equal_var=False).pvalue)
                    if n1!=n2:
                        dct2['name_pair'].append(tuple(np.sort([n1,n2])))
                        dct2['pvalue'].append(ttest_ind(a,b, equal_var=False).pvalue)
                        dct2['keyword'].append(k)
                        dct2['score1'].append(np.mean(df2[(df2['name']==n1) & (df2['keyword']==k)]['mean']))
                        dct2['score2'].append(np.mean(df2[(df2['name']==n2) & (df2['keyword']==k)]['mean']))
                        if np.mean(df2[(df2['name']==n1) & (df2['keyword']==k)]['mean'])>np.mean(df2[(df2['name']==n2) & (df2['keyword']==k)]['mean']):
                            dct2['result'].append(f'{n1} is better than {n2}')
                        else:
                            dct2['result'].append(f'{n2} is better than {n1}')
                pvalues.append(pv)
        # print(df7)
        # input()
        df7=pd.DataFrame(dct2)
        df8 = pd.DataFrame()
        for k in df7['keyword'].unique():
            df8 = pd.concat([df8,df7[df7['keyword']==k].drop_duplicates(subset='name_pair')])
        df8 = df8.sort_values(by='pvalue')
        df8 = df8[df8['pvalue']<0.3]
        df8 = df8.iloc[:,1:]
        df8.to_html('static/reviewlizer/reviewlizerPvalues.html', index=False)

        with open('static/reviewlizer/reviewlizerPvalues.html', 'r') as file:
            data = file.read()
        data = data.replace('<table border="1" class="dataframe">', '<meta http-Equiv="Cache-Control" Content="no-cache" /> <meta http-Equiv="Pragma" Content="no-cache" /> <meta http-Equiv="Expires" Content="0" /> <table class="table">')
        data = data.replace("style=\"text-align: right;\"", "style=\"text-align: left;\"")
        data = '<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.0-beta2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-BmbxuPwQa2lc/FVzBcNJ7UAyJxM6wuqIj61tLrc4wSX0szH/Ev+nYRRuWlolflfl" crossorigin="anonymous">\n' + data
        # with open("InstaSeerDf2.html", "w") as file:
        #      file.write("<link href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.0.0-beta2/dist/css/bootstrap.min.css\" rel=\"stylesheet\" integrity=\"sha384-BmbxuPwQa2lc/FVzBcNJ7UAyJxM6wuqIj61tLrc4wSX0szH/Ev+nYRRuWlolflfl\" crossorigin=\"anonymous\">")
        with open("static/reviewlizer/reviewlizerPvalues.html", "w") as file:
            file.write(data)



    #pd.set_option('display.max_colwidth', 60)
        f = px.box(df2, y='mean', facet_row='keyword', x='name', color='keyword')
        f.update_layout(height=150*len(df2['keyword'].unique()))
        f.write_html("static/reviewlizer/reviewlizerBoxPlots.html")

    dfIm2 = df.copy()
    images = []
    for i in dfIm2['name']:
        gis = GoogleImagesSearch(api_key, cx)
        _search_params = {
            'q': i,
            'num': 1
        }
        try:
            gis.search(search_params=_search_params)
            images.append(gis.results()[0].url)
        except:
            images.append("https://upload.wikimedia.org/wikipedia/commons/1/14/No_Image_Available.jpg")
    dfIm2 = dfIm2.reset_index()
    dfIm2 = dfIm2.drop(columns='index')
    # your images
    colOrder = ['image']+list(dfIm2.columns)
    dfIm2['image'] = images

    # convert your links to html tags
    def path_to_image_html(path):
        return '<img src="'+ path + '" width="200" >'

    pd.set_option('display.max_colwidth', None)
    dfIm2 = dfIm2[colOrder]
    #HTML(dfIm2.style.hide_index().set_properties(**{'font-size': '11pt','background-color': '#edeeef','border-color': 'black','border-style' :'solid' ,'border-width': '0px','border-collapse':'collapse'}).render())
    dfIm2.to_html('static/reviewlizer/reviewlizerDf.html', escape=False ,formatters=dict(image=path_to_image_html))
    #df.to_html('static/reviewlizerDf.html', index=False, border = 0)
    with open('static/reviewlizer/reviewlizerDf.html', 'r') as file:
        data = file.read()
    data = data.replace('<table border="1" class="dataframe">', '<meta http-Equiv="Cache-Control" Content="no-cache" /> <meta http-Equiv="Pragma" Content="no-cache" /> <meta http-Equiv="Expires" Content="0" /> <table class="table">')
    data = data.replace("style=\"text-align: right;\"", "style=\"text-align: left;\"")
    data = '<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.0-beta2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-BmbxuPwQa2lc/FVzBcNJ7UAyJxM6wuqIj61tLrc4wSX0szH/Ev+nYRRuWlolflfl" crossorigin="anonymous">\n' + data
    # with open("InstaSeerDf2.html", "w") as file:
    #      file.write("<link href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.0.0-beta2/dist/css/bootstrap.min.css\" rel=\"stylesheet\" integrity=\"sha384-BmbxuPwQa2lc/FVzBcNJ7UAyJxM6wuqIj61tLrc4wSX0szH/Ev+nYRRuWlolflfl\" crossorigin=\"anonymous\">")
    with open("static/reviewlizer/reviewlizerDf.html", "w") as file:
        file.write(data)
    return df
