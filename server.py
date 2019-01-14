from flask import Flask
from flask import session, redirect, url_for, render_template, Response, request
import json
import requests
from urllib.parse import urlencode, quote_plus


CLIENT_ID = "CHANGE ME"
SECRET_KEY = "CHANGE ME"
FLASK_SESSION_KEY = "CHANGE ME"
MY_ADDRESS =  "http://merchant.authsaz.com:5000"
REDIRECT_URL = MY_ADDRESS + "/callback"
API_CALLBACK_URL = MY_ADDRESS + "/apicallback"


SERVER_NAME_API = 				"https://api-gateway.authsaz.com:444"

# More information is available at:
#       https://www.ibm.com/support/knowledgecenter/SSPREK_9.0.5/com.ibm.isam.doc/config/concept/OAuthEndpoints.html#oauthendpoints
SERVER_NAME_OAUTH_AUTHORIZE = 	"https://api-gateway.authsaz.com/mga/sps/oauth/oauth20/authorize"
SERVER_NAME_OAUTH_TOKEN = 		"https://api-gateway.authsaz.com/mga/sps/oauth/oauth20/token"
SERVER_NAME_OAUTH_INTROSPECT = 	"https://api-gateway.authsaz.com/mga/sps/oauth/oauth20/introspect"
SERVER_NAME_OAUTH_USERINFO = 	"https://api-gateway.authsaz.com/mga/sps/oauth/oauth20/userinfo"
SERVER_NAME_OAUTH_REVOKE = 		"https://api-gateway.authsaz.com/mga/sps/oauth/oauth20/revoke"
SERVER_NAME_OAUTH_LOGOUT = 		"https://api-gateway.authsaz.com/mga/sps/oauth/oauth20/logout"

SERVER_VERIFY = SERVER_NAME_API + "/mga"

app = Flask(__name__, static_url_path="/static")
app.config.update(
    SECRET_KEY=FLASK_SESSION_KEY
)
# Only for debugging
#
# proxies = {"http": "http://192.168.0.1:8080",
#           "https": "http://192.168.0.1:8080"}
proxies = None

def flat_multi(multidict):
    flat = {}
    for key, values in multidict.items():
        flat[key] = values[0] if type(values) == list and len(values) == 1 \
                    else values
    return flat

@app.route('/', methods=['GET'])
def index_page():
    params = {
      "scope": "financial non-financial",
      "redirect_uri":REDIRECT_URL,
      "response_type": "code",
      "state":"123",
      "client_id":CLIENT_ID
    }
    oauth_url = SERVER_NAME_OAUTH_AUTHORIZE + "?" +urlencode(params)
    return render_template("index.html", oauth_url = oauth_url)

@app.route('/logout', methods=['GET','POST'])
def logout():
    if "access_token" in session:
       header = {
          "Content-type": "application/x-www-form-urlencoded;charset=UTF-8",
          'Authorization': 'Bearer ' + session["access_token"]
       }
       r = requests.post(SERVER_NAME_OAUTH_LOGOUT, headers = header,proxies=proxies, verify=False)
       session.clear()
       return "1"
    else:
       return "0"


@app.route('/callback', methods=['GET','POST'])
def oauth_callback():
    params = flat_multi(request.values)
    if "code" in params:
       code = params["code"]
       header = {
          "Content-type": "application/x-www-form-urlencoded;charset=UTF-8"
       }
       data = {
          "client_id": CLIENT_ID,
          "client_secret": SECRET_KEY,
          "redirect_uri": REDIRECT_URL,
          "code": code,
          "grant_type": "authorization_code"
       }
       r = requests.post(SERVER_NAME_OAUTH_TOKEN, headers = header, proxies=proxies, data=data, verify=False)
       js = r.json()
       if "access_token" in js:
           session["access_token"] = js["access_token"]
           session["refresh_token"] = js["refresh_token"]
           session["token_type"] = js["token_type"]
           session["expires_in"] = js["expires_in"]
           session["scope"] = js["scope"]
           return render_template("close_popup.html")
       else:
           return "failed" + json.dumps(js)
    else:
       return "ERROR"

@app.route('/apicallback', methods=['GET', 'POST'])	   
def api_callback():
    params = flat_multi(request.values)
    if "response" in params and "last_action" in session:
       headers = { 
                'Authorization': 'Bearer ' + session["access_token"]
              }
       data = {
            "operation": "verify",
            "response": params["response"]
       }
       r = requests.post(SERVER_VERIFY + session['last_action'], data=data, headers=headers, verify=False, proxies=proxies, allow_redirects=True)
       web_result = r.json()
       return render_template("api_popup_close.html", web_result = json.dumps(web_result) )
    return render_template("api_popup_close.html")
	   
