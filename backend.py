from threading import Thread
from time import sleep
from os import path,\
    mkdir,\
    listdir,\
    remove
from shutil import copyfile
from logging import getLogger
from json import load,\
    dump
from datetime import datetime
from traceback import format_exc
from sqlite3 import connect
from chia.util.bech32m import decode_puzzle_hash, encode_puzzle_hash
from chia.util.byte_types import hexstr_to_bytes
from variables import full_node_db_path,\
    denominator,\
    backend_ops_timeout_s,\
    backup_descriptor,\
    pre_mine_addrs

class json_ops_class():

    def __init__(self):
        self._log = getLogger()
        if not path.isdir('wd'):
            mkdir('wd')
            self._log.debug('The working dir was created as it was missing.')
        self._log.info('{} initialized'.format(type(self).__name__))

    def read_json(self,
                  json_filepath):
        while True:
            try:
                with open(json_filepath, 'r') as json_in_handle:
                    return load(json_in_handle)
            except:
                self._log.warning('Retrying load of {}, failed because \n{}'.format(json_filepath,
                                                                       format_exc(chain=False)))
                sleep(1)

    def save_json(self,
                  json_filepath,
                  obj):
        while True:
            try:
                with open(json_filepath, 'w') as json_out_handle:
                    return dump(obj, json_out_handle, indent=2)
            except:
                self._log.warning('Retrying dump in {}, failed because \n{}'.format(json_filepath,
                                                                       format_exc(chain=False)))
                sleep(1)

class DataParser(json_ops_class):
    def __init__(self):
        super(DataParser, self).__init__()

    def return_latest_total_supply(self):
        wf_contents = self.read_json(json_filepath=path.join('wd', 'wf.json'))
        return sum(addr[1]['coin_balance'] for addr in wf_contents[-1]['data'].items())

    def return_latest_circulating_supply(self):
        wf_contents = self.read_json(json_filepath=path.join('wd', 'wf.json'))
        return sum(addr[1]['coin_balance'] for addr in wf_contents[-1]['data'].items()) - \
               sum(addr[1]['coin_balance'] for addr in filter(lambda x:x[0] in pre_mine_addrs, wf_contents[-1]['data'].items()))

class json_ops_daemon_thread(json_ops_class):

    def __init__(self):
        super(json_ops_daemon_thread, self).__init__()
        if path.isfile(path.join('wd', 'wf.json')):
            with open(path.join('wd', 'wf.json')) as wf_in:
                self.wf_contents = load(wf_in)
            self.addresses = {'last_height': self.wf_contents[-1]['last_height'],
                              'data': self.wf_contents[-1]['data']}
            self._log.info('wf contents loaded from disk')
        else:
            self.wf_contents = []
            self.addresses = {'last_height': 0,
                              'data': {}}
            self._log.info('wf contents initialized from scratch')
        self._log.info('{} initialized'.format(type(self).__name__))

    def backup(self):
        self._log.info('Backup in progress')
        while True:
            try:
                all_filespaths = sorted([path.join('wd', x) for x in listdir('wd')], key=path.getmtime)
                while len(listdir('wd')) > backup_descriptor['number_of_files']:
                    remove(all_filespaths[0])
                    all_filespaths.pop(0)
                break
            except:
                self._log.error('Problem found in \"wd\" when deleting the old files. Retrying ...')
                self._log.debug(format_exc(chain=False))
                sleep(5)
        if path.isfile(path.join('wd', 'wf.json')):
            copyfile(path.join('wd', 'wf.json'),
                     path.join('wd', str(datetime.now()).replace(':', '_') + '__' + 'wf.json'))
        self._log.info('Backup completed')

    def dump_on_disk(self):
        self._log.info('Save on disk in progress ...')
        self.wf_contents.append(self.addresses)

        while (len(self.wf_contents)) > backup_descriptor['number_of_entries']:
            self.wf_contents.pop(0)

        self.save_json(json_filepath=path.join('wd', 'wf.json'),
                       obj=self.wf_contents)
        self._log.info('Save on disk in completed')

    def refresh_addresses(self):
        self._log.info('Address refresh in progress ...')
        conn = connect(full_node_db_path)
        dbcursor = conn.cursor()
        dbcursor.execute("SELECT spent, puzzle_hash, amount FROM coin_record LIMIT {last_height},(SELECT COUNT(*) FROM coin_record);".format(last_height=self.addresses['last_height']))
        rows = dbcursor.fetchall()

        for row in rows:
            wallet = encode_puzzle_hash(hexstr_to_bytes(row[1]), prefix='hdd')
            if wallet not in self.addresses['data'].keys():
                self.addresses['data'][wallet] = {'coin_balance': 0,
                                          'coin_spent': 0}
                coin_raw=int.from_bytes(row[2], 'big')
                coin=coin_raw/denominator
                if row[0]:
                    self.addresses['data'][wallet]['coin_spent'] += coin
                else:
                    self.addresses['data'][wallet]['coin_balance'] += coin
            else:
                coin_raw=int.from_bytes(row[2], 'big')
                coin=coin_raw/denominator
                if row[0]:
                    self.addresses['data'][wallet]['coin_spent'] += coin
                else:
                    self.addresses['data'][wallet]['coin_balance'] += coin
        new_records = len(rows)
        self.addresses['last_height'] += new_records
        self._log.info('Address refresh completed. {} new records were added.'.format(new_records))

    def loop_slave(self):
        while True:
            self.refresh_addresses()
            self.backup()
            self.dump_on_disk()
            sleep(backend_ops_timeout_s)

    def loop(self):
        t = Thread(target=self.loop_slave).start()