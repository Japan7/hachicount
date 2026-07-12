import pytest
from hachicount.solver import (
    User, Tag, UserForGroupTransaction, UserToUserTransaction,
    compute_net_account, solve,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def alice():
    return User(name="Alice", discord_id="001")

@pytest.fixture
def bob():
    return User(name="Bob", discord_id="002")

@pytest.fixture
def carol():
    return User(name="Carol", discord_id="003")

@pytest.fixture
def dave():
    return User(name="Dave", discord_id="004")

@pytest.fixture
def eve():
    return User(name="Eve", discord_id="005")

@pytest.fixture
def tag_all(alice, bob, carol):
    return Tag(name="all", users=[alice, bob, carol])

@pytest.fixture
def tag_ab(alice, bob):
    return Tag(name="ab", users=[alice, bob])

@pytest.fixture
def tag_bc(bob, carol):
    return Tag(name="bc", users=[bob, carol])


# ---------------------------------------------------------------------------
# compute_net_account — group transactions
# ---------------------------------------------------------------------------

def test_group_payer_is_owed_by_others(alice, bob, carol):
    tag = Tag(name="all", users=[alice, bob, carol])
    # Alice pays 900 for 3 people → share = 300 each
    txn = UserForGroupTransaction(userFrom=alice, tagTo=tag, value=900)
    net = compute_net_account([txn], [])

    assert net[alice] == -600   # paid 900, owes her own 300: net = -(900-300)
    assert net[bob]   == 300
    assert net[carol] == 300

def test_group_balances_sum_to_zero(alice, bob, carol):
    tag = Tag(name="all", users=[alice, bob, carol])
    txn = UserForGroupTransaction(userFrom=alice, tagTo=tag, value=1000)
    net = compute_net_account([txn], [])
    assert sum(net.values()) == 0

def test_group_two_people(alice, bob):
    tag = Tag(name="pair", users=[alice, bob])
    txn = UserForGroupTransaction(userFrom=alice, tagTo=tag, value=200)
    net = compute_net_account([txn], [])
    assert net[alice] == -100
    assert net[bob]   == 100

def test_multiple_group_transactions(alice, bob, carol):
    tag = Tag(name="all", users=[alice, bob, carol])
    t1 = UserForGroupTransaction(userFrom=alice, tagTo=tag, value=900)
    t2 = UserForGroupTransaction(userFrom=bob,   tagTo=tag, value=300)
    net = compute_net_account([t1, t2], [])
    # t1: alice=-600, bob=+300, carol=+300
    # t2: alice=+100, bob=-200, carol=+100
    assert net[alice] == -500
    assert net[bob]   == 100
    assert net[carol] == 400
    assert sum(net.values()) == 0


# ---------------------------------------------------------------------------
# compute_net_account — user-to-user transactions
# ---------------------------------------------------------------------------

def test_completed_u2u_affects_balance(alice, bob):
    txn = UserToUserTransaction(userFrom=bob, userTo=alice, value=500, completed=True)
    net = compute_net_account([], [txn])
    assert net[bob]   == -500
    assert net[alice] == 500

def test_incomplete_u2u_ignored(alice, bob):
    txn = UserToUserTransaction(userFrom=bob, userTo=alice, value=500, completed=False)
    net = compute_net_account([], [txn])
    # incomplete → no effect; neither user appears (or is zero)
    assert net.get(bob, 0)   == 0
    assert net.get(alice, 0) == 0

def test_mixed_completed_and_pending(alice, bob):
    done    = UserToUserTransaction(userFrom=bob, userTo=alice, value=300, completed=True)
    pending = UserToUserTransaction(userFrom=bob, userTo=alice, value=200, completed=False)
    net = compute_net_account([], [done, pending])
    assert net[bob]   == -300
    assert net[alice] == 300


# ---------------------------------------------------------------------------
# compute_net_account — group + user-to-user combined
# ---------------------------------------------------------------------------

def test_group_and_u2u_combined(alice, bob, carol):
    tag = Tag(name="all", users=[alice, bob, carol])
    group_txn = UserForGroupTransaction(userFrom=alice, tagTo=tag, value=900)
    # Bob pays back Alice 300 (completed)
    repayment = UserToUserTransaction(userFrom=bob, userTo=alice, value=300, completed=True)
    net = compute_net_account([group_txn], [repayment])
    assert net[alice] == -300   # was -600, received 300
    assert net[bob]   == 0      # was +300, paid 300
    assert net[carol] == 300
    assert sum(net.values()) == 0


# ---------------------------------------------------------------------------
# solve
# ---------------------------------------------------------------------------

def test_solve_simple(alice, bob):
    net = {alice: -100, bob: 100}
    txns = solve(dict(net))
    assert len(txns) == 1
    assert txns[0].userFrom == bob
    assert txns[0].userTo   == alice
    assert txns[0].value    == 100

def test_solve_balances_zero_out(alice, bob, carol):
    net = {alice: -600, bob: 300, carol: 300}
    result_net = dict(net)
    solve(result_net)
    assert all(v == 0 for v in result_net.values())

def test_solve_three_people_two_transactions(alice, bob, carol):
    # alice is owed 600, bob owes 300, carol owes 300
    net = {alice: -600, bob: 300, carol: 300}
    txns = solve(dict(net))
    assert len(txns) == 2
    total_settled = sum(t.value for t in txns)
    assert total_settled == 600

def test_solve_already_balanced_returns_empty(alice, bob):
    net = {alice: 0, bob: 0}
    txns = solve(dict(net))
    assert txns == []

def test_solve_is_deterministic(alice, bob, carol):
    net = {alice: -600, bob: 300, carol: 300}
    run1 = solve(dict(net))
    run2 = solve(dict(net))
    assert [(t.userFrom, t.userTo, t.value) for t in run1] == \
           [(t.userFrom, t.userTo, t.value) for t in run2]

def test_solve_does_not_mutate_original(alice, bob):
    net = {alice: -100, bob: 100}
    original = dict(net)
    solve(dict(net))   # pass a copy
    assert net == original


# ---------------------------------------------------------------------------
# Complex tag scenarios
# ---------------------------------------------------------------------------

def test_two_tags_different_subsets(alice, bob, carol, tag_ab, tag_bc):
    # Alice pays 200 for {Alice, Bob} → alice=-100, bob=+100
    # Carol pays 300 for {Bob, Carol} → carol=-150, bob=+150
    t1 = UserForGroupTransaction(userFrom=alice, tagTo=tag_ab, value=200)
    t2 = UserForGroupTransaction(userFrom=carol, tagTo=tag_bc, value=300)
    net = compute_net_account([t1, t2], [])
    assert net[alice] == -100
    assert net[bob]   == 250   # owes 100 to alice + 150 to carol
    assert net[carol] == -150
    assert sum(net.values()) == 0

def test_payer_in_multiple_tags(alice, bob, carol, dave, tag_all):
    # Alice pays for {Alice, Bob, Carol} and also for {Alice, Dave}
    tag_ad = Tag(name="ad", users=[alice, dave])
    t1 = UserForGroupTransaction(userFrom=alice, tagTo=tag_all, value=900)   # share=300
    t2 = UserForGroupTransaction(userFrom=alice, tagTo=tag_ad,  value=400)   # share=200
    net = compute_net_account([t1, t2], [])
    assert net[alice] == -600 + -200   # -(900-300) + -(400-200)
    assert net[bob]   == 300
    assert net[carol] == 300
    assert net[dave]  == 200
    assert sum(net.values()) == 0

def test_everyone_pays_once(alice, bob, carol, tag_all):
    # Each person pays 300 for the full group → should all zero out
    t1 = UserForGroupTransaction(userFrom=alice, tagTo=tag_all, value=300)
    t2 = UserForGroupTransaction(userFrom=bob,   tagTo=tag_all, value=300)
    t3 = UserForGroupTransaction(userFrom=carol, tagTo=tag_all, value=300)
    net = compute_net_account([t1, t2, t3], [])
    assert net[alice] == 0
    assert net[bob]   == 0
    assert net[carol] == 0

def test_tag_with_partial_repayment(alice, bob, carol, tag_all):
    # Alice pays 900 for the group; Bob repays 100 (partial, completed)
    t1 = UserForGroupTransaction(userFrom=alice, tagTo=tag_all, value=900)
    repay = UserToUserTransaction(userFrom=bob, userTo=alice, value=100, completed=True)
    net = compute_net_account([t1], [repay])
    assert net[alice] == -500   # was -600, got 100 back
    assert net[bob]   == 200    # owed 300, paid 100
    assert net[carol] == 300
    assert sum(net.values()) == 0

def test_cross_tag_payments_solve(alice, bob, carol, dave, tag_all):
    # Alice pays 900 for {Alice, Bob, Carol}; Dave pays 400 for {Bob, Dave}
    tag_bd = Tag(name="bd", users=[bob, dave])
    t1 = UserForGroupTransaction(userFrom=alice, tagTo=tag_all, value=900)
    t2 = UserForGroupTransaction(userFrom=dave,  tagTo=tag_bd,  value=400)
    net = compute_net_account([t1, t2], [])
    # alice=-600, bob=300+200=500, carol=300, dave=-200
    assert net[alice] == -600
    assert net[bob]   == 500
    assert net[carol] == 300
    assert net[dave]  == -200
    assert sum(net.values()) == 0

    txns = solve(dict(net))
    assert all(v == 0 for v in {
        u: net[u] + sum(t.value for t in txns if t.userTo == u)
                  - sum(t.value for t in txns if t.userFrom == u)
        for u in net
    }.values())

def test_five_people_two_overlapping_tags(alice, bob, carol, dave, eve):
    # Tag 1: alice pays for {alice, bob, carol, dave, eve} — 1000 → share=200
    tag_five = Tag(name="five", users=[alice, bob, carol, dave, eve])
    t1 = UserForGroupTransaction(userFrom=alice, tagTo=tag_five, value=1000)
    # Tag 2: bob pays for {bob, carol} — 300 → share=150
    tag_bc = Tag(name="bc", users=[bob, carol])
    t2 = UserForGroupTransaction(userFrom=bob, tagTo=tag_bc, value=300)
    net = compute_net_account([t1, t2], [])
    assert net[alice] == -800   # -(1000-200)
    assert net[bob]   == 200 - 150   # owes 200 from t1, owed 150 from t2
    assert net[carol] == 200 + 150   # owes 200 from t1, owes 150 from t2
    assert net[dave]  == 200
    assert net[eve]   == 200
    assert sum(net.values()) == 0

    result = dict(net)
    solve(result)
    assert all(v == 0 for v in result.values())
