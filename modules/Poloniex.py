# coding=utf-8
import hashlib
import hmac
import json
import socket
import time
import urllib
import urllib2


class PoloniexApiError(Exception):
    pass


def create_time_stamp(datestr, formatting="%Y-%m-%d %H:%M:%S"):
    return time.mktime(time.strptime(datestr, formatting))


class Poloniex:
    def __init__(self, api_key, secret):
        self.APIKey = api_key
        self.Secret = secret
        socket.setdefaulttimeout(30)

    def post_process(self, before):
        after = before

        # Add timestamps if there isnt one but is a datetime
        if 'return' in after:
            if isinstance(after['return'], list):
                for x in xrange(0, len(after['return'])):
                    if isinstance(after['return'][x], dict):
                        if 'datetime' in after['return'][x] and 'timestamp' not in after['return'][x]:
                            after['return'][x]['timestamp'] = float(create_time_stamp(after['return'][x]['datetime']))

        return after

    def api_query(self, command, req=None):

        if req is None:
            req = {}

        def _read_response(resp):
            data = json.loads(resp.read())
            if 'error' in data:
                raise PoloniexApiError(data['error'])
            return data

        try:
            if command == "returnTicker" or command == "return24hVolume":
                ret = urllib2.urlopen(urllib2.Request('https://poloniex.com/public?command=' + command))
                return _read_response(ret)
            elif command == "returnOrderBook":
                ret = urllib2.urlopen(urllib2.Request(
                    'https://poloniex.com/public?command=' + command + '&currencyPair=' + str(req['currencyPair'])))
                return _read_response(ret)
            elif command == "returnMarketTradeHistory":
                ret = urllib2.urlopen(urllib2.Request(
                    'https://poloniex.com/public?command=' + "returnTradeHistory" + '&currencyPair=' + str(
                        req['currencyPair'])))
                return _read_response(ret)
            elif command == "returnLoanOrders":
                req_url = 'https://poloniex.com/public?command=' + "returnLoanOrders" + '&currency=' + str(req['currency'])
                if req['limit'] != '':
                    req_url += '&limit=' + str(req['limit'])
                ret = urllib2.urlopen(urllib2.Request(req_url))
                return _read_response(ret)
            else:
                req['command'] = command
                req['nonce'] = int(time.time() * 1000)
                post_data = urllib.urlencode(req)

                sign = hmac.new(self.Secret, post_data, hashlib.sha512).hexdigest()
                headers = {
                    'Sign': sign,
                    'Key': self.APIKey
                }

                ret = urllib2.urlopen(urllib2.Request('https://poloniex.com/tradingApi', post_data, headers))
                json_ret = _read_response(ret)
                return self.post_process(json_ret)
        except Exception as ex:
            # add command information to exception
            # (this isn't compatible with python 3)
            import sys
            raise type(ex), type(ex)(ex.message + ' Requesting %s' % command), sys.exc_info()[2]

    def return_ticker(self):
        return self.api_query("returnTicker")

    def return24h_volume(self):
        return self.api_query("return24hVolume")

    def return_order_book(self, currency_pair):
        return self.api_query("returnOrderBook", {'currencyPair': currency_pair})

    def return_market_trade_history(self, currency_pair):
        return self.api_query("returnMarketTradeHistory", {'currencyPair': currency_pair})

    def transfer_balance(self, currency, amount, from_account, to_account):
        return self.api_query("transferBalance", {'currency': currency, 'amount': amount, 'fromAccount': from_account,
                                                  'toAccount': to_account})

    # Returns all of your balances.
    # Outputs: 
    # {"BTC":"0.59098578","LTC":"3.31117268", ... }
    def return_balances(self):
        return self.api_query('returnBalances')

    def return_available_account_balances(self, account):
        balances = self.api_query('returnAvailableAccountBalances', {"account": account})
        if isinstance(balances, list):  # silly api wrapper, empty dict returns a list, which breaks the code later.
            balances = {}
        return balances

    # Returns your open orders for a given market, specified by the "currencyPair" POST parameter, e.g. "BTC_XCP"
    # Inputs:
    # currencyPair  The currency pair e.g. "BTC_XCP"
    # Outputs: 
    # orderNumber   The order number
    # type          sell or buy
    # rate          Price the order is selling or buying at
    # Amount        Quantity of order
    # total         Total value of order (price * quantity)
    def return_open_orders(self, currency_pair):
        return self.api_query('returnOpenOrders', {"currencyPair": currency_pair})

    def return_open_loan_offers(self):
        loan_offers = self.api_query('returnOpenLoanOffers')
        if isinstance(loan_offers, list):  # silly api wrapper, empty dict returns a list, which breaks the code later.
            loan_offers = {}
        return loan_offers

    def return_active_loans(self):
        return self.api_query('returnActiveLoans')

    # Returns your trade history for a given market, specified by the "currencyPair" POST parameter
    # Inputs:
    # currencyPair  The currency pair e.g. "BTC_XCP"
    # Outputs: 
    # date          Date in the form: "2014-02-19 03:44:59"
    # rate          Price the order is selling or buying at
    # amount        Quantity of order
    # total         Total value of order (price * quantity)
    # type          sell or buy
    def return_trade_history(self, currency_pair):
        return self.api_query('returnTradeHistory', {"currencyPair": currency_pair})

    # Places a buy order in a given market. Required POST parameters are "currencyPair", "rate", and "amount".
    # If successful, the method will return the order number.
    # Inputs:
    # currencyPair  The curreny pair
    # rate          price the order is buying at
    # amount        Amount of coins to buy
    # Outputs: 
    # orderNumber   The order number
    def buy(self, currency_pair, rate, amount):
        return self.api_query('buy', {"currencyPair": currency_pair, "rate": rate, "amount": amount})

    # Places a sell order in a given market. Required POST parameters are "currencyPair", "rate", and "amount".
    # If successful, the method will return the order number.
    # Inputs:
    # currencyPair  The curreny pair
    # rate          price the order is selling at
    # amount        Amount of coins to sell
    # Outputs: 
    # orderNumber   The order number
    def sell(self, currency_pair, rate, amount):
        return self.api_query('sell', {"currencyPair": currency_pair, "rate": rate, "amount": amount})

    def create_loan_offer(self, currency, amount, duration, auto_renew, lending_rate):
        return self.api_query('createLoanOffer',
                              {"currency": currency, "amount": amount, "duration": duration, "autoRenew": auto_renew,
                               "lendingRate": lending_rate, })

    # Cancels an order you have placed in a given market. Required POST parameters are "currencyPair" and "orderNumber".
    # Inputs:
    # currencyPair  The curreny pair
    # orderNumber   The order number to cancel
    # Outputs: 
    # succes        1 or 0
    def cancel(self, currency_pair, order_number):
        return self.api_query('cancelOrder', {"currencyPair": currency_pair, "orderNumber": order_number})

    def cancel_loan_offer(self, currency, order_number):
        return self.api_query('cancelLoanOffer', {"currency": currency, "orderNumber": order_number})

    # Immediately places a withdrawal for a given currency, with no email confirmation.
    # In order to use this method, the withdrawal privilege must be enabled for your API key.
    # Required POST parameters are "currency", "amount", and "address". Sample output: {"response":"Withdrew 2398 NXT."}
    # Inputs:
    # currency      The currency to withdraw
    # amount        The amount of this coin to withdraw
    # address       The withdrawal address
    # Outputs: 
    # response      Text containing message about the withdrawal
    def withdraw(self, currency, amount, address):
        return self.api_query('withdraw', {"currency": currency, "amount": amount, "address": address})

    def return_loan_orders(self, currency, limit=''):
        return self.api_query('returnLoanOrders', {"currency": currency, "limit": limit})

    # Toggles the auto renew setting for the specified orderNumber
    def toggle_auto_renew(self, order_number):
        return self.api_query('toggleAutoRenew', {"orderNumber": order_number})
