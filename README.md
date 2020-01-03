# MoneyDashboard

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
md = MoneyDashboard(email, password)
```

Once authenticated, you can start fetching data from the MoneyDashboard API.

```python
balances = md.getBalances()
```

The above request will load your accounts data, and with that response you can get your balances.

```python
print('Net Balance: ', balances['net_balance'])
```