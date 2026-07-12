from dataclasses import dataclass
from typing import Dict


@dataclass
class User:
    name: str
    discord_id: str

    def __hash__(self):
        return hash(self.discord_id)

@dataclass
class Tag:
    name: str
    users: list[User]
    # board: Board

@dataclass
class UserForGroupTransaction:
    userFrom: User
    tagTo: Tag
    value: int # in cents
    # board: Board

@dataclass
class UserToUserTransaction:
    userFrom: User
    userTo:   User
    value: int # in cents
    completed: bool = False
    # board: Board



def compute_net_account(user_to_group: list[UserForGroupTransaction], user_to_user: list[UserToUserTransaction]) -> Dict[User, int]:
    net_accounts: Dict[User, int] = {}

    for elt in user_to_group:
        n = len(elt.tagTo.users)
        share = elt.value // n
        remainder = elt.value % n
        non_payers = [u for u in elt.tagTo.users if u != elt.userFrom]
        last_non_payer = non_payers[-1]
        for user in elt.tagTo.users:
            if user not in net_accounts:
                net_accounts[user] = 0
            if user == elt.userFrom:
                net_accounts[user] -= elt.value - share
            elif user == last_non_payer:
                net_accounts[user] += share + remainder
            else:
                net_accounts[user] += share

    for elt in filter(lambda t: t.completed, user_to_user):
        if elt.userFrom not in net_accounts:
            net_accounts[elt.userFrom] = 0
        if elt.userTo not in net_accounts:
            net_accounts[elt.userTo] = 0
        net_accounts[elt.userFrom] -= elt.value
        net_accounts[elt.userTo] += elt.value

    return net_accounts


def solve(net_accounts: Dict[User, int]) -> list[UserToUserTransaction]:
    transactions = []

    while any(v != 0 for v in net_accounts.values()):
        max_debitor = max(net_accounts, key=lambda u: (net_accounts[u], u.discord_id))   # owes the most (positive)
        max_creditor = min(net_accounts, key=lambda u: (net_accounts[u], u.discord_id))  # is owed the most (negative)

        amount = min(net_accounts[max_debitor], abs(net_accounts[max_creditor]))
        net_accounts[max_debitor] -= amount
        net_accounts[max_creditor] += amount

        transactions.append(UserToUserTransaction(
            userFrom=max_debitor,
            userTo=max_creditor,
            value=amount,
        ))

    return transactions

