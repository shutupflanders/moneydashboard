import requests
from requests.exceptions import HTTPError
import logging
import json
from decimal import Decimal

class MoneyDashboard():

    def __init__(self, session=None, email=None, password=None):
        self.__session = session
        self.__logger = logging.getLogger()

    def get_session(self):
        return self.__session

    def set_session(self, session):
        self.__session = session

    def login(self, email, password):
        self.__logger.info('Logging in...')
        """Login to Moneydashboard using the credentials provided in config"""
        url = "https://my.moneydashboard.com/landing/login"

        payload = {
            "OriginId": "1",
            "Email": email,
            "Password": password,
            "CampaignRef": "",
            "ApplicationRef": "",
            "UserRef": ""
        }
        headers = {
            "Authority": "my.moneydashboard.com",
            'Origin': 'https://my.moneydashboard.com',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) \
            Chrome/78.0.3904.70 Safari/537.36',
            'Content-Type': 'application/json;charset=UTF-8',
            'Accept': 'application/json, text/plain, */*',
            'X-Requested-With': 'XMLHttpRequest',
            '__requestverificationtoken': 'KXU5u0kZUP9xkqB4dttI43vaUBhtUGrwlW1Y6mqn_4rVAXsM8WdA\
            -XBLWbHuQeexS4m1zLKNsKfy1WCQyx2oPO20tik1',
            'Dnt': '1',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Referer': 'https://my.moneydashboard.com/landing',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8,it;q=0.7',
            'Cookie': 'hasUser=true; __RequestVerificationToken=AGq1bYzUaMxnUC3pAi2sVxfoS5Ea3Ujl6tn3\
            g2aoooYsx2s3g1KZTdci4da6wkHVL3liXI4g-kLlyoAn2p0vcB4lmM41; AWSALB=3kABtlACp8CGnHsB881VtHMYz\
            sQ6lJDCNMZSTod84LMWzx4FdC1Mc0vOVg8FnifGX1mn59meREwM3D/zPl78ZoQ4Q34v5O1lpHJ6bX95PH2UnsRBfKagE1neZnK4',
        }
        self.set_session(requests.session())
        try:
            response = self.get_session().request("POST", url, json=payload, headers=headers)
            response.raise_for_status()
        except HTTPError as http_err:
            self.__logger.error(f'[HTTP Error]: Failed to login ({http_err})')
            raise SystemExit
        except Exception as err:
            self.__logger.error(f'[Error]: Failed to login ({err})')
            raise SystemExit
        else:
            response_data = response.json()
            if response_data["IsSuccess"] is True:
                return response_data['IsSuccess']
            else:
                self.__logger.error(f'[Error]: Failed to login ({response_data["ErrorCode"]})')
                raise SystemExit


    def getAccounts(self):
        self.__logger.info('Getting Accounts...')
        """Retrieve account list from MoneyDashboard account"""
        url = "https://my.moneydashboard.com/api/Account/"

        headers = {
            "Authority": "my.moneydashboard.com",
            'Accept': 'application/json, text/plain, */*',
            "X-Newrelic-Id": "UA4AV1JTGwAJU1BaDgc=",
            'Dnt': '1',
            'X-Requested-With': 'XMLHttpRequest',
            '__requestverificationtoken': 'qY38K1qoy_1nrAHrOdHs-GW_nnjkDoN65ixTassq76TN4Kjuoi-DRz\
            Kx4AjHgStx9CL2gBOGZqEWAl9yBbYquHwFc7QUBT0NlbziXOcQV2kjfn7Xvtu1o71VlJXtpSLYiB8Yxg2',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) C\
            hrome/78.0.3904.70 Safari/537.36',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Referer': 'https://my.moneydashboard.com/dashboard',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8,it;q=0.7',
        }

        if self.get_session() is None:
            self.login()

        try:
            response = self.get_session().request("GET", url, headers=headers)
            response.raise_for_status()
        except HTTPError as http_err:
            self.__logger.error(f'[HTTP Error]: Failed to get Account List ({http_err})')
            raise SystemExit
        except Exception as err:
            self.__logger.error(f'[Error]: Failed to get Account List ({err})')
            raise SystemExit
        else:
            return response.json()

    def getBalances(self):
        TWOPLACES = Decimal(10) ** -2
        
        balance = {
            "net_balance": Decimal(0.00),
            "positive_balance": Decimal(0.00),
            "negative_balance": Decimal(0.00),
        }
        balances = []

        accounts = self.getAccounts()
        for account in accounts:
            if account['IsClosed'] is not True:
                if account["IsIncludedInCashflow"] is True:
                    bal = Decimal(account['Balance'])
                    if account["Balance"] >=0:
                        balance["positive_balance"] += bal
                    else:
                        balance["negative_balance"] += bal

                    balance['net_balance'] += bal

                balances.append({
                    "operator": account["Institution"]["Name"],
                    "name": account["Name"],
                    "balance": self.moneyfmt(Decimal(account["Balance"])),
                    "last_update": account["LastRefreshed"]
                })

        balance['net_balance'] = self.moneyfmt(Decimal(balance['net_balance']))
        balance['positive_balance'] = self.moneyfmt(Decimal(balance['positive_balance']))
        balance['negative_balance'] = self.moneyfmt(Decimal(balance['negative_balance']))
        balance['balances'] = balances

        return json.dumps(balance)

    def moneyfmt(self, value, places=2, curr='', sep=',', dp='.',
                 pos='', neg='-', trailneg=''):
        """Convert Decimal to a money formatted string.

        places:  required number of places after the decimal point
        curr:    optional currency symbol before the sign (may be blank)
        sep:     optional grouping separator (comma, period, space, or blank)
        dp:      decimal point indicator (comma or period)
                 only specify as blank when places is zero
        pos:     optional sign for positive numbers: '+', space or blank
        neg:     optional sign for negative numbers: '-', '(', space or blank
        trailneg:optional trailing minus indicator:  '-', ')', space or blank


        """
        q = Decimal(10) ** -places  # 2 places --> '0.01'
        sign, digits, exp = value.quantize(q).as_tuple()
        result = []
        digits = list(map(str, digits))
        build, next = result.append, digits.pop
        if sign:
            build(trailneg)
        for i in range(places):
            build(next() if digits else '0')
        if places:
            build(dp)
        if not digits:
            build('0')
        i = 0
        while digits:
            build(next())
            i += 1
            if i == 3 and digits:
                i = 0
                build(sep)
        build(curr)
        build(neg if sign else pos)
        return ''.join(reversed(result))

