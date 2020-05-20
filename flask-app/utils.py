import json
from json.decoder import JSONDecodeError


def get_balance(expenses):
    group_balance = dict()
    for expense in expenses:
        debt = round(expense['amount']/len(expense['for_whom']), 2)
        for debitor in expense['for_whom']:
            try:
                group_balance[debitor['username']] -= debt
            except KeyError:
                group_balance[debitor['username']] = -debt
        creditor = expense['who_paid']['username']
        credit = expense['amount']
        group_balance[creditor] += credit

    return group_balance


def generate_list_payments(dict_balance):
    payments = []
    ls_balance = []
    for tuple in dict_balance.items():
        ls_balance.append(list(tuple))

    ls_balance.sort(key=lambda x: x[1], reverse = True)

    while True:
        creditor = ls_balance.pop(0)
        debitor = ls_balance.pop()

        if abs(creditor[1]) > abs(debitor[1]):
            creditor[1]  += debitor[1]
            payments.append({'from_who': debitor[0], 'to_whom': creditor[0], 'amount': -round(debitor[1], 2) })
            ls_balance.append(creditor)

        elif abs(creditor[1]) == abs(debitor[1]) :
            payments.append({'from_who': debitor[0], 'to_whom': creditor[0], 'amount': -round(debitor[1], 2) })
        else:
            debitor[1]  += creditor[1]
            payments.append({'from_who': debitor[0], 'to_whom': creditor[0], 'amount': round(creditor[1], 2) })
            ls_balance.append(debitor)

        if len(list(filter(lambda x: x[1] < 0.5, ls_balance))) == len(ls_balance):
            break

        ls_balance.sort(key=lambda x: x[1], reverse = True)

    return payments
