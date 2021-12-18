import requests
import json
from urllib.parse import urlencode

DEFAULT_URL = "https://www.plentymarkets.co.uk/rest/"


class PlentyMarketRestClient():

    def __init__(self, api_url=DEFAULT_URL):
        self._access_token = ""
        self._refresh_token = ""
        self._url = api_url
        self._headers = {}
        self._last_request_status_code = 200
        self._last_request_content = None
        self._token_expiration = 0

    def setHeader(self, header):
        self._headers.update(header)

    def getHeaders(self):
        return self._headers

    def getLastRequestContent(self):
        return self._last_request_content

    def setLastRequestContent(self, content):
        self._last_request_content = content

    def setLastStatusCode(self, status_code):
        """
        Sets last response's status code. (Usually called by decorator _safeQuery)
        """
        self._last_request_status_code = status_code

    def login(self, email, password, id=0):
        """
        Logins to plentymarket using email and password.
        Posts requests to login API endpoint.

        :param str email: plentymarkets email
        :param str password: plentymarkets password
        :return: Returns response
        :rtype: Response Object
        """
        data = {
            "email": email,
            "password": password,
            "id": id
        }
        url = self._url + "account/login"
        response = requests.post(url, json=data)

        self.setLastStatusCode(response.status_code)

        data = json.loads(response.text)

        if "accessToken" in data and "refreshToken" in data:
            access_token = data["accessToken"]
            self._refresh_token = data["refreshToken"]
            self.setHeader({'Authorization': 'Bearer ' + access_token})
            print("Logged in successfully!")
        else:
            print("Error: Could not login. invalid credentials or API endpoint")

        return response

    def refreshLogin(self):
        """
        NOTE: Incomplete method and may not work properly!
        Refresh login using refresh token.

        :return: Returns response
        :rtype: Response Object
        """
        url = self._url + "account/login/refresh"
        response = requests.post(url, headers=self._headers)

        data = json.loads(response.text)
        if "refreshToken" in data:
            self._refresh_token = data["refreshToken"]
        return response

    def _safeQuery(func):
        """
        Decorator: Checks for valid request and response.
        :param function func: function to apply the decorator to
        :return: Returns wrapper function.
        :rtype: function
        """
        def wrapper(*args, **kwargs):
            self = args[0]
            if self._last_request_status_code == 200:
                try:
                    response = func(*args, **kwargs)
                    self.setLastStatusCode(response.status_code)

                    if response.status_code == 401:
                        print("Unauthorized: expired or invalid access token.")
                        self.safeQuery(self, func)

                    elif response.status_code == 200:
                        self.setLastRequestContent(response.content)

                    elif response.status_code == 404:
                        raise("HTTP 404 Error, unvalid API endpoint")

                    return response

                except Exception as e:
                    print("Error: " + str(e))

            elif self._last_request_status_code == 401:
                try:
                    print("Refreshing access token..")
                    self.refreshLogin()
                    response = func(*args, **kwargs)

                    if response.status_code == 200:
                        self.setLastRequestContent(response.content)

                    self.setLastStatusCode(response.status_code)
                    return response
                except Exception as e:
                    print("Error: " + str(e))

        return wrapper

    @_safeQuery
    def post(self, api_endpoint, data={}):
        """
        Executes POST request to plentymarket API endpoint
        :param str api_endpoint: API endpoint (e.g: payment/properties/types/names)
        :param dict data: required data to execute request
        :return: Returns HTTP response
        :rtype: Response Object
        """
        return requests.post(self._url + api_endpoint, data=data, headers=self._headers)

    @_safeQuery
    def delete(self, api_endpoint):
        """
        Executes DELETE request to plentymarket API endpoint
        :param str api_endpoint: API endpoint (e.g: /rest/languages/translations/{translationId})
        :return: Returns HTTP response
        :rtype: Response Object
        """
        return requests.delete(self._url + api_endpoint)

    @_safeQuery
    def get(self, api_endpoint, data={}):
        """
        Executes GET request to plentymarket API endpoint
        :param str api_endpoint: API endpoint (e.g: pim/attributes)
        :param dict data: required data to execute request
        :return: Returns HTTP response
        :rtype: Response Object
        """
        query = urlencode(data)
        if api_endpoint[:-1] != "?":
            query = "?" + query
        url = self._url + api_endpoint + query
        return requests.get(url, headers=self._headers)

    @_safeQuery
    def put(self, api_endpoint, data={}):
        """
        Executes PUT request to plentymarket API endpoint
        :param str api_endpoint: API endpoint (e.g: plugin_sets/{setId}/plugins/{pluginId})
        :param dict data: required data to execute request
        :return: Returns HTTP response
        :rtype: Response Object
        """
        return requests.put(self._url + api_endpoint, data=data)
