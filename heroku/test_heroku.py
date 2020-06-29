# app/weather_service.py
import os
from dotenv import load_dotenv
import spotipy
import sys
from spotipy.oauth2 import SpotifyClientCredentials
import utils as util
import datetime
load_dotenv()


#
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")
username = os.getenv("username")
scope = 'user-library-read playlist-modify-public'
#
util.prompt_for_user_token(username,
                           scope,
                           SPOTIPY_CLIENT_ID,
                           SPOTIPY_CLIENT_SECRET,
                           SPOTIPY_REDIRECT_URI)

token = util.prompt_for_user_token(username, scope)

def podcast_playlist_generator(username, token):
    sp = spotipy.Spotify(auth=token) #calls spotipy with authorized credentials
    results = sp.current_user_playlists(limit=50)
    for i, item in enumerate(results['items']):
        if i or item["name"] != "Favorite Podcasts":
            sp.user_playlist_create(username, "Favorite Podcasts", public=True, description='Latest Episodes') #Consider branding app & playlist name
        else:
            break
#podcast_playlist_generator(username, token)
def user_playlist_add_episodes(
        sp, user, playlist_id, episodes, position=None
    ):
        """ Adds episodes to a playlist
            Parameters:
                - user - the id of the user
                - playlist_id - the id of the playlist
                - episodes - a list of track URIs, URLs or IDs
                - position - the position to add the tracks
        """
        plid = sp._get_id("playlist", playlist_id)
        ftracks = [sp._get_uri("episode", tid) for tid in episodes]
        return sp._post(
            "users/%s/playlists/%s/tracks" % (user, plid),
            payload=ftracks,
            position=position,
        )


sp = spotipy.Spotify(auth=token) #calls spotipy with authorized credentials
results = sp.current_user_playlists(limit=50)
for i, item in enumerate(results['items']):
    if i or item["name"] != "Favorite Podcasts":
        sp.user_playlist_create(username, "Favorite Podcasts", public=True, description='Latest Episodes') #Consider branding app & playlist name
    else:
        break
sp = spotipy.Spotify(auth=token)
results = sp.current_user_saved_shows()
items = results["items"]
ID_LIST = [p["show"]["id"] for p in items]
episodes = []
for x in ID_LIST:
    sodes = sp.show(x)
    episodes.append(sodes) 
show_items = [p["episodes"]["items"] for p in episodes]
recent_releases = [item[0] for item in show_items]
today = datetime.date.today()
yesterday = str(today - datetime.timedelta(days=1))
new_release = [b for b in recent_releases if str(b["release_date"]) == yesterday or today]
#print(new_release)
print(len(new_release))
if len(new_release) < 1:
    print("There are no new episodes to add")
else:
    recent_ep_uris = [sub['id'] for sub in new_release]
    playlists = sp.current_user_playlists()
    playlists_items = playlists['items']
    favorite_podcasts = [x for x in playlists_items if x['name'] == "Favorite Podcasts"]
    playlist = favorite_podcasts[0]
    user_playlist_add_episodes(sp, username, playlist['id'], recent_ep_uris, position=None)

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

load_dotenv()

# Send email using template function
def send_episode_email(username, token):
    load_dotenv()

    sp = spotipy.Spotify(auth=token)
    results = sp.current_user_saved_shows()
    items = results["items"]
    ID_LIST = [p["show"]["id"] for p in items]
    episodes = []
    for x in ID_LIST:
        sodes = sp.show(x)
        episodes.append(sodes) 
    show_items = [p["episodes"]["items"] for p in episodes]
    recent_releases = [item[0] for item in show_items]
    y = datetime.datetime.now()
    date_today = str(y.strftime("%Y-%m-%d"))
    today = datetime.date.today()
    yesterday = str(today - datetime.timedelta(days=1))
    new_release = [b for b in recent_releases if str(b["release_date"]) == yesterday or date_today]
    if len(new_release) > 0:
        recent_ep_uris = [sub['uri'] for sub in new_release] 
        new_episodes = []
        for x in recent_ep_uris:
            sodes = sp.episode(x)
            new_episodes.append(sodes)
        episode_details = [{
            "show": q['show']["name"],
            "name": q['name']}
            for q in new_episodes
        ]
    else:
        episode_details = {
            "show": "No new episodes have been added",
            "name": ""
        }

    #template_data = {
    #                    "episode_info":[
    #                    {"show": "Test Show" ,"name": "Test Episode"},
    #                    {"show": "Try 2", "name": "Tester"}
    #                    ]
    #                }
    template_data = {"episode_info": episode_details}
 
    # Building the ability to send the email
    client = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
    
    message = Mail(from_email=os.environ.get("MY_EMAIL"),to_emails=os.environ.get("TO_EMAIL"))
     
    message.template_id = os.environ.get("SENDGRID_TEMPLATE_ID")

    message.dynamic_template_data = template_data    
    
    try:
        response = client.send(message)
        print("RESPONSE: ", type(response))
        print(response.status_code) # if 202 prints then SUCCESS
        print(response.body)
        print(response.headers)
        return response
    except Exception as e:
        print(e)
        return None


send_episode_email(username, token)