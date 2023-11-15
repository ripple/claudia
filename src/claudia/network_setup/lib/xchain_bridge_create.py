import argparse
import glob
import json
import os
import pathlib
import requests
import sys
import time
from jinja2 import Environment, FileSystemLoader

file_path = pathlib.Path(__file__).parent.resolve()
GENESIS_ACCOUNT_ID = "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh"
GENESIS_ACCOUNT_SEED = "snoPBrXtMeMyMHUVTgbuqAfg1SUTb"
DESTINATION_ACCOUNT_ID = "rh1HPuRVsYYvThxG2Bs1MfjmrVC73S16Fb"
DEFAULT_LOCKING_SERVER_ENDPOINT = "localhost:5001"
DEFAULT_ISSUING_SERVER_ENDPOINT = "localhost:5003"
DEFAULT_TRANSFER_AMOUNT = "1000000000"
MIN_ACCOUNT_CREATE_AMOUNT = "500000000"
DEFAULT_ACCOUNT_KEY_TYPE = "secp256k1"
WITNESS_SIGNING_KEY_KEY = "ed25519"
WITNESS_QUORUM = 0.8
VALIDATION_CHECK_TIMEOUT = 300  # max sec for validating tnx
SIGNATURE_REWARD = 100
SIDECHAIN_BRIDGE_CURRENCY_XRP = {"currency": "XRP"}
ISSUING_CHAIN_MASTER_ACCOUNT_DEFAULT_BALANCE = "1000000000000000"
NO_OF_WITNESS_SERVERS = 5
WITNESS_CONFIG_TEMPLATE_DIR = os.path.join(file_path, "../configs/sidechain/witness/template")


