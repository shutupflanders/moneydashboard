import requests
from requests.exceptions import HTTPError
from babel.numbers import format_currency
import logging
import json
from decimal import Decimal
from bs4 import BeautifulSoup


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
        self._requestVerificationToken = ""

    def get_session(self):
        return self.__session

    def set_session(self, session):
        self.__session = session

    def login(self):
        self.__logger.info('Logging in...')

        self.set_session(requests.session())

        landing_url = "https://my.moneydashboard.com/landing"
        landing_response = self.get_session().request("GET", landing_url)
        soup = BeautifulSoup(landing_response.text, "html.parser")
        self._requestVerificationToken = soup.find("input", {"name": "__RequestVerificationToken"})['value']

        cookies = self.get_session().cookies.get_dict()
        cookie_string = "; ".join([str(x) + "=" + str(y) for x, y in cookies.items()])

        self.set_session(requests.session())
        """Login to Moneydashboard using the credentials provided in config"""
        url = "https://my.moneydashboard.com/landing/login"

        payload = {
            "OriginId": "1",
            "Password": self._password,
            "Email": self._email,
            "CampaignRef": "",
            "ApplicationRef": "",
            "UserRef": ""
        }
        headers = {
            'Origin': 'https://my.moneydashboard.com',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) \
            Chrome/79.0.3945.88 Safari/537.36',
            'Content-Type': 'application/json;charset=UTF-8',
            'Accept': 'application/json, text/plain, */*',
            'X-Requested-With': 'XMLHttpRequest',
            "X-Newrelic-Id": "UA4AV1JTGwAJU1BaDgc=",
            '__requestverificationtoken': self._requestVerificationToken,
            'Dnt': '1',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Referer': 'https://my.moneydashboard.com/landing',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8,it;q=0.7',
            'Cookie': cookie_string,
        }
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

        """Session expires every 10 minutes or so, so we'll login again anyway."""
        self.login()

        """Retrieve account list from MoneyDashboard account"""
        url = "https://my.moneydashboard.com/api/Account/"

        headers = {
            "Authority": "my.moneydashboard.com",
            'Accept': 'application/json, text/plain, */*',
            "X-Newrelic-Id": "UA4AV1JTGwAJU1BaDgc=",
            'Dnt': '1',
            'X-Requested-With': 'XMLHttpRequest',
            '__requestverificationtoken': self._requestVerificationToken,
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) C\
            hrome/78.0.3904.70 Safari/537.36',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Referer': 'https://my.moneydashboard.com/dashboard',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8,it;q=0.7',
        }
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
                    if account["Balance"] >= 0:
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
