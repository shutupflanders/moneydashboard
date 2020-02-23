import requests
from requests.exceptions import HTTPError
from babel.numbers import format_currency
import logging
import json
from decimal import Decimal


class LoginFailedException(Exception):
    pass


class GetAccountsListFailedException(Exception):
    pass


class MoneyDashboard():
    def __init__(self, session=None, email=None, password=None, currency="GBP"):
        self.__session = session
        self.__logger = logging.getLogger()
        self._email = email
        self._password = password
        self._currency = currency

    def get_session(self):
        return self.__session

    def set_session(self, session):
        self.__session = session

    def login(self):
        self.__logger.info('Logging in...')
        """Login to Moneydashboard using the credentials provided in config"""
        url = "https://my.moneydashboard.com/landing/login"

        payload = {
            "OriginId": "1",
            "Email": self._email,
            "Password": self._password,
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
            raise LoginFailedException
        except Exception as err:
            self.__logger.error(f'[Error]: Failed to login ({err})')
            raise LoginFailedException
        else:
            response_data = response.json()
            if response_data["IsSuccess"] is True:
                return response_data['IsSuccess']
            else:
                self.__logger.error(f'[Error]: Failed to login ({response_data["ErrorCode"]})')
                raise LoginFailedException

    def get_accounts(self):
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
        """Session expires every 10 minutes or so, so we'll login again anyway."""
        self.login()
        try:
            response = self.get_session().request("GET", url, headers=headers)
            response.raise_for_status()
        except HTTPError as http_err:
            self.__logger.error(f'[HTTP Error]: Failed to get Account List ({http_err})')
            raise GetAccountsListFailedException
        except Exception as err:
            self.__logger.error(f'[Error]: Failed to get Account List ({err})')
            raise GetAccountsListFailedException
        else:
            return response.json()

    def _money_fmt(self, balance):
        return format_currency(Decimal(balance), self._currency, locale='en_GB')

    def get_balances(self):
        balance = {
            "net_balance": Decimal(0.00),
            "positive_balance": Decimal(0.00),
            "negative_balance": Decimal(0.00),
        }

        current_accounts_balances = []
        credit_cards_balances = []
        saving_goals_balances = []
        other_accounts_balances = []
        unknown_balances = []

        accounts = self.get_accounts()
        for account in accounts:
            if account['IsClosed'] is not True:
                if account["IsIncludedInCashflow"] is True and account["IncludeInCalculations"] is True:
                    bal = Decimal(account['Balance'])
                    if account["Balance"] >=0:
                        balance["positive_balance"] += bal
                    else:
                        balance["negative_balance"] += bal

                    balance['net_balance'] += bal

                balance_obj = {
                    "operator": account["Institution"]["Name"],
                    "name": account["Name"],
                    "balance": self._money_fmt(account["Balance"]),
                    "last_update": account["LastRefreshed"]
                }

                if account["AccountTypeId"] == 0:
                    current_accounts_balances.append(balance_obj)
                elif account["AccountTypeId"] == 2:
                    credit_cards_balances.append(balance_obj)
                elif account["AccountTypeId"] == 3:
                    other_accounts_balances.append(balance_obj)
                elif account["AccountTypeId"] == 4:
                    saving_goals_balances.append(balance_obj)
                else:
                    unknown_balances.append(balance_obj)

        acct_balances = {
            "current_accounts": current_accounts_balances,
            "credit_cards": credit_cards_balances,
            "other_accounts": other_accounts_balances,
            "saving_goals": saving_goals_balances,
            "unknown": unknown_balances,
        }

        balance['net_balance'] = self._money_fmt(balance['net_balance'])
        balance['positive_balance'] = self._money_fmt(balance['positive_balance'])
        balance['negative_balance'] = self._money_fmt(balance['negative_balance'])
        balance['balances'] = acct_balances

        return json.dumps(balance)
