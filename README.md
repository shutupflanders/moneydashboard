# MoneyDashboard

[![Buy me a coffee][buymeacoffee-shield]][buymeacoffee]

Python library for accessing MoneyDashboard data

# Installation

## With Pip

`pip install moneydashboard`

## With Source Code

You can get the source code by cloning it from Github:

`git clone https://github.com/shutupflanders/moneydashboard.git`

or get the tarball:

`curl -OJL https://github.com/shutupflanders/moneydashboard/tarball/master`

then either include the library into your code, or install it with:

`python setup.py install`

# Usage

You need to first create an instance.

```python
md = MoneyDashboard(email="myemail@email.com", password="MyPassword123")
```

**Arguments**:
* `email` - the account e-mail used for your MoneyDashboard account
* `password` - the password for said account
* `format_as_currency` - (bool) if set to `True` it will return the currency symbol with all monetary values.


Once authenticated, you can start fetching data from the MoneyDashboard API.
It will return data as a JSON string, or throw an exception if something went wrong.

## Methods

`get_balances` - retrieves a list of your account balances and an overview:
```python
balances = json.loads(md.get_balances())
```

*Response example:*
```json
{
  "net_balance": "1,234.56",
  "positive_balance": "1,234.56",
  "negative_balance": "0",
  "balances": {
    "current_accounts": [
      {
        "operator": "FakeBank Ltd",
        "name": "Fake Account",
        "balance": "123.45",
        "currency": "GBP",
        "last_update": "2021-01-01T12:33:21.979768Z"
      },
      ...
    ]
  }    
}
```

`get_transactions` - retrieves the transactions for all accounts using the given filter:
* `1` - Last 7 Days
* `2` - Since Last Login
* `3` - All Untagged
The above request will load your account data, and with that response you can get your balances.
```python
balances = json.loads(md.get_transactions(type=1))
```
*Response example*:
```json
{
  {
    "date": "2021-01-01 00:00:00+00:00",
    "account": "Fake Bank - Main Account",
    "type": "Debit",
    "amount": "-123.45",
    "currency": "GBP"
  },
  ....
}
```

[buymeacoffee-shield]: https://www.buymeacoffee.com/assets/img/guidelines/download-assets-sm-2.svg
[buymeacoffee]: https://www.buymeacoffee.com/IcV9egW
