from django.shortcuts import render
from . import pgn, reviewAnalyzer, charwords, googleCreds, instaSeer
from .miluogo import score, models, updateMap
def home(request):
    return render(request, 'index.html')

def aboutit(request):
    return render(request, 'aboutit2.html')


def cell1(request):
    input_lastname = request.GET.get('lastname', 'Adams')

    pgn.getGraph(input_lastname)
    return render(request, 'pgn.html', {'given_lastname':input_lastname})

def cell6(request):
    return render(request, 'moviePosters.html')
def cell7(request):
    return render(request, 'instaSeer.html')
def cell8(request):
    return render(request, 'airfoils.html')
def cell9(request):
    return render(request, 'about.html')

def cell4(request):
    return render(request, 'fakeNews.html')

def cell5(request):
    return render(request, 'sales.html')

lastJobName = 'Data Scientist'
last_price_importance, last_work_importance, last_danger_importance, last_air_importance, last_green_importance = 2.5, 2.5, 2.5, 2.5, 2.5
def cell2(request):
    global lastJobName
    global last_price_importance, last_work_importance, last_danger_importance, last_air_importance, last_green_importance
    input_jobName = request.GET.get('jobName', 'Data Scientist')
    price_importance = request.GET.get('price_importance', 2.5)
    work_importance = request.GET.get('work_importance', 2.5)
    danger_importance = request.GET.get('danger_importance', 2.5)
    air_importance = request.GET.get('air_importance', 2.5)
    green_importance = request.GET.get('green_importance', 2.5)

    if (input_jobName!=lastJobName) or ([last_price_importance, last_work_importance, last_danger_importance, last_air_importance, last_green_importance]!=[price_importance, work_importance, danger_importance, air_importance, green_importance]):
        #price_importance, work_importance, danger_importance, air_importance, green_importance = 5,5,5,5,5
        score.score(input_jobName,price_importance, work_importance, danger_importance, air_importance, green_importance)
        updateMap.updateMap()
        lastJobName = input_jobName
        last_price_importance, last_work_importance, last_danger_importance, last_air_importance, last_green_importance = price_importance, work_importance, danger_importance, air_importance, green_importance
    #getCompaniesDataframe(googleCreds.GOOGLE_API_KEY, jobName=job_name, dfPath="static/miluogo/1_dfCompanies.csv")
    #miluogo.updateMap(job_name, price_importance, work_importance, danger_importance, air_importance, green_importance)
    return render(request, 'miluogo.html',{'given_jobName':input_jobName, 'given_price_importance':price_importance, 'given_work_importance':work_importance, 'given_danger_importance':danger_importance,'given_air_importance':air_importance,'given_green_importance':green_importance})



lastProductNames = 'iPhone 11 Pro\niPhone 12 Pro\nGoogle Pixel 5\nGoogle Pixel 4A'
lastProductKeyWords = 'screen\ncamera\nstabilization\nbattery\nmaterials\nprice'



def cell3(request):
    global lastProductNames
    global lastProductKeyWords
    input_productNames = request.GET.get('productNames', 'iPhone 11 Pro\niPhone 12 Pro\nGoogle Pixel 5\nGoogle Pixel 4A')
    input_productKeyWords = request.GET.get('productKeyWords', 'screen\ncamera\nstabilization\nbattery\nmaterials\nprice')

    if (input_productNames!=lastProductNames) or (input_productKeyWords!=lastProductKeyWords):
        reviewAnalyzer.getSetScoresText(input_productNames, input_productKeyWords, maxNumber=5, plot = True, api_key=googleCreds.GOOGLE_API_KEY2, cx = googleCreds.GOOGLE_CX)
        lastProductNames= input_productNames
        lastProductKeyWords = input_productKeyWords
    plotHeight1 = str(200*len(input_productNames.split('\n')))+'px'
    plotHeight2 = str(200*len(input_productKeyWords.split('\n')))+'px'
    return render(request, 'reviewlizer.html', {'given_productNames':input_productNames,'given_productKeyWords':input_productKeyWords,'plotHeight1':plotHeight1,'plotHeight2':plotHeight2})




lastImageUrls = 'https://s1.1zoom.ru/big3/11/Netherlands_Houses_478971.jpg\nhttps://timelapsenetwork.com/wp-content/uploads/TL-foto-Milano-City-5.jpg'
lastCaptionTexts = 'This is a beautiful picture of Nehtherlands #amsterdam #travel @user1 @user2\nThis is Milano #italy @user3'
def cell7(request):
    global lastImageUrls
    global lastCaptionTexts
    input_ImageUrls = request.GET.get('ImageUrls', 'https://s1.1zoom.ru/big3/11/Netherlands_Houses_478971.jpg\nhttps://timelapsenetwork.com/wp-content/uploads/TL-foto-Milano-City-5.jpg')
    input_CaptionTexts = request.GET.get('CaptionTexts', 'This is a beautiful picture of Nehtherlands #amsterdam #travel @user1 @user2\nThis is Milano #italy @user3')
    if (input_ImageUrls!=lastProductNames) or (input_CaptionTexts!=lastCaptionTexts):
        instaSeer.getScores(input_ImageUrls, input_CaptionTexts)
        lastImageUrls = input_ImageUrls
        lastCaptionTexts = input_CaptionTexts
    # plotHeight1 = str(200*len(input_productNames.split('\n')))+'px'
    # plotHeight2 = str(200*len(input_productKeyWords.split('\n')))+'px'
    return render(request, 'instaSeer.html', {'given_ImageUrls':input_ImageUrls,'given_CaptionTexts':input_CaptionTexts})