class RippledServer(object):
    def __init__(self, rippled_server):
        self.rippled_server = "http://{}".format(rippled_server)

    def execute_transaction(self, payload, method="submit", verbose=False):
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
                if self.is_transaction_validated(response_result) and verbose:
                    print("  Transaction validated!")

        except requests.exceptions.RequestException as e:
            print("Failed to establish connection to rippled")
            sys.exit(1)

        if verbose:
            print(response_result)

        if "engine_result_code" in response_result and response_result["engine_result_code"] != 0:
            print(response_result)
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

    def is_transaction_validated(self, response, engine_result="tesSUCCESS"):
        tx_id = response["tx_json"]["hash"]

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

    def get_account_objects(self, account_id, verbose=False):
        payload = {
            "tx_json": {
                "account": account_id
            },
        }
        return self.execute_transaction(payload=payload, method="account_objects", verbose=verbose)

    def wallet_propose(self, seed=None, key_type=DEFAULT_ACCOUNT_KEY_TYPE):
        payload = {
            "tx_json": {
                "ledger_index": "current",
                "key_type": key_type
            }
        }
        if seed:
            payload["tx_json"]["seed"] = seed
        return self.execute_transaction(payload=payload, method="wallet_propose")

    def get_account_credentials(self, seed=None, key_type=DEFAULT_ACCOUNT_KEY_TYPE):
        wallet = self.wallet_propose(seed=seed, key_type=key_type)
        return wallet["account_id"], wallet["master_seed"]

    def make_payment(self, source_account_id=GENESIS_ACCOUNT_ID, source_account_seed=GENESIS_ACCOUNT_SEED,
                     destination_account_id=None, amount_to_transfer=MIN_ACCOUNT_CREATE_AMOUNT, verbose=False):
        if destination_account_id:
            if verbose:
                print(f"Transfer {amount_to_transfer} from {destination_account_id} to {source_account_id}")
            payload = {
                "tx_json": {
                    "TransactionType": "Payment",
                    "Account": source_account_id,
                    "Destination": destination_account_id,
                    "Amount": amount_to_transfer,
                },
                "secret": source_account_seed
            }
            return self.execute_transaction(payload=payload, method="submit", verbose=verbose)
        else:
            raise Exception("  Destination account cannot be None")

    def create_signer_list(self, signing_keys, signer_weight=1, verbose=False):
        signer_entries = []
        if verbose:
            print(f"Signing Keys: {signing_keys}")
        for signer_key in signing_keys:
            signer_entry = {
                "SignerEntry": {
                    "Account": signer_key,
                    "SignerWeight": signer_weight
                }
            }
            signer_entries.append(signer_entry)
        if verbose:
            print(f"signerEntries: {signer_entries}")
        return signer_entries

    def set_signer_list(self, account_id, seed, signer_entries, signer_quorum, verbose=False):
        if verbose:
            print("Set signer list set")

        payload = {
            "tx_json": {
                "Flags": 0,
                "TransactionType": "SignerListSet",
                "Account": account_id,
                "SignerQuorum": int(signer_quorum),
                "SignerEntries": signer_entries,
            },
            "secret": seed
        }
        return self.execute_transaction(payload=payload, method="submit")

    def create_xchain_bridge(self, bridge, door_account_id, door_account_seed, verbose=False):
        if verbose:
            print("Create bridge")

        payload = {
            "tx_json": {
                "Account": door_account_id,
                "TransactionType": "XChainCreateBridge",
                "XChainBridge": bridge,
                "SignatureReward": SIGNATURE_REWARD,
                "MinAccountCreateAmount": MIN_ACCOUNT_CREATE_AMOUNT
            },
            "secret": door_account_seed
        }
        self.execute_transaction(payload=payload, method="submit", verbose=verbose)

        for account_object in self.get_account_objects(door_account_id)["account_objects"]:
            if account_object["LedgerEntryType"] == "Bridge" and account_object["XChainBridge"] == bridge:
                return
        print("  XChain bridge creation failed!")
        sys.exit(1)

    def xchain_transfer(self, source_account_id=GENESIS_ACCOUNT_ID, source_account_seed=GENESIS_ACCOUNT_SEED,
                        destination_account_id=None, amount_to_transfer=DEFAULT_TRANSFER_AMOUNT,
                        bridge=None, verbose=False):
        print("- XChain Transfer")
        if bridge and destination_account_id:
            if verbose:
                print(f"Transfer {amount_to_transfer} from {destination_account_id} to {source_account_id}")
            payload = {
                "tx_json": {
                    "Account": source_account_id,
                    "Destination": destination_account_id,
                    "TransactionType": "XChainAccountCreateCommit",
                    "Amount": amount_to_transfer,
                    "SignatureReward": SIGNATURE_REWARD,
                    "XChainBridge": bridge
                },
                "secret": source_account_seed
            }
            return self.execute_transaction(payload=payload, method="submit", verbose=verbose)
        else:
            raise Exception("  bridge cannot be None")

    def get_account_balance(self, account_id):
        payload = {
            "tx_json": {
                "account": account_id,
                "ledger_index": "current",
                "strict": True,
                "queue": True
            }
        }

        count = 1
        max_retries = 10
        while count <= max_retries:
            account_info = self.execute_transaction(payload=payload, method="account_info")
            try:
                return int(account_info['account_data']['Balance'])
            except KeyError as e:
                count += 1
                time.sleep(2)
        return 0

    def disable_master_key_pair(self, key=GENESIS_ACCOUNT_ID, seed=GENESIS_ACCOUNT_SEED, verbose=False):
        if verbose:
            print("Disable Issuing chain Master key: {key}")

        payload = {
            "tx_json": {
                "TransactionType": "AccountSet",
                "Account": key,
                "SetFlag": 4
            },
            "secret": seed
        }
        return self.execute_transaction(payload=payload, method="submit", verbose=verbose)


