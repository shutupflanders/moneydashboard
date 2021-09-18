import json
import logging
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import requests
from babel.numbers import format_currency, format_decimal
from bs4 import BeautifulSoup
from requests.exceptions import HTTPError


class LoginFailedException(Exception):
    pass


class GetAccountsListFailedException(Exception):
    pass


class GetTransactionListFailedException(Exception):
    pass


class InvalidTransactionListTypeFilter(Exception):
    pass


class MoneyDashboard:
    def __init__(self, email, password, currency="GBP", format_as_currency=True):
        self.__logger = logging.getLogger()
        self.__session = None
        self._requestVerificationToken = ""

        self._email = email
        self._password = password

        self._currency = currency
        self._formatAsCurrency = format_as_currency
        self._accounts = self._get_accounts()
        self._transactionFilterTypes = {
            1: "Last 7 Days",
            2: "Since Last Login",
            3: "All Untagged",
        }
        datetime.now(timezone.utc)

    def _get_session(self):
        return self.__session

    def _set_session(self, session):
        self.__session = session

    def _login(self):
        self.__logger.info("Logging in...")

        self._set_session(requests.session())

        landing_url = "https://my.moneydashboard.com/landing"
        landing_response = self._get_session().request("GET", landing_url)
        soup = BeautifulSoup(landing_response.text, "html.parser")
        self._requestVerificationToken = soup.find(
            "input", {"name": "__RequestVerificationToken"}
        )["value"]

        cookies = self._get_session().cookies.get_dict()
        cookie_string = "; ".join([str(x) + "=" + str(y) for x, y in cookies.items()])

        self._set_session(requests.session())
        # Login to Moneydashboard using the credentials provided in config
        url = "https://my.moneydashboard.com/landing/login"

        payload = {
            "OriginId": "1",
            "Password": self._password,
            "Email": self._email,
            "CampaignRef": "",
            "ApplicationRef": "",
            "UserRef": "",
        }
        headers = {
            "Origin": "https://my.moneydashboard.com",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) \
            Chrome/79.0.3945.88 Safari/537.36",
            "Content-Type": "application/json;charset=UTF-8",
            "Accept": "application/json, text/plain, */*",
            "X-Requested-With": "XMLHttpRequest",
            "X-Newrelic-Id": "UA4AV1JTGwAJU1BaDgc=",
            "__requestverificationtoken": self._requestVerificationToken,
            "Dnt": "1",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Referer": "https://my.moneydashboard.com/landing",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8,it;q=0.7",
            "Cookie": cookie_string,
        }
        try:
            response = self._get_session().request(
                "POST", url, json=payload, headers=headers
            )
            response.raise_for_status()
        except HTTPError as http_err:
            self.__logger.error("[HTTP Error]: Failed to login (%s)", http_err)
            raise LoginFailedException from http_err
        except Exception as err:
            self.__logger.error("[Error]: Failed to login (%s)", err)
            raise LoginFailedException from err
        else:
            response_data = response.json()
            if response_data["IsSuccess"] is True:
                return response_data["IsSuccess"]
            else:
                self.__logger.error(
                    "[Error]: Failed to login (%s)", response_data["ErrorCode"]
                )
                raise LoginFailedException

    def _get_headers(self):
        return {
            "Authority": "my.moneydashboard.com",
            "Accept": "application/json, text/plain, */*",
            "X-Newrelic-Id": "UA4AV1JTGwAJU1BaDgc=",
            "Dnt": "1",
            "X-Requested-With": "XMLHttpRequest",
            "__requestverificationtoken": self._requestVerificationToken,
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) C\
            hrome/78.0.3904.70 Safari/537.36",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Referer": "https://my.moneydashboard.com/dashboard",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8,it;q=0.7",
        }

    def _get_accounts(self):
        """Retrieve account list from MoneyDashboard account"""
        self.__logger.info("Getting Accounts...")

        # Session expires every 10 minutes or so, so we'll login again anyway.
        self._login()

        url = "https://my.moneydashboard.com/api/Account/"

        headers = self._get_headers()
        try:
            response = self._get_session().request("GET", url, headers=headers)
            response.raise_for_status()
        except HTTPError as http_err:
            self.__logger.error(
                "[HTTP Error]: Failed to get Account List (%s)", http_err
            )
            raise GetAccountsListFailedException from http_err
        except Exception as err:
            self.__logger.error("[Error]: Failed to get Account List (%s)", err)
            raise GetAccountsListFailedException from err
        else:
            accounts = {}
            for account in response.json():
                accounts[account["Id"]] = account
            return accounts

    def _get_transactions(self, type: int):
        """Retrieve transactions from MoneyDashboard account"""
        if type not in self._transactionFilterTypes:
            self.__logger.error("Invalid Transaction Filter.")
            raise InvalidTransactionListTypeFilter

        self.__logger.info("Getting Transactions...")

        # Session expires every 10 minutes or so, so we'll login again anyway.
        self._login()

        url = (
            "https://my.moneydashboard.com/dashboard/GetWidgetTransactions?filter="
            + str(type)
        )

        headers = self._get_headers()
        try:
            response = self._get_session().request("GET", url, headers=headers)
            response.raise_for_status()
        except HTTPError as http_err:
            self.__logger.error(
                "[HTTP Error]: Failed to get Transaction List (%s)", http_err
            )
            raise GetTransactionListFailedException from http_err
        except Exception as err:
            self.__logger.error("[Error]: Failed to get Transaction List (%s)", err)
            raise GetTransactionListFailedException from err
        else:
            return response.json()

    def _money_fmt(self, balance):
        return (
            format_currency(Decimal(balance), self._currency, locale="en_GB")
            if self._formatAsCurrency
            else format_decimal(Decimal(balance))
        )

    def _parse_wcf_date(self, time_string):
        epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
        ticks, offset = re.match(r"/Date\((\d+)([+-]\d{4})?\)/$", time_string).groups()
        utc_dt = epoch + timedelta(milliseconds=int(ticks))
        if offset:
            offset = int(offset)
            # http://www.odata.org/documentation/odata-version-2-0/json-format
            # says offset is minutes (an error?)
            dt = utc_dt.astimezone(timezone(timedelta(minutes=offset)))
            # but it looks like it could be HHMM
            hours, minutes = divmod(abs(offset), 100)
            if offset < 0:
                hours, minutes = -hours, -minutes
            dt = utc_dt.astimezone(timezone(timedelta(hours=hours, minutes=minutes)))
            return dt.strftime("%Y/%m/%d, %H:%M:%S")
        return utc_dt

    def get_balances(self):
        balance = {
            "net_balance": Decimal(0.00),
            "positive_balance": Decimal(0.00),
            "negative_balance": Decimal(0.00),
        }

        current_accounts_balances = []
        credit_cards_balances = []
        saving_goals_balances = []
        savings_accounts_balances = []
        other_accounts_balances = []
        unknown_balances = []

        accounts = self._accounts
        for _, account in accounts.items():
            if account["IsClosed"] is not True:
                if (
                    account["IsIncludedInCashflow"] is True
                    and account["IncludeInCalculations"] is True
                ):
                    bal = Decimal(account["Balance"])
                    if account["Balance"] >= 0:
                        balance["positive_balance"] += bal
                    else:
                        balance["negative_balance"] += bal

                    balance["net_balance"] += bal

                balance_obj = {
                    "operator": account["Institution"]["Name"],
                    "name": account["Name"],
                    "balance": self._money_fmt(account["Balance"]),
                    "currency": self._currency,
                    "last_update": account["LastRefreshed"],
                }

                if account["AccountTypeId"] == 0:
                    current_accounts_balances.append(balance_obj)
                elif account["AccountTypeId"] == 1:
                    savings_accounts_balances.append(balance_obj)
                elif account["AccountTypeId"] == 2:
                    credit_cards_balances.append(balance_obj)
                elif account["AccountTypeId"] == 3:
                    other_accounts_balances.append(balance_obj)
                elif account["AccountTypeId"] == 4:
                    saving_goals_balances.append(balance_obj)
                else:
                    unknown_balances.append(balance_obj)

        balance["net_balance"] = self._money_fmt(balance["net_balance"])
        balance["positive_balance"] = self._money_fmt(balance["positive_balance"])
        balance["negative_balance"] = self._money_fmt(balance["negative_balance"])
        balance["balances"] = {
            "current_accounts": current_accounts_balances,
            "credit_cards": credit_cards_balances,
            "other_accounts": other_accounts_balances,
            "saving_goals": saving_goals_balances,
            "savings_accounts": savings_accounts_balances,
            "unknown": unknown_balances,
        }

        return json.dumps(balance)

    def get_transactions(self, type):
        transactions = self._get_transactions(type)

        transaction_list = []
        for transaction in transactions:
            transaction_list.append(
                {
                    "date": self._parse_wcf_date(transaction["Date"]),
                    "account": self._accounts[transaction["AccountId"]]["Institution"][
                        "Name"
                    ]
                    + " - "
                    + self._accounts[transaction["AccountId"]]["Name"]
                    if transaction["AccountId"] in self._accounts
                    else "Unknown",
                    "type": "Debit" if transaction["IsDebit"] else "Credit",
                    "amount": self._money_fmt(transaction["Amount"]),
                    "currency": transaction["NativeCurrency"],
                }
            )

        return json.dumps(transaction_list, default=str)