@app.route('/me', methods=['POST','GET'])
def do_introspect():
    if "access_token" in session:
       header = {
          "Accept": "application/json"
       }
       data = {
          "client_id": CLIENT_ID,
          "client_secret": SECRET_KEY,
          "token": session["access_token"]
       }
       r = requests.post(SERVER_NAME_OAUTH_INTROSPECT, data=data, proxies=proxies, headers = header, verify=False)
       return r.text
    else:
       return Response(json.dumps({"error": "not logged in"}), content_type='appication/json') , 401

@app.route('/refresh_token', methods=['POST','GET'])
def do_refresh_token():
    if "access_token" in session:
       header = {
          "Accept": "application/json"
       }
       data = {
          "client_id": CLIENT_ID,
          "client_secret": SECRET_KEY,
          "refresh_token": session["refresh_token"],
          "grant_type": "refresh_token"
       }

       r = requests.post(SERVER_NAME_OAUTH_TOKEN, data=data, headers = header, verify=False, proxies=proxies)
       js = r.json() 
       if "access_token" in js:
           session["access_token"] = js["access_token"]
           session["refresh_token"] = js["refresh_token"]
           session["token_type"] = js["token_type"]
           session["expires_in"] = js["expires_in"]
           session["scope"] = js["scope"]
           return Response(json.dumps({"status": "1"}), content_type='appication/json')
       else:
           return Response(json.dumps({"status": "0"}), content_type='appication/json')
    else:
       return Response(json.dumps({"error": "not logged in"}), content_type='appication/json') , 401

@app.route('/balance', methods=['POST'])
def do_balance():
    if "access_token" in session:
       params = flat_multi(request.values)
       headers = { 'Content-type': 'application/json',
                'Accept': 'appication/json',
                'Authorization': 'Bearer ' + session["access_token"]
              }
       data = {
               'account': params['acc_balance']
           }
       r = requests.post(SERVER_NAME_API + '/api/nf/balance', data=json.dumps(data), headers=headers, verify=False, proxies=proxies, allow_redirects=False)
       if r.status_code == 302:
            return do_auth(r)
       else:
            web_result = r.json()
            return Response(json.dumps(web_result), content_type='appication/json')
    else:
       return Response(json.dumps({"error": "not logged in"}), content_type='appication/json') , 401

@app.route('/get_accounts', methods=['POST'])
def do_get_accounts():
    if "access_token" in session:
       params = flat_multi(request.values)
       headers = { 'Content-type': 'application/json',
                'Accept': 'appication/json',
                'Authorization': 'Bearer ' + session["access_token"]
              }
       data = {
               'username': params['username']
           }
       r = requests.post(SERVER_NAME_API + '/api/nf/accounts', data=json.dumps(data), headers=headers, verify=False, proxies=proxies, allow_redirects=False)
       if r.status_code == 302:
            return do_auth(r)
       else:
            web_result = r.json()
            return Response(json.dumps(web_result), content_type='appication/json')
    else:
       return Response(json.dumps({"error": "not logged in"}), content_type='appication/json') , 401
       
       
def do_auth(req):
    headers = { 
            'Authorization': 'Bearer ' + session["access_token"]
          }
    r =requests.get(SERVER_NAME_API + req.headers['location'], headers=headers, verify=False, proxies=proxies, allow_redirects=False)
    web_result = r.json()
    if "challenge" in web_result:
        session["last_action"] = web_result["action"]
        web_result = {
            "status": "auth-need", 
            "url": SERVER_VERIFY + "/sps/authsvc?PolicyId={policy}&challenge={challenge}&callback={target}", 
            "policy": web_result['policy_id'], 
            "target": API_CALLBACK_URL, 
            "challenge": web_result["challenge"]
         }
        return Response(json.dumps(web_result), content_type='appication/json')
    else:
        return Response(json.dumps({"error": "challenge not found"}), content_type='appication/json') , 578

@app.route('/transfer', methods=['POST'])
def do_transfer():
    if "access_token" in session:
       params = flat_multi(request.values)
       headers = { 'Content-type': 'application/json', 
                'Accept': 'appication/json',
                'Authorization': 'Bearer ' + session["access_token"]
              }
       data = {
               'account2': params['acc_to'],
               'account': params['acc_from'],
               'amount': params['amount']
           }
       r = requests.post(SERVER_NAME_API + '/api/f/transfer', headers=headers, data=json.dumps(data), proxies=proxies, verify=False, allow_redirects=False)
       if r.status_code == 302:
            return do_auth(r)
       else:
            web_result = r.json()
            return Response(json.dumps(web_result), content_type='appication/json')
    else:
       return Response(json.dumps({"error": "not logged in"}), content_type='appication/json') , 401

run = {
    "debug": True,
    "port": 5000,
    "host": '0.0.0.0',
    "threaded": True
}

if __name__== "__main__":
   app.run(debug=run["debug"], threaded=run["threaded"], host=run["host"], port=run["port"])
