import streamlit as st
from claudia.claudia import set_python_launch_vars
from claudia.python.features.environment import get_client, get_test_genesis_wallet
from claudia.python.lib.framework import constants
from claudia.python.lib.framework.common import send_payment, ResponseCode, get_account_balance, read_env_var, \
    sign_autofill_and_submit, get_nft_tokens, get_token_offers_response
from claudia.python.lib.framework.object_factory import ObjFactory, ObjType
from xrpl import CryptoAlgorithm
from xrpl.ledger import get_fee
from xrpl.wallet import Wallet


class Context(object):
    connectionType = None
    url = None
    client = None
    algorithm = None
    test_genesis_wallet = None
    default_fee = None
    minDrop = None
    transferAmount = None
    exception = None
    test_status = None


def init_context():
    try:
        context = Context()
        context.connectionType = read_env_var('CONNECTION_TYPE')
        connectionScheme = read_env_var('CONNECTION_SCHEME')
        connectionURL = read_env_var('CONNECTION_URL')
        context.url = "{}://{}".format(connectionScheme, connectionURL)
        try:
            context.client = get_client(context)
        except ConnectionRefusedError:
            raise Exception(f"ERROR: Cannot connect to {context.url}. Make sure the network is accessible.")
        context.algorithm = CryptoAlgorithm.SECP256K1
        context.test_genesis_wallet = get_test_genesis_wallet(context)
        context.default_fee = int(get_fee(context.client))
        context.minDrop = context.default_fee
        context.transferAmount = constants.DEFAULT_TRANSFER_AMOUNT
        context.exception = None
        context.test_status = None
        return context
    except Exception as e:
        st.error(f"An unexpected error has occurred. Details: \n{e}")
        raise e


def verify_network(context):
    if not context.client.is_open():
        st.error("Network is not accessible!")
        raise Exception("Network is not accessible!")


def create_wallet(context):
    try:
        wallet = Wallet.create(algorithm=context.algorithm)
        return wallet
    except Exception as e:
        return f"An unexpected error has occurred. Details: \n{e}"


def fund_wallet(context, wallet, fund_amount=constants.DEFAULT_ACCOUNT_FUND_AMOUNT):
    try:
        response = send_payment(
            context,
            source_wallet=context.test_genesis_wallet,
            destination_wallet=wallet,
            amount=fund_amount
        )
        return response
    except Exception as e:
        return f"An unexpected error has occurred. Details: \n{e}"


def verify_funding(response):
    try:
        if ResponseCode.success not in str(response):
            raise Exception(
                "Expected response code was not received."
                "\nExpected Code = '{}'."
                "\nResponse received: '{}'".format(ResponseCode.success, response)
            )
    except Exception as e:
        return f"An unexpected error has occurred. Details: \n{e}"


def get_create_account_summary(context, wallet):
    return f"- Workflow Summary:" \
           f"\n   - Wallet Address: {wallet.classic_address}" \
           f"\n   - Wallet Seed: {wallet.seed}" \
           f"\n   - Wallet Funds: {str(get_account_balance(context, wallet.classic_address))}" \
           f"\n   - Source Wallet Address: {context.test_genesis_wallet.classic_address}"


def get_send_payment_summary(context, source_wallet, destination_wallet, initial_source_balance,
                             initial_destination_balance):
    return f"- Workflow Summary:" \
           f"\n   - Source Wallet Address: {source_wallet.classic_address}" \
           f"\n   - Source Wallet Seed: {source_wallet.seed}" \
           f"\n   - Source Wallet Initial Balance: {initial_source_balance}" \
           f"\n   - Source Wallet Current Balance: {str(get_account_balance(context, source_wallet.classic_address))}" \
           f"\n   - Destination Wallet Address: {destination_wallet.classic_address}" \
           f"\n   - Destination Wallet Seed: {destination_wallet.seed}" \
           f"\n   - Destination Wallet Initial Balance: {initial_destination_balance}" \
           f"\n   - Destination Wallet Current Balance: {str(get_account_balance(context, destination_wallet.classic_address))}"


def get_nft_minting_summary(context, owner_address, owner_seed, nftoken):
    return f" - Workflow Summary:" \
           f"\n    - Owner Wallet Address: {owner_address}" \
           f"\n    - Owner Wallet Seed: {owner_seed}" \
           f"\n    - Minted NFT ID: {nftoken}"


