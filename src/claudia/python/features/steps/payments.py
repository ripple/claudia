from behave import *
from claudia.python.lib.framework.common import *
from claudia.python.lib.framework.object_factory import ObjFactory, ObjType
from xrpl.account import get_balance
from xrpl.models import IssuedCurrencyAmount, DepositPreauth, AccountSet, AccountSetAsfFlag
from xrpl.models.requests import Tx
from xrpl.transaction import submit


@when('we send a payment of "{transfer_amount}" XRP from Alice to Bob')
def step_impl(context, transfer_amount):
    try:
        context.transferAmount = float(transfer_amount) if '.' in transfer_amount else int(transfer_amount)
        context.payment = ObjFactory.getObj(
            ObjType.payment,
            account=context.sourceAddress,
            destination=context.destinationAddress,
            amount=str(context.transferAmount)
        )
        context.payment_response = submit_and_wait(context.payment, context.client, context.sourceWallet)
        context.response = context.client.request(Tx(transaction=context.payment_response.result["hash"]))
    except Exception as e:
        context.exception = e
        context.test_status = "failed"


@when('we send a payment of "{transfer_amount}" XRP from Alice to self')
def step_impl(context, transfer_amount):
    try:
        context.transferAmount = int(transfer_amount)
        context.payment = ObjFactory.getObj(
            ObjType.payment,
            account=context.sourceAddress,
            destination=context.sourceAddress,
            amount=str(context.transferAmount)
        )
        context.payment_response = submit_and_wait(context.payment, context.client, context.sourceWallet)
        context.response = context.client.request(Tx(transaction=context.payment_response.result["hash"]))
    except Exception as e:
        context.exception = e
        context.test_status = "failed"


@when('we only submit a payment of "{transfer_amount}" XRP from Alice to Bob')
def step_impl(context, transfer_amount):
    try:
        context.transferAmount = int(transfer_amount)
        context.payment = ObjFactory.getObj(
            ObjType.payment,
            account=context.sourceAddress,
            destination=context.destinationAddress,
            amount=str(context.transferAmount)
        )
        context.signed_payment_tx = submit(context.payment, context.sourceWallet)
    except Exception as e:
        context.exception = e
        context.test_status = "failed"


@when('we send a payment with amount greater than balance from Alice to Bob')
def step_impl(context):
    try:
        context.transferAmount = get_balance(context.sourceAddress, context.client) + 1
        context.payment = ObjFactory.getObj(
            ObjType.payment,
            account=context.sourceAddress,
            destination=context.destinationAddress,
            amount=str(context.transferAmount)
        )

        context.payment_response = submit_and_wait(context.payment, context.client, context.sourceWallet)
        context.response = context.client.request(Tx(transaction=context.payment_response.result["hash"]))
    except Exception as e:
        context.exception = e
        context.test_status = "failed"


@when('we send a payment of "{transfer_amount}" XRP from Alice to Invalid')
def step_impl(context, transfer_amount):
    try:
        context.transferAmount = int(transfer_amount)
        context.payment = ObjFactory.getObj(
            ObjType.payment,
            account=context.sourceAddress,
            destination=context.invalidAddress,
            amount=str(context.transferAmount)
        )

        context.payment_response = submit_and_wait(context.payment, context.client, context.sourceWallet)
        context.response = context.client.request(Tx(transaction=context.payment_response.result["hash"]))
    except Exception as e:
        context.exception = e
        context.test_status = "failed"


@when('we send a payment of "{transfer_amount}" XRP to Bob without providing source information')
def step_impl(context, transfer_amount):
    try:
        context.transferAmount = int(transfer_amount)
        context.payment = ObjFactory.getObj(
            ObjType.payment,
            account=context.sourceAddress,
            destination=context.destinationAddress,
            amount=str(context.transferAmount)
        )
        context.payment_response = submit_and_wait(context.payment, context.client, "")
        context.response = context.client.request(Tx(transaction=context.payment_response.result["hash"]))
    except Exception as e:
        context.exception = e
        context.test_status = "failed"


@when('we send a payment of "{transfer_amount}" XRP from Alice without providing destination information')
def step_impl(context, transfer_amount):
    try:
        context.transferAmount = int(transfer_amount)
        context.payment = ObjFactory.getObj(
            ObjType.payment,
            account=context.sourceAddress,
            destination=context.destinationAddress,
            amount=str(context.transferAmount)
        )

        context.payment_response = submit_and_wait(context.payment, context.client, context.sourceWallet)
        context.response = context.client.request(Tx(transaction=context.payment_response.result["hash"]))
    except Exception as e:
        context.exception = e
        context.test_status = "failed"


