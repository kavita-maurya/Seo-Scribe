from flask import Flask, render_template, request, jsonify, make_response
import openai
import os
import textstat
import math
import requests
import json
from six.moves import urllib
from geopy.geocoders import Nominatim
import pycountry
import seo_score

app = Flask(__name__)
openai.api_key = "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"
seoApiKey = 'a9c5a917-d645-470a-96b0-8f2436ed2078'
geolocator = Nominatim(user_agent="Geolocation")


@app.route('/')
def index():
    return 'Hello, World!'


def bucketize(value):
    if (value <= 20):
        return "0-20"
    elif (value <= 40):
        return "21-40"
    elif (value <= 60):
        return "41-60"
    elif (value <= 80):
        return "61-80"
    else:
        return "81-100"


def find_backlinks_using_seo_review_api(inputUrl, numOfLinks):
    response = {}
    if (numOfLinks > 0):
        toolRequestUrl = 'https://api.seopowersuite.com/backlinks/v1.0/get-backlinks?apikey='+seoApiKey+'&target='+inputUrl+'&mode=url&limit='+str(min(10000,numOfLinks))+'&order_by=inlink_rank&output=json'
        print(toolRequestUrl)
        r = requests.get(toolRequestUrl).json()['backlinks']
        total_size = 0
        bucket_map = {'0-20':0,'21-40':0,'41-60':0,'61-80':0,'81-100':0}
        
        ls = []
        for data in r:
            total_size = total_size + 1
            bucket = bucketize(data["domain_inlink_rank"])
            bucket_map[bucket] += 1
            app_data = {
                "url": urllib.parse.unquote_plus(data["url_from"]),
                "last_visited": data["last_visited"],
                "page_authority": data["inlink_rank"],
                "domain_authority": data["domain_inlink_rank"],
            }
            ls.append(app_data)

    bucket_map['0-20'] =  math.ceil((bucket_map['0-20']/total_size) * 100)
    bucket_map['21-40'] =  math.ceil((bucket_map['21-40']/total_size) * 100)
    bucket_map['41-60'] =  math.ceil((bucket_map['41-60']/total_size) * 100)
    bucket_map['61-80'] =  math.ceil((bucket_map['61-80']/total_size) * 100)
    bucket_map['81-100'] =  math.ceil((bucket_map['81-100']/total_size) * 100)


    response['urls'] = ls
    response['bucket_map'] = bucket_map
    return response


def find_domain_authority_using_seo_review_api(inputUrl):
    # API URL
    toolRequestUrl = 'https://api.seopowersuite.com/backlinks/v1.0/get-summary?apikey='+seoApiKey+'&target='+inputUrl+'&mode=url&output=json'
    r = requests.get(toolRequestUrl).json()

    countries = r['summary'][0]["top_countries"]
    for country in countries:
        code = country['country']
        location = geolocator.geocode(code)
        country['code'] = code.upper()
        country['country'] = pycountry.countries.get(alpha_2=code).name
        country['lat'] = location.latitude
        country['lon'] = location.longitude


    response = {
        "backlinks": r['summary'][0]["backlinks"],
        "page_authority": r['summary'][0]["inlink_rank"],
        "domain_authority": r['summary'][0]["domain_inlink_rank"],
        "top_countries": countries
    }
    return response


def build_cors_preflight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add('Access-Control-Allow-Headers', "*")
    response.headers.add('Access-Control-Allow-Methods', "*")
    return response