def get_nft_burning_summary(owner_address,
                            owner_seed,
                            nft_id,
                            initial_owner_nft_count,
                            owner_nft_count_post_burning):
    return f"- Workflow Summary:" \
           f"\n   - Owner Wallet Address: {owner_address}" \
           f"\n   - Owner Wallet Seed: {owner_seed}" \
           f"\n   - Burnt NFT ID: {nft_id}" \
           f"\n   - Owner Wallet NFT Count before burning: {initial_owner_nft_count}" \
           f"\n   - Owner Wallet NFT Count after burning: {owner_nft_count_post_burning}"


def get_create_buy_offer_summary(
        owner_address,
        owner_seed,
        buyer_address,
        buyer_seed,
        nft_id,
        offer_id
):
    return f"- Workflow Summary:" \
           f"\n   - Owner Wallet Address: {owner_address}" \
           f"\n   - Owner Wallet Seed: {owner_seed}" \
           f"\n   - Buyer Wallet Address: {buyer_address}" \
           f"\n   - Buyer Wallet Seed: {buyer_seed}" \
           f"\n   - Minted NFT ID: {nft_id}" \
           f"\n   - Created Offer ID: {offer_id}"


def get_accept_buy_offer_summary(
        owner_address,
        owner_seed,
        offer_id
):
    return f"- Workflow Summary:" \
           f"\n   - Owner Wallet Address: {owner_address}" \
           f"\n   - Owner Wallet Seed: {owner_seed}" \
           f"\n   - Accepted Buy Offer ID: {offer_id}"


def get_create_sell_offer_summary(
        owner_address,
        owner_seed,
        nft_id,
        offer_id
):
    return f"- Workflow Summary:" \
           f"\n   - Owner Wallet Address: {owner_address}" \
           f"\n   - Owner Wallet Seed: {owner_seed}" \
           f"\n   - Minted NFT ID: {nft_id}" \
           f"\n   - Created Offer ID: {offer_id}"


def get_accept_sell_offer_summary(
        buyer_address,
        buyer_seed,
        offer_id
):
    return f"- Workflow Summary:" \
           f"\n   - Buyer Wallet Address: {buyer_address}" \
           f"\n   - Buyer Wallet Seed: {buyer_seed}" \
           f"\n   - Accepted Sell Offer ID: {offer_id}"


def propose_or_get_wallet(context, seed=""):
    if seed == "":
        wallet = Wallet.create(algorithm=context.algorithm)
        send_payment(context,
                     source_wallet=context.test_genesis_wallet,
                     destination_wallet=wallet,
                     amount=constants.DEFAULT_ACCOUNT_FUND_AMOUNT)
    else:
        wallet = Wallet.from_seed(seed=seed, algorithm=context.algorithm)

    return wallet, wallet.seed


def ask_for_network():
    network = st.selectbox(
        'Choose Network',
        ('local-mainnet', 'devnet', 'testnet', 'local-sidechain'))
    yes_button = st.button(label='GO!')
    if yes_button:
        set_python_launch_vars(network, "websocket")
        return


def validate_input(key, value):
    if value == "" or value is None:
        error = f"{key} is a required field. Please try again..."
        st.error(error)
        raise Exception(error)


def create_account():
    network = st.selectbox(
        'Choose Network',
        ('local-mainnet', 'devnet', 'testnet', 'local-sidechain'))
    continue_button = st.button(label='Go!', use_container_width=True)
    if continue_button:
        with st.spinner(''):
            st.caption("Details")
            with st.container():
                st.text(" - Applying settings and verifying if the network is accessible")
                set_python_launch_vars(network, "websocket")
                context = init_context()
                verify_network(context)
                st.text(" - Proposing wallet")
                wallet = create_wallet(context)
                st.text(" - Funding wallet")
                response = fund_wallet(context, wallet)
                st.text(" - Verifying wallet funding")
                verify_funding(response)
                st.text('- Account created! 🎉')
                st.code(get_create_account_summary(context, wallet))