@when('we send a payment of "{transfer_amount_in_usd}" USD from Alice to Bob')
def step_impl(context, transfer_amount_in_usd):
    try:
        context.transferAmount = IssuedCurrencyAmount(
            currency="USD",
            value=str(transfer_amount_in_usd),
            issuer="rf1BiGeXwwQoi8Z2ueFYTEXSwuJYfV2Jpn"
        )

        context.payment = ObjFactory.getObj(
            ObjType.payment,
            account=context.sourceAddress,
            destination=context.destinationAddress,
            amount=context.transferAmount
        )

        context.payment_response = submit_and_wait(context.payment, context.client, context.sourceWallet)
        context.response = context.client.request(Tx(transaction=context.payment_response.result["hash"]))
    except Exception as e:
        context.exception = e
        context.test_status = "failed"


@when('we send a payment of "{transfer_amount}" XRP with destination tag "{destination_tag}" info from Alice to Bob')
def step_impl(context, transfer_amount, destination_tag):
    try:
        context.transferAmount = int(transfer_amount)
        context.payment = ObjFactory.getObj(
            ObjType.payment,
            account=context.sourceAddress,
            destination=context.destinationAddress,
            destination_tag=int(destination_tag),
            amount=str(context.transferAmount)
        )

        context.payment_response = submit_and_wait(context.payment, context.client, context.sourceWallet)
        context.response = context.client.request(Tx(transaction=context.payment_response.result["hash"]))
    except Exception as e:
        context.exception = e
        context.test_status = "failed"


@when('we send a payment of "{transfer_amount}" XRP with invoice id "{invoice_id}" from Alice to Bob')
def step_impl(context, transfer_amount, invoice_id):
    try:
        context.transferAmount = int(transfer_amount)
        context.payment = ObjFactory.getObj(
            ObjType.payment,
            account=context.sourceAddress,
            destination=context.destinationAddress,
            invoice_id=invoice_id,
            amount=str(context.transferAmount)
        )

        context.payment_response = submit_and_wait(context.payment, context.client, context.sourceWallet)
        context.response = context.client.request(Tx(transaction=context.payment_response.result["hash"]))
    except Exception as e:
        context.exception = e
        context.test_status = "failed"


@when('we send a payment of "{transfer_amount}" XRP from Alice as a preauth account to Bob')
def step_impl(context, transfer_amount):
    try:
        context.transferAmount = int(transfer_amount)

        account_set_tx = AccountSet(
            account=context.destinationAddress,
            set_flag=AccountSetAsfFlag.ASF_DEPOSIT_AUTH,
        )

        submit_and_wait(account_set_tx, context.client, context.destinationWallet)

        deposit_pre_auth_tx = DepositPreauth(
            account=context.destinationAddress,
            sequence=get_account_sequence(context.client, context.destinationAddress),
            authorize=context.sourceAddress,
            fee=str(context.minDrop)
        )
        submit_and_wait(deposit_pre_auth_tx, context.client, context.destinationWallet)
        context.destinationBalance = get_balance(context.destinationAddress, context.client)
        context.payment = ObjFactory.getObj(
            ObjType.payment,
            account=context.sourceAddress,
            destination=context.destinationAddress,
            amount=str(context.transferAmount)
        )

        context.payment_response = submit_and_wait(context.payment, context.client, context.sourceWallet)
        context.response = context.client.request(Tx(transaction=context.payment_response.result["hash"]))
    except Exception as e:
        context.exception = e
        context.test_status = "failed"


@when('we send a payment of "{transfer_amount}" XRP from Alice as a non-preauth account to Bob')
def step_impl(context, transfer_amount):
    try:
        context.transferAmount = int(transfer_amount)
        account_set_tx = AccountSet(
            account=context.destinationAddress,
            set_flag=AccountSetAsfFlag.ASF_DEPOSIT_AUTH,
        )

        submit_and_wait(account_set_tx, context.client, context.destinationWallet)

        context.destinationBalance = get_balance(context.destinationAddress, context.client)
        context.payment = ObjFactory.getObj(
            ObjType.payment,
            account=context.sourceAddress,
            destination=context.destinationAddress,
            amount=str(context.transferAmount)
        )
        context.payment_response = submit_and_wait(context.payment, context.client, context.sourceWallet)
        context.response = context.client.request(Tx(transaction=context.payment_response.result["hash"]))
    except Exception as e:
        context.exception = e
        context.test_status = "failed"


@then('the balances after a valid payment are correct')
def step_impl(context):
    verify_payment_account_objects(context, context.response)
    verify_account_balance(get_account_balance(context, context.sourceAddress),
                           (context.sourceBalance - context.transferAmount - context.minDrop))
    verify_account_balance(get_account_balance(context, context.destinationAddress), (
            context.destinationBalance + context.transferAmount))


@then('the balances are correct in submit only mode')
def step_impl(context):
    verify_account_balance(get_account_balance(context, context.sourceAddress), (context.sourceBalance))
    verify_account_balance(get_account_balance(context, context.destinationAddress), (context.destinationBalance))


@then('the self-payment should fail')
def step_impl(context):
    verify_test_status(context.test_status, "failed")
    verify_test_error_message(str(context.exception),
                              "An XRP payment transaction cannot have the same sender and destination.")
    verify_account_balance(get_account_balance(context, context.sourceAddress), context.sourceBalance)