def generate_witness_configs(rippled, bridge, witness_configs_dir):
    print("  Generate witness configs")
    signing_keys = []
    base_witness_rpc_endpoint_port = 6010

    file_loader = FileSystemLoader(WITNESS_CONFIG_TEMPLATE_DIR)
    env = Environment(loader=file_loader)
    template = env.get_template('witness.template')
    for count in range(1, NO_OF_WITNESS_SERVERS + 1):
        witness_name = f"witness{count:02d}"
        key, seed = rippled.get_account_credentials(key_type=WITNESS_SIGNING_KEY_KEY)
        locking_chain = {
            "Endpoint": {
                "Host": "rippled_1",
                "Port": "6006"
            },
            "TxnSubmit": {
                "SigningKeySeed": seed,
                "SigningKeyType": WITNESS_SIGNING_KEY_KEY,
                "SubmittingAccount": key
            },
            "RewardAccount": key
        }

        issuing_chain = {
            "Endpoint": {
                "Host": "rippled_3",
                "Port": "6006"
            },
            "TxnSubmit": {
                "SigningKeySeed": seed,
                "SigningKeyType": WITNESS_SIGNING_KEY_KEY,
                "SubmittingAccount": key
            },
            "RewardAccount": key
        }
        rpc_endpoint = {
            "Port": base_witness_rpc_endpoint_port + count
        }

        signing_key, signing_key_seed = rippled.get_account_credentials(key_type=WITNESS_SIGNING_KEY_KEY)
        signing_keys.append(signing_key)
        json_bridge = json.dumps(bridge, indent=2)

        content = template.render(locking_chain=locking_chain,
                                  issuing_chain=issuing_chain,
                                  rpc_endpoint=rpc_endpoint,
                                  witness_name=witness_name,
                                  xchain_bridge=json_bridge,
                                  signing_key_seed=signing_key_seed,
                                  signing_key_type=WITNESS_SIGNING_KEY_KEY)

        if not os.path.exists(witness_configs_dir):
            os.mkdir(witness_configs_dir)
        witness_config_file = os.path.join(witness_configs_dir, f"{witness_name}.json")
        with open(witness_config_file, mode="w") as output:
            output.write(content)

    return signing_keys


def setup_sidechain(locking_chain, issuing_chain, witness_configs_dir):
    print("- Setup Sidechain")
    locking_chain_door_account_id, locking_chain_door_seed = locking_chain.get_account_credentials()
    bridge = {
        "LockingChainDoor": locking_chain_door_account_id,
        "LockingChainIssue": SIDECHAIN_BRIDGE_CURRENCY_XRP,
        "IssuingChainDoor": GENESIS_ACCOUNT_ID,
        "IssuingChainIssue": SIDECHAIN_BRIDGE_CURRENCY_XRP
    }
    signing_keys = generate_witness_configs(rippled=locking_chain, bridge=bridge, witness_configs_dir=witness_configs_dir)

    locking_chain_submitting_account_ids = []
    issuing_chain_submitting_account_ids = []
    locking_chain_door_account_id = None

    witness_config_files = glob.glob(os.path.join(witness_configs_dir, 'witness*.json'))
    no_of_witnesses = 0
    for witness_config_filename in witness_config_files:
        no_of_witnesses += 1
        witness_config_file = f"{witness_config_filename}"

        with open(witness_config_file, "r") as fp:
            witness_data = json.load(fp)

        locking_chain_submitting_account_ids.append(witness_data["LockingChain"]["TxnSubmit"]["SubmittingAccount"])
        issuing_chain_submitting_account_ids.append(witness_data["IssuingChain"]["TxnSubmit"]["SubmittingAccount"])
        locking_chain_door_account_id = witness_data["XChainBridge"]["LockingChainDoor"]

    print(f"  Create Locking Chain Door account: {locking_chain_door_account_id}")
    locking_chain.make_payment(destination_account_id=locking_chain_door_account_id)

    print("  Create Locking Chain Submission accounts")
    for locking_chain_submitting_account_id in locking_chain_submitting_account_ids:
        locking_chain.make_payment(destination_account_id=locking_chain_submitting_account_id)

    print("  Create Issuing Chain Submission accounts")
    for issuing_chain_submitting_account_id in issuing_chain_submitting_account_ids:
        issuing_chain.make_payment(destination_account_id=issuing_chain_submitting_account_id)

    print("  Create SignerList")
    signer_entries = locking_chain.create_signer_list(signing_keys)
    locking_chain.set_signer_list(account_id=locking_chain_door_account_id, seed=locking_chain_door_seed,
                                  signer_entries=signer_entries, signer_quorum=WITNESS_QUORUM * no_of_witnesses)
    issuing_chain.set_signer_list(account_id=GENESIS_ACCOUNT_ID, seed=GENESIS_ACCOUNT_SEED,
                                  signer_entries=signer_entries, signer_quorum=WITNESS_QUORUM * no_of_witnesses)

    print("  Create XChain bridge")
    locking_chain.create_xchain_bridge(bridge, locking_chain_door_account_id, locking_chain_door_seed)
    issuing_chain.create_xchain_bridge(bridge, GENESIS_ACCOUNT_ID, GENESIS_ACCOUNT_SEED)

    print(f"  Disable issuing chain master key pair: {GENESIS_ACCOUNT_ID}")
    issuing_chain.disable_master_key_pair(key=GENESIS_ACCOUNT_ID, seed=GENESIS_ACCOUNT_SEED)