def send_payment_across_accounts():
    network = st.selectbox(
        'Choose Network',
        ('local-mainnet', 'devnet', 'testnet', 'local-sidechain'))

    with st.expander(" - OPTIONAL: Enter source wallet seed. If nothing is provided, Claudia will create one"):
        source_seed = st.text_input('Source Wallet Seed', type="password", key='source_seed_send_payment')

    with st.expander(" - OPTIONAL: Enter destination wallet seed. If nothing is provided, Claudia will create one"):
        destination_seed = st.text_input('Destination Wallet Seed', type="password",
                                         key='destination_seed_send_payment')

    with st.expander(" - OPTIONAL: Enter fund amount. If nothing is provided, Claudia will send 1000 drops"):
        fund_amount = st.text_input('Fund Amount in XRP drops', "1000", key='fund_send_payment')
    continue_button = st.button(label='Go!', use_container_width=True)
    if continue_button:
        with st.spinner(''):
            st.caption("Details")
            with st.container():
                st.text(" - Applying settings and verifying if the network is accessible")
                set_python_launch_vars(network, "websocket")
                context = init_context()
                verify_network(context)
                st.text(" - Getting the wallets ready")
                source_wallet, source_seed = propose_or_get_wallet(context, source_seed)
                destination_wallet, destination_seed = propose_or_get_wallet(context, destination_seed)
                initial_source_balance = get_account_balance(context, source_wallet.classic_address)
                initial_destination_balance = get_account_balance(context, source_wallet.classic_address)
                st.text(" - Sending payment")
                response = send_payment(
                    context,
                    source_wallet=source_wallet,
                    destination_wallet=destination_wallet,
                    amount=fund_amount
                )
                st.text(" - Verifying payment")
                verify_funding(response)
                st.text('- Payment was successful! 🎉')
                st.code(get_send_payment_summary(context,
                                                 source_wallet,
                                                 destination_wallet,
                                                 initial_source_balance,
                                                 initial_destination_balance), language='bash')


def mint_nft():
    network = st.selectbox(
        'Choose Network',
        ('local-mainnet', 'devnet', 'testnet', 'local-sidechain'))

    with st.expander(" - OPTIONAL: Enter owner wallet seed. If nothing is provided, Claudia will create one"):
        owner_seed = st.text_input('Owner Wallet Seed', type="password", key='owner_seed_mint')
    continue_button = st.button(label='Go!', use_container_width=True)
    if continue_button:
        with st.spinner(''):
            st.caption("Details")
            with st.container():
                st.text(" - Applying settings and verifying if the network is accessible")
                set_python_launch_vars(network, "websocket")
                context = init_context()
                verify_network(context)
                st.text(" - Getting the owner wallet ready")
                owner_wallet, owner_seed = propose_or_get_wallet(context, owner_seed)
                owner_address = owner_wallet.classic_address
                owner_seed = owner_wallet.seed
                st.text(" - Minting NFT")
                payload = ObjFactory.getObj(
                    ObjType.nft_token_mint,
                    account=owner_address,
                    nftoken_taxon=0,
                    flags=8
                )
                response = sign_autofill_and_submit(context.client, payload, owner_wallet)
                st.text(f" - Verifying if minting succeeded")
                if ResponseCode.success not in str(response):
                    raise Exception(
                        "Expected response code was not received."
                        "\nExpected Code = '{}'."
                        "\nResponse received: '{}'".format(ResponseCode.success, response)
                    )

                nftoken = get_nft_tokens(context.client, owner_address)[-1]
                st.text('- NFT Minting was successful! 🎉')
                st.code(
                    get_nft_minting_summary(
                        context,
                        owner_address,
                        owner_seed,
                        nftoken
                    ),
                    language='bash'
                )


def burn_nft():
    network = st.selectbox(
        'Choose Network',
        ('local-mainnet', 'devnet', 'testnet', 'local-sidechain'))

    owner_seed = st.text_input('REQUIRED: Owner Wallet Seed', type="password", key='owner_seed_burn')
    nft_id = st.text_input('REQUIRED: NFT ID', key='nft_burn')
    continue_button = st.button(label='Go!', use_container_width=True)
    if continue_button:
        validate_input("Owner Seed", owner_seed)
        validate_input("NFT ID", nft_id)
        with st.spinner(''):
            st.caption("Details")
            with st.container():
                st.text(" - Applying settings and verifying if the network is accessible")
                set_python_launch_vars(network, "websocket")
                context = init_context()
                verify_network(context)
                st.text(" - Getting the owner wallet ready")
                owner_wallet, owner_seed = propose_or_get_wallet(context, owner_seed)
                owner_address = owner_wallet.classic_address
                initial_owner_nft_count = len(get_nft_tokens(context.client, owner_address))
                st.text(" - Burning NFT")
                payload = ObjFactory.getObj(
                    ObjType.nft_token_burn,
                    account=owner_address,
                    nftoken_id=nft_id,
                )
                response = sign_autofill_and_submit(context.client, payload, owner_wallet)
                owner_nft_count_post_burning = len(get_nft_tokens(context.client, owner_address))

                st.text(f" - Verifying if burning succeeded")
                if ResponseCode.success not in str(response):
                    raise Exception(
                        "Expected response code was not received."
                        "\nExpected Code = '{}'."
                        "\nResponse received: '{}'".format(ResponseCode.success, response)
                    )

                st.text('- NFT Minting was successful! 🎉')
                st.code(
                    get_nft_burning_summary(
                        owner_address,
                        owner_seed,
                        nft_id,
                        initial_owner_nft_count,
                        owner_nft_count_post_burning
                    ),
                    language='bash'
                )