@then('the payment with amount greater than balance should fail')
def step_impl(context):
    verify_test_status(context.test_status, "failed")
    verify_test_error_message(str(context.exception),
                              "Transaction failed: tecUNFUNDED_PAYMENT")

    verify_account_balance(get_account_balance(context, context.sourceAddress),
                           (context.sourceBalance - context.minDrop))
    verify_account_balance(get_account_balance(context, context.destinationAddress), context.destinationBalance)


@then('the payment with invalid destination should fail')
def step_impl(context):
    verify_test_status(context.test_status, "failed")
    verify_test_error_message(str(context.exception),
                              "Invalid value to construct an AccountID: expected valid classic address or "
                              "X-Address, received str.")
    verify_account_balance(get_account_balance(context, context.sourceAddress), context.sourceBalance)


@then('the payment with zero amount should fail')
def step_impl(context):
    verify_test_status(context.test_status, "failed")
    verify_test_error_message(str(context.exception), "Can only send positive amounts.")
    verify_account_balance(get_account_balance(context, context.sourceAddress), context.sourceBalance)
    verify_account_balance(get_account_balance(context, context.destinationAddress), context.destinationBalance)


@then('the payment with decimal amount should fail')
def step_impl(context):
    verify_test_status(context.test_status, "failed")
    verify_test_error_message(str(context.exception), "Error processing Amount: 10.5 is an invalid XRP amount.")
    verify_account_balance(get_account_balance(context, context.sourceAddress), context.sourceBalance)
    verify_account_balance(get_account_balance(context, context.destinationAddress), context.destinationBalance)


@then('the payment without source information should fail')
def step_impl(context):
    verify_test_status(context.test_status, "failed")
    verify_test_error_message(str(context.exception), "Wallet must be provided when submitting an unsigned transaction")
    verify_account_balance(get_account_balance(context, context.destinationAddress), context.destinationBalance)


@then('the payment without destination information should fail')
def step_impl(context):
    verify_test_status(context.test_status, "failed")
    verify_test_error_message(str(context.exception), "Destination not specified.")
    verify_account_balance(get_account_balance(context, context.sourceAddress), context.sourceBalance)


@then('the payment of 10 million XRP should fail')
def step_impl(context):
    verify_account_balance(get_account_balance(context, context.sourceAddress),
                           (context.sourceBalance - context.minDrop))
    verify_account_balance(get_account_balance(context, context.destinationAddress), context.destinationBalance)


@then('the balances after a non-xrp payment are correct')
def step_impl(context):
    verify_test_status(context.test_status, "failed")
    verify_test_error_message(str(context.exception), "Transaction failed: tecPATH_DRY")
    verify_account_balance(get_account_balance(context, context.sourceAddress),
                           (context.sourceBalance - context.minDrop))
    verify_account_balance(get_account_balance(context, context.destinationAddress), context.destinationBalance)


@then('the balances after a payment with destination tag info are correct')
def step_impl(context):
    verify_payment_account_objects(context, context.response)
    verify_account_balance(get_account_balance(context, context.sourceAddress), (
            context.sourceBalance - context.transferAmount - context.minDrop))
    verify_account_balance(get_account_balance(context, context.destinationAddress),
                           (context.destinationBalance + context.transferAmount))


@then('the balances after a payment with invoice id info are correct')
def step_impl(context):
    verify_payment_account_objects(context, context.response)
    verify_account_balance(get_account_balance(context, context.sourceAddress),
                           (context.sourceBalance - context.transferAmount - context.minDrop))
    verify_account_balance(get_account_balance(context, context.destinationAddress),
                           (context.destinationBalance + context.transferAmount))


@then('the balances after a payment with invalid invoice id info are correct')
def step_impl(context):
    verify_test_status(context.test_status, "failed")
    verify_test_error_message(str(context.exception), "non-hexadecimal number found in fromhex() arg at position 3")
    verify_account_balance(get_account_balance(context, context.sourceAddress), context.sourceBalance)
    verify_account_balance(get_account_balance(context, context.destinationAddress), context.destinationBalance)


@then('the balances after a payment from preauth account are correct')
def step_impl(context):
    verify_payment_account_objects(context, context.response)
    verify_account_balance(get_account_balance(context, context.sourceAddress),
                           (context.sourceBalance - context.transferAmount - context.minDrop))
    verify_account_balance(get_account_balance(context, context.destinationAddress),
                           (context.destinationBalance + context.transferAmount))


@then('the balances after a payment from non-preauth account are correct')
def step_impl(context):
    verify_test_status(context.test_status, "failed")
    verify_test_error_message(str(context.exception), "Transaction failed: tecNO_PERMISSION")
    verify_account_balance(get_account_balance(context, context.sourceAddress),
                           (context.sourceBalance - context.minDrop))
    verify_account_balance(get_account_balance(context, context.destinationAddress), context.destinationBalance)