def xchain_transfer(locking_chain, issuing_chain, witness_configs_dir):
    witness_config_files = glob.glob(os.path.join(witness_configs_dir, 'witness*.json'))

    for witness_config_filename in witness_config_files:
        witness_config_file = f"{witness_config_filename}"

        with open(witness_config_file, "r") as fp:
            witness_data = json.load(fp)
            xchain_bridge = witness_data["XChainBridge"]
            break

    current_balance = issuing_chain.get_account_balance(account_id=DESTINATION_ACCOUNT_ID)
    locking_chain.xchain_transfer(bridge=xchain_bridge, destination_account_id=DESTINATION_ACCOUNT_ID,
                                  amount_to_transfer=ISSUING_CHAIN_MASTER_ACCOUNT_DEFAULT_BALANCE)
    if issuing_chain.get_account_balance(account_id=DESTINATION_ACCOUNT_ID) != \
            current_balance + int(ISSUING_CHAIN_MASTER_ACCOUNT_DEFAULT_BALANCE):
        print("  XChain Transfer failed")
        sys.exit(1)
    print(f"  Account {DESTINATION_ACCOUNT_ID} balance: {issuing_chain.get_account_balance(account_id=DESTINATION_ACCOUNT_ID)}")


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--lockingChain', default=DEFAULT_LOCKING_SERVER_ENDPOINT,
                        help="Locking chain RPC endpoint (default: {})".format(DEFAULT_LOCKING_SERVER_ENDPOINT))
    parser.add_argument('--issuingChain', default=DEFAULT_ISSUING_SERVER_ENDPOINT,
                        help="Issuing chain RPC endpoint (default: {})".format(DEFAULT_ISSUING_SERVER_ENDPOINT))
    parser.add_argument("--witnessConfigDir", required=True,
                        help="Path to witness configs directory")
    parser.add_argument("--xChainTransfer", help="Submit a XChain Transfer", action='store_true')

    return parser.parse_args()


def main(locking_chain_end_point, issuing_chain_end_point, witness_configs_dir, submit_xchain_transfer):
    locking_chain = RippledServer(locking_chain_end_point)
    issuing_chain = RippledServer(issuing_chain_end_point)
    if submit_xchain_transfer:
        xchain_transfer(locking_chain, issuing_chain, witness_configs_dir)
    else:
        setup_sidechain(locking_chain, issuing_chain, witness_configs_dir)


if __name__ == '__main__':
    cmd_args = parse_arguments()
    main(cmd_args.lockingChain, cmd_args.issuingChain, cmd_args.witnessConfigDir, cmd_args.xChainTransfer)