def create_nft_buy_offer():
    network = st.selectbox(
        'Choose Network',
        ('local-mainnet', 'devnet', 'testnet', 'local-sidechain'))

    owner_seed = st.text_input('REQUIRED: Owner Wallet Seed', type="password", key='owner_seed_create_buy')
    nft_id = st.text_input('REQUIRED: NFT ID', key='nft_create_buy')

    with st.expander(" - OPTIONAL: Enter buyer wallet seed. If nothing is provided, Claudia will create one"):
        buyer_seed = st.text_input('Buyer Wallet Seed', type="password", key='buyer_seed_create_buy')
    continue_button = st.button(label='Go!', use_container_width=True)
    if continue_button:
        validate_input("Owner Seed", owner_seed)
        validate_input("NFT ID", nft_id)
        with st.spinner(''):
            st.caption("Details")
            with st.container():
                st.text(" - Applying settings and verifying if the network is accessible")
                set_python_launch_vars(network, "websocket")
                context = init_context()
                verify_network(context)
                st.text(" - Getting the wallets ready")
                owner_wallet, owner_seed = propose_or_get_wallet(context, owner_seed)
                owner_address = owner_wallet.classic_address
                buyer_wallet, buyer_seed = propose_or_get_wallet(context, buyer_seed)
                buyer_address = buyer_wallet.classic_address
                st.text(f" - Creating a buy offer")
                payload = ObjFactory.getObj(
                    ObjType.nf_token_create_offer,
                    account=buyer_address,
                    owner=owner_address,
                    nftoken_id=nft_id,
                    amount=context.transferAmount
                )
                response = sign_autofill_and_submit(context.client, payload, buyer_wallet)

                st.text(f" - Verifying if offer creation succeeded")
                if ResponseCode.success not in str(response):
                    raise Exception(
                        "Expected response code was not received."
                        "\nExpected Code = '{}'."
                        "\nResponse received: '{}'".format(ResponseCode.success, response)
                    )

                offer_id = get_token_offers_response(context.client, buyer_address, token_id=nft_id)[0]
                st.text('- Creating NFT Buy Offer was successful! 🎉')
                st.code(
                    get_create_buy_offer_summary(
                        owner_address,
                        owner_seed,
                        buyer_address,
                        buyer_seed,
                        nft_id,
                        offer_id
                    ),
                    language='bash'
                )


def accept_nft_buy_offer():
    network = st.selectbox(
        'Choose Network',
        ('local-mainnet', 'devnet', 'testnet', 'local-sidechain'))

    owner_seed = st.text_input('REQUIRED: Owner Wallet Seed', type="password", key='owner_seed_accept_buy')
    offer_id = st.text_input('REQUIRED: Buy Offer ID', key='offer_accept_buy')

    continue_button = st.button(label='Go!', use_container_width=True)
    if continue_button:
        validate_input("Owner Seed", owner_seed)
        validate_input("Buy Offer ID", offer_id)
        with st.spinner(''):
            st.caption("Details")
            with st.container():
                st.text(" - Applying settings and verifying if the network is accessible")
                set_python_launch_vars(network, "websocket")
                context = init_context()
                verify_network(context)
                st.text(" - Getting the wallets ready")
                owner_wallet, owner_seed = propose_or_get_wallet(context, owner_seed)
                owner_address = owner_wallet.classic_address
                st.text(f" - Accepting a buy offer")
                payload = ObjFactory.getObj(
                    ObjType.nf_token_accept_offer,
                    account=owner_address,
                    nftoken_buy_offer=offer_id
                )
                response = sign_autofill_and_submit(context.client, payload, owner_wallet)

                st.text(f" - Verifying if offer creation succeeded")
                if ResponseCode.success not in str(response):
                    raise Exception(
                        "Expected response code was not received."
                        "\nExpected Code = '{}'."
                        "\nResponse received: '{}'".format(ResponseCode.success, response)
                    )
                st.text('- Creating NFT Buy Offer was successful! 🎉')
                st.code(
                    get_accept_buy_offer_summary(
                        owner_address,
                        owner_seed,
                        offer_id
                    ),
                    language='bash'
                )


