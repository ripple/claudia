################################################################################
# This script is used to validate a rippled network by:
# 1. Verifying "server_state"
# 2. Perform a payment transaction
#
# Usage:
#   python3 scripts/validate_network.py [optional parameter]
#       [--rippledServer <rippled host:port (default: localhost:5001)>
################################################################################

import argparse
import json
import sys
import requests
import time

GENESIS_ACCOUNT_ID = "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh"
GENESIS_ACCOUNT_SEED = "snoPBrXtMeMyMHUVTgbuqAfg1SUTb"
DEFAULT_RIPPLED_SERVER = "localhost:5001"
TRANSFER_AMOUNT = "10000000000"
DESTINATION_ACCOUNT_ID = "rh1HPuRVsYYvThxG2Bs1MfjmrVC73S16Fb"
VALIDATION_CHECK_TIMEOUT = 300  # seconds


class RippledServer(object):
    def __init__(self, rippled_server=DEFAULT_RIPPLED_SERVER):
        self.rippled_server = "http://{}".format(rippled_server)

    def execute_transaction(self, payload, method):
        tx_json = None
        if "tx_json" in payload:
            tx_json = payload["tx_json"]
        if "secret" in payload:
            secret = payload["secret"]
            request = {"method": method, "params": [dict(tx_json=tx_json, secret=secret)]}
        else:
            request = {"method": method, "params": [tx_json]}

        try:
            response = requests.post(self.rippled_server, json.dumps(request))
            response_result = json.loads(response.content.decode('utf-8'))['result']

            if "engine_result" in response_result and (
                    response_result["engine_result"] == "tesSUCCESS" or
                    response_result["engine_result"] == "terQUEUED"):
                if self.is_transaction_validated(response_result):
                    print("  Transaction validated!")

        except requests.exceptions.RequestException as e:
            print("Failed to establish connection to rippled")
            sys.exit(1)

        return response_result

    def tx(self, tx_id):
        payload = {
            "tx_json": {
                "transaction": tx_id,
                "binary": False
            }
        }
        return self.execute_transaction(payload=payload, method="tx")

    def get_account_balance(self, account_id):
        payload = {
            "tx_json": {
                "account": account_id,
                "ledger_index": "current",
                "strict": True,
                "queue": True
            },
        }
        account_info = self.execute_transaction(payload=payload, method="account_info")
        try:
            return int(account_info['account_data']['Balance'])
        except KeyError as e:
            return 0

    def is_transaction_validated(self, response, engine_result="tesSUCCESS"):
        tx_id = response["tx_json"]["hash"]

        VALIDATION_CHECK_TIMEOUT = 30  # max sec for validating tnx
        start_time = time.time()
        end_time = start_time + VALIDATION_CHECK_TIMEOUT
        while time.time() <= end_time:
            tx_response = self.tx(tx_id)
            if tx_response["validated"]:
                if response["engine_result"] == "terQUEUED":
                    return True
                else:
                    if tx_response["meta"]["TransactionResult"] == engine_result:
                        return True
            time.sleep(1)
        raise Exception("  Transaction not validated: {}".format(tx_id))


def verify_network(rippled):
    print("  Server State: ", end="")
    start_time = time.time()
    while True:
        time.sleep(5)
        server_info = rippled.execute_transaction(payload={}, method="server_info")
        server_state = server_info["info"]["server_state"]
        proposers = server_info["info"]["last_close"]["proposers"]
        if server_state in ("full", "proposing") and proposers != 0:
            print("{}".format(server_state))
            break

        if time.time() > (start_time + VALIDATION_CHECK_TIMEOUT):
            print("{}".format(server_state))
            sys.exit(1)


def verify_payment_txn(rippled):
    print("  Verify Payment Transaction")
    initial_balance = int(rippled.get_account_balance(DESTINATION_ACCOUNT_ID))

    payload = {
        "tx_json": {
            "TransactionType": "Payment",
            "Account": GENESIS_ACCOUNT_ID,
            "Destination": DESTINATION_ACCOUNT_ID,
            "Amount": TRANSFER_AMOUNT,
        },
        "secret": GENESIS_ACCOUNT_SEED
    }
    rippled.execute_transaction(payload=payload, method="submit")
    new_balance = int(rippled.get_account_balance(DESTINATION_ACCOUNT_ID))

    if new_balance != (initial_balance + int(TRANSFER_AMOUNT)):
        print("  Account balance mismatch")
        sys.exit(1)


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rippledServer', default=DEFAULT_RIPPLED_SERVER,
                        help="rippled server (default: {})".format(DEFAULT_RIPPLED_SERVER))
    parser.add_argument("--paymentTransaction", help="Submit a Payment Transaction", action='store_true')

    return parser.parse_args()


def main(rippled_server, submit_payment_txn):
    rippled = RippledServer(rippled_server)
    verify_network(rippled)
    if submit_payment_txn:
        verify_payment_txn(rippled)


if __name__ == '__main__':
    cmd_args = parse_arguments()
    main(cmd_args.rippledServer, cmd_args.paymentTransaction)
