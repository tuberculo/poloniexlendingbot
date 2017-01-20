# coding=utf-8
from ConfigParser import SafeConfigParser

config = SafeConfigParser()
Data = None
# This module is the middleman between the bot and a SafeConfigParser object, so that we can add extra functionality
# without clogging up lendingbot.py with all the config logic. For example, added a default value to get().


def init(file_location, data=None):
    global Data
    Data = data
    loaded_files = config.read(file_location)
    if len(loaded_files) != 1:
        import shutil
        # Copy default config file if not found
        try:
            shutil.copy('default.cfg.example', file_location)
            print '\ndefault.cfg.example has been copied to ' + file_location + '\n' \
                  'Edit it with your API key and custom settings.\n'
            raw_input("Press Enter to acknowledge and exit...")
            exit(1)
        except Exception as ex:
            print "Failed to automatically copy config. Please do so manually. Error: " + str(ex)
            exit(1)
    return config


def has_option(category, option):
    return config.has_option(category, option)


def getboolean(category, option, default_value=False):
    if config.has_option(category, option):
        return config.getboolean(category, option)
    else:
        return default_value


def get(category, option, default_value=False, lower_limit=False, upper_limit=False):
    if config.has_option(category, option):
        value = config.get(category, option)
        if lower_limit:
            if float(value) < float(lower_limit):
                print "ERROR: " + option + "'s value: '" + value + "' is below the minimum limit: " + str(lower_limit)
                exit(1)
        if upper_limit:
            if float(value) > float(upper_limit):
                print "ERROR: " + option + "'s value: '" + value + "' is above the maximum limit: " + str(upper_limit)
                exit(1)
        return value
    else:
        if default_value is None:
            print "ERROR: " + option + " is not allowed to be left unset. Please check your config."
            exit(1)
        return default_value
# Below: functions for returning some config values that require special treatment.


def get_coin_cfg():
    coin_cfg = {}
    if config.has_option("BOT", "coinconfig"):
        try:
            # parsed
            import json
            from decimal import Decimal

            coin_config = (json.loads(config.get("BOT", "coinconfig")))
            for cur in coin_config:
                cur = cur.split(':')
                coin_cfg[cur[0]] = dict(minrate=(Decimal(cur[1])) / 100, maxactive=Decimal(cur[2]),
                                        maxtolend=Decimal(cur[3]), maxpercenttolend=(Decimal(cur[4])) / 100,
                                        maxtolendrate=(Decimal(cur[5])) / 100)
        except Exception as ex:
            print "Coinconfig parsed incorrectly, please refer to the documentation. Error: " + str(ex)
    return coin_cfg


def get_currencies_list(option):
    if config.has_option("BOT", option):
        full_list = ['STR', 'BTC', 'BTS', 'CLAM', 'DOGE', 'DASH', 'LTC', 'MAID', 'XMR', 'XRP', 'ETH', 'FCT']
        cur_list = []
        raw_cur_list = config.get("BOT", option).split(",")
        for raw_cur in raw_cur_list:
            cur = raw_cur.strip(' ').upper()
            if cur == 'ALL':
                return full_list
            elif cur == 'ACTIVE':
                cur_list += Data.get_lending_currencies()
            else:
                if cur in full_list:
                    cur_list.append(cur)
        return list(set(cur_list))
    else:
        return []