def create_nft_sell_offer():
    network = st.selectbox(
        'Choose Network',
        ('local-mainnet', 'devnet', 'testnet', 'local-sidechain'))

    owner_seed = st.text_input('REQUIRED: Owner Wallet Seed', type="password", key='owner_seed_create_sell')
    nft_id = st.text_input('REQUIRED: NFT ID', key='nft_create_sell')
    continue_button = st.button(label='Go!', use_container_width=True)
    if continue_button:
        validate_input("Owner Seed", owner_seed)
        validate_input("NFT ID", nft_id)
        with st.spinner(''):
            st.caption("Details")
            with st.container():
                st.text(" - Applying settings and verifying if the network is accessible")
                set_python_launch_vars(network, "websocket")
                context = init_context()
                verify_network(context)
                st.text(" - Getting the wallets ready")
                owner_wallet, owner_seed = propose_or_get_wallet(context, owner_seed)
                owner_address = owner_wallet.classic_address
                st.text(f" - Creating a sell offer")
                payload = ObjFactory.getObj(
                    ObjType.nf_token_create_offer,
                    account=owner_address,
                    nftoken_id=nft_id,
                    amount=context.transferAmount,
                    flags=1
                )
                response = sign_autofill_and_submit(context.client, payload, owner_wallet)

                st.text(f" - Verifying if offer creation succeeded")
                if ResponseCode.success not in str(response):
                    raise Exception(
                        "Expected response code was not received."
                        "\nExpected Code = '{}'."
                        "\nResponse received: '{}'".format(ResponseCode.success, response)
                    )

                offer_id = get_token_offers_response(context.client, owner_address, token_id=nft_id)[0]

                st.text('- Creating NFT Sell Offer was successful! 🎉')
                st.code(
                    get_create_sell_offer_summary(
                        owner_address,
                        owner_seed,
                        nft_id,
                        offer_id
                    ),
                    language='bash'
                )


def accept_nft_sell_offer():
    network = st.selectbox(
        'Choose Network',
        ('local-mainnet', 'devnet', 'testnet', 'local-sidechain'))

    offer_id = st.text_input('REQUIRED: Sell Offer ID', key='offer_accept_sell')
    with st.expander(" - OPTIONAL: Enter buyer wallet seed. If nothing is provided, Claudia will create one"):
        buyer_seed = st.text_input('Buyer Wallet Seed', type="password", key='buyer_seed_accept_sell')

    continue_button = st.button(label='Go!', use_container_width=True)
    if continue_button:
        validate_input("Sell Offer ID", offer_id)
        with st.spinner(''):
            st.caption("Details")
            with st.container():
                st.text(" - Applying settings and verifying if the network is accessible")
                set_python_launch_vars(network, "websocket")
                context = init_context()
                verify_network(context)
                st.text(" - Getting the wallets ready")
                buyer_wallet, buyer_seed = propose_or_get_wallet(context, buyer_seed)
                buyer_address = buyer_wallet.classic_address
                st.text(f" - Accepting a sell offer")
                payload = ObjFactory.getObj(
                    ObjType.nf_token_accept_offer,
                    account=buyer_address,
                    nftoken_sell_offer=offer_id
                )
                response = sign_autofill_and_submit(context.client, payload, buyer_wallet)

                st.text(f" - Verifying if offer creation succeeded")
                if ResponseCode.success not in str(response):
                    raise Exception(
                        "Expected response code was not received."
                        "\nExpected Code = '{}'."
                        "\nResponse received: '{}'".format(ResponseCode.success, response)
                    )
                st.text('- Accepting NFT Sell Offer was successful! 🎉')
                st.code(
                    get_accept_sell_offer_summary(
                        buyer_address,
                        buyer_seed,
                        offer_id
                    ),
                    language='bash'
                )
