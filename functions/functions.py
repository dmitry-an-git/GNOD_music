import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from config import *
import pandas as pd
import numpy as np
import re
from time import sleep
from random import randint
import pickle

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id= Client_ID,
                                                           client_secret= Client_Secret))

data = pd.read_csv('data/all_songs.csv')


def dash(df):

    columns = df.columns.to_list()
    
    for i in columns:

        df[i] = df[i].str.replace(b'\xe2\x80\x90'.decode('utf-8'), '-')
        df[i] = df[i].str.replace(b'\xe2\x80\x91'.decode('utf-8'), '-')
        df[i] = df[i].str.replace(b'\xe2\x80\x92'.decode('utf-8'), '-')
        df[i] = df[i].str.replace(b'\xe2\x80\x93'.decode('utf-8'), '-')
        df[i] = df[i].str.replace(b'\xe2\x80\x94'.decode('utf-8'), '-')
        df[i] = df[i].str.replace(b'\xe2\x80\x94'.decode('utf-8'), '-')
        df[i] = df[i].str.replace('\xa0', ' ') #nbs


        

    return df


def clean(df):

    columns = df.columns.to_list()
    
    for i in columns:

        df[i] = df[i].str.replace('"',"")
        df[i] = df[i].str.replace(r'\[[\w. \$\&\’\'\-\,]*\]',"")
        df[i] = df[i].str.replace(r'\([\w. \$\&\’\'\-\,]*\)',"")
        df[i] = df[i].str.replace('“','')
        df[i] = df[i].str.replace('”','')
        df[i] = df[i].str.replace('’','')
        df[i] = df[i].str.replace('&','')
        df[i] = df[i].str.replace('!','')
        df[i] = df[i].str.replace('—',' ')
        df[i] = df[i].str.replace('\'',' ')
        df[i] = df[i].str.replace(r'"$',' ')       
        df[i] = df[i].str.replace(r'ft.[\w. \$\&\’\'\-\,]*',' ')
        df[i] = df[i].str.replace(r'feat.[\w. \$\&\’\'\-\,]*',' ')
        df[i] = df[i].str.replace(r'\/[\w. \$\&\’\'\-\,]*',' ')
#        df[i] = df[i].str.replace(r'\[[\w. \$\&\’\'\-\,]*\]',"")
        df[i] = df[i].str.replace('\n','')
    
        
    return df 


def input_validation():
    input_finished = False
    while input_finished == False:
        song = input('Pls input the song:')
        artist = input('Pls input the artist:')
        print("You are looking for {} by {}".format(song,artist))
        accept = input('Press \'Y\' if true, press any other key to repeat input:')
        if accept in ['Y','y']:
            print('Ok, the input is accepted.')
            input_finished = True
        else:
            print('Ok, please repeat the input.')
            input_finished = False
    return song, artist


def search_song(song,artist):
    
        print('Querying songs...')
        
        artists = []
        songs   = []
        years   = []
        index   = []
        id      = []
        
        results = sp.search(q='track:{} artist:{}'.format(song,artist), limit=5)
        num     = len(results['tracks']['items'])
        
        if num > 0:
            for i in range (0,num):
                artists.append(results['tracks']['items'][i]['name'])
                songs.append(results['tracks']['items'][i]['artists'][0]['name'])
                years.append(results['tracks']['items'][i]['album']['release_date'])
                index.append(i+1)
                id.append(results['tracks']['items'][i]['id'])
            selection_df = pd.DataFrame({'artist':artists, 'name':songs, 'release':years, 'id':id})
            selection_df.index = index
            a = True
            print ('The following is found: ')
            return a, selection_df
        elif num == 0:
            print ('Nothing is found! ')
            selection_df = pd.DataFrame({'artist':artists, 'name':songs, 'release':years, 'id':id})
            a = False
            return a, selection_df


def get_audio_features(list_of_songs):
    
    print('Querying audio features...')
    
    dic = {}
    for key in sp.audio_features('4yzUTT6pCLKlaWlNwe4XM8')[0].keys():
        dic[key]=[]
       
    steps=[j for j in range(50,len([list_of_songs]),50)]
    
    for n,i in enumerate([list_of_songs]):
        if i != '': ## some songs have not ids
                a = sp.audio_features(i)
                if a != [None]: ## some songs have id but not audio features
                    for key in a[0].keys():
                        dic[key].append(a[0][key])
                else:
                    for key in dic.keys():
                        dic[key].append('')
        else:
            for key in dic.keys():
                dic[key].append('')
        if n in steps:
            seconds_to_wait = randint(1,10)
            print("Waiting {} seconds before querying next 50 songs!(n={})".format(seconds_to_wait,n))
            sleep(seconds_to_wait)
            
    
    df = pd.DataFrame(dic)    
    
    print('Querying audio features... Done')
    
    return df



def load(filename = "filename.pickle"): 
    try: 
        with open(filename, "rb") as file: 
            return pickle.load(file) 
    except FileNotFoundError: 
        print("File not found!") 
    

def cluster_predictor(df):
    
    scaler = load("models/scaler.pickle")
    best_model = load("models/kmeans_14.pickle")
    
    audio_features = ['danceability', 'energy', 
       'mode', 'speechiness', 'acousticness', 'instrumentalness', 
       'tempo','time_signature','key', 'liveness','loudness','valence', ]
    
    audio_features_final = ['danceability', 'mode',
       'tempo','time_signature','key', 'liveness','loudness' ]
    
    
    X = df[audio_features]
    X_scaled = scaler.transform(X)
    X_scaled_df = pd.DataFrame(X_scaled, columns = X.columns)
    
    cluster = best_model.predict(X_scaled_df[audio_features_final])
    
    print('The cluster is {}.'.format(cluster[0]))
    
    return cluster[0]


def advice(cluster,hot):
    df = data[(data['cluster']==cluster)&(data['hot']==hot)].sample(1)
    
    print('The recommended song is \'{}\' by {}, {}.'.format(df['song'].values[0],df['singer'].values[0],df['url'].values[0]))
 
    return


def music_recommender():
    search = True
    while search == True:
        
        song,artist = input_validation()
        a,db = search_song(song,artist)
        
        if a == False:
            print('Please provide the inputs again')
            continue
        else:
            display(db[['artist','name','release']])
        
        x = int(input('Please select the right song: '))
        id_search = db['id'].loc[x]
        
        if id_search in data['id'].values:
            print ("the song is in the list")
            hot = data[data['id']==id_search]['hot'].values[0]
            print ("is it hot: {}".format(hot))
            
        else: 
            print('not in the db')
            hot = False
        
        db_af = get_audio_features(id_search)
        
        cluster = cluster_predictor(db_af)
        
        advice(cluster,hot)
   
        cont = input('Press Q if you want to exit, any other key if you want to continue from the start: ')
        if cont in ['q','Q']:
            print('Bye!')
            break
        else:
            print('Lets do it again!')
            continue