def corsify_actual_response(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response    


@app.route('/analyzeDomainUrl', methods=["POST", "OPTIONS"])
def analyze_domain_url():
    
    if request.method == "OPTIONS": # CORS preflight
        return build_cors_preflight_response()


    text = request.json['text']
    print(text)

    authority = find_domain_authority_using_seo_review_api(text)
    backlinks = find_backlinks_using_seo_review_api(text, authority['backlinks'])
    

    data = jsonify(
        authority=authority,
        backlinks=backlinks
    )

    return corsify_actual_response(data)    


def analyze_keywords(text):
    prompt = f'Analyze the keywords:\n\n{text}\n\nKeywords:'
    try:
        response = openai.Completion.create(
            engine='text-davinci-003',
            prompt=prompt,
            max_tokens=30,
            n=1,
            temperature=0.5,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
        )
        keywords = [x.strip() for x in response['choices'][0]['text'].strip().split(',')]

        # keeping keywords that are not blank
        filtered_keywords = [keyword for keyword in keywords if keyword]
        return keywords
    except Exception as e:
        print('OpenAI API request failed:', str(e))
        return None


def calculate_word_count(text):
    word_count = textstat.lexicon_count(text)
    return word_count


def calculate_readability_score(text):
    readability_score = textstat.flesch_reading_ease(text)
    return readability_score


def calculate_seo_score(text, keywords):
    toolRequestUrl = 'https://api.seoreviewtools.com/seo-content-analysis/?content=1&keyword='+str(keywords)+'&relatedkeywords='+str(keywords)+'&key='+seoApiKey
    #r = requests.post(url = toolRequestUrl, data = data)
    return seo_score.calculate_seo_score(text)


def calculate_quality_score(text):
    quality_score = textstat.text_standard(text)
    return quality_score


def analyze_quality(text):
    prompt = f'Analyze the overall quality of the blog post:\n\n{text}'
    try:
        response = openai.Completion.create(
            engine='text-davinci-003',
            prompt=prompt,
            max_tokens=200,
            temperature=0.5,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
        )
        quality_analysis = response.choices[0].text.strip()
        return quality_analysis
    except Exception as e:
        print('OpenAI API request failed:', str(e))
        return None


def give_suggestions(text):
    prompt = f'Give some top suggestions to enhance the blog post concisely:\n\n{text}'
    try:
        response = openai.Completion.create(
            engine='text-davinci-003',
            prompt=prompt,
            max_tokens=200,
            temperature=0.5,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
        )
        suggestions = [i for a,i in enumerate(response.choices[0].text.strip().split('\n')) if i!='']
        return suggestions
    except Exception as e:
        print('OpenAI API request failed:', str(e))
        return None  


def on_page_optimization_suggestion(text):
    prompt = f'Provide concise recommendations to optimize on-page elements such as meta tags, headings, URL structure, image tags, and internal linking for the given blog post:\n\n{text}'
    try:
        response = openai.Completion.create(
            engine='text-davinci-003',
            prompt=prompt,
            max_tokens=200,
            temperature=0.5,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
        )
        suggestions = [i for a,i in enumerate(response.choices[0].text.strip().split('\n')) if i!='']
        return suggestions
    except Exception as e:
        print('OpenAI API request failed:', str(e))
        return None        


def calculate_keyword_density(text, keywords):
    # Convert the text to lowercase for case-insensitive matching
    text = text.lower()

    # Calculate the total number of words in the text
    total_words = len(text.split())

    # Initialize a dictionary to store the frequency of each keyword
    keyword_frequency = {keyword: 0 for keyword in keywords}

    # Count the frequency of each keyword in the text
    for keyword in keywords:
        temp = keyword.lower()
        keyword_frequency[keyword] = text.count(temp)

    # Calculate the keyword density as a percentage
    keyword_density = {keyword: math.ceil((frequency / total_words) * 100) for keyword, frequency in
                       keyword_frequency.items()}

    return keyword_density


@app.route('/analyzeBlog', methods=["POST", "OPTIONS"])
def analyze_blog():
    
    if request.method == "OPTIONS": # CORS preflight
        return build_cors_preflight_response()


    text = request.json['text']
    print(text)

    keywords = analyze_keywords(text)
    if keywords is None:
        return jsonify(error='Failed to analyze keywords'), 500

    word_count = calculate_word_count(text)
    readability_score = calculate_readability_score(text)
    quality_score = calculate_quality_score(text)
    seo_score = calculate_seo_score(text, keywords)

    quality_analysis = analyze_quality(text)
    if quality_analysis is None:
        return jsonify(error='Failed to analyze overall quality'), 500

    keyword_density = calculate_keyword_density(text, keywords)
    
    suggestions = give_suggestions(text)
    if suggestions is None:
        return jsonify(error='Failed to give suggestions'), 500


    on_page_optimization_suggestions = on_page_optimization_suggestion(text)
    if on_page_optimization_suggestions is None:
        return jsonify(error='Failed to give on_page_optimization_suggestions'), 500

    data = jsonify(
        keywords=keywords,
        word_count=word_count,
        readability_score=readability_score,
        quality_analysis=quality_analysis,
        quality_score=quality_score,
        seo_score=seo_score,
        keyword_density=keyword_density,
        suggestions=suggestions,
        on_page_optimization_suggestions=on_page_optimization_suggestions
    )
    return corsify_actual_response(data)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)