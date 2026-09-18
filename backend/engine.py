from db import get_agents, update_agent, add_event, get_current_round
from agents import decide_action, generate_dialogue, shift_mood

# Pending offer survives between rounds (in-memory).
_LAST_PENDING_OFFER = None


def _parse_inventory(inv_str):
    result = {"fish": 0, "bread": 0}
    if not inv_str:
        return result
    for part in inv_str.split(","):
        tokens = part.strip().split()
        if len(tokens) >= 2:
            try:
                count = int(tokens[0])
                item = tokens[1].lower()
                if item in result:
                    result[item] = count
            except ValueError:
                pass
    return result


def _format_inventory(inv):
    parts = []
    if inv.get("fish", 0) > 0:
        parts.append(f"{inv['fish']} fish")
    if inv.get("bread", 0) > 0:
        parts.append(f"{inv['bread']} bread")
    return ", ".join(parts) if parts else "nothing"


def _describe(action, details, target):
    if action == "OFFER_TRADE":
        return (f"You are the BUYER. You want ONE {details['item']} from {target}. "
                f"Your offer: exactly {details['price']} coins. "
                f"Say this offer to {target} in one line.")
    if action == "ACCEPT":
        return f"You accept {target}'s trade offer."
    if action == "REFUSE":
        return f"You refuse {target}'s trade offer."
    if action == "CHAT":
        return "You start a friendly conversation."
    if action == "IGNORE":
        return "You ignore the other agent."
    return "You take an action."


def run_round():
    global _LAST_PENDING_OFFER

    agents = get_agents()
    mira = next((a for a in agents if a["name"] == "Mira"), None)
    leo = next((a for a in agents if a["name"] == "Leo"), None)
    if not mira or not leo:
        return []

    current_round = get_current_round() + 1
    events_created = []

    # ---- Local state (source of truth for the whole round) ----
    mira_money = mira["money"]
    leo_money = leo["money"]
    mira_inv = _parse_inventory(mira["inventory"])
    leo_inv = _parse_inventory(leo["inventory"])
    mira_mood = mira["mood"]
    leo_mood = leo["mood"]

    # ============ MIRA ACTS ============
    mira_pending = None
    if _LAST_PENDING_OFFER and _LAST_PENDING_OFFER[0] == "Leo":
        mira_pending = _LAST_PENDING_OFFER

    mira_action, mira_details = decide_action(mira, leo, pending_offer=mira_pending)

    if mira_pending and mira_action == "ACCEPT":
        offerer, item, price, side = mira_pending
        if side == "buy":
            # Leo wants to buy from Mira
            mira_money += price
            leo_money -= price
            mira_inv[item] = max(0, mira_inv.get(item, 0) - 1)
            leo_inv[item] = leo_inv.get(item, 0) + 1
        else:
            # Leo wants to sell to Mira
            mira_money -= price
            leo_money += price
            mira_inv[item] = mira_inv.get(item, 0) + 1
            leo_inv[item] = max(0, leo_inv.get(item, 0) - 1)
        mira_mood = shift_mood(mira_mood, 1)
        leo_mood = shift_mood(leo_mood, 1)
        if side == "buy":
            mira_desc = (f"You are the SELLER. You are selling ONE {item} to Leo for {price} coins. "
                         f"Accept the deal in one line. Do not offer to pay him.")
        else:
            mira_desc = (f"You are the BUYER. You are buying ONE {item} from Leo for {price} coins. "
                         f"Accept the deal in one line.")
        _LAST_PENDING_OFFER = None

    elif mira_pending and mira_action == "REFUSE":
        mira_mood = shift_mood(mira_mood, -1)
        leo_mood = shift_mood(leo_mood, -1)
        mira_desc = f"You refuse Leo's offer in one short line."
        _LAST_PENDING_OFFER = None
    else:
        mira_desc = _describe(mira_action, mira_details, target=leo["name"])

    mira_dialogue = generate_dialogue(
        agent_name=mira["name"],
        traits=mira["traits"],
        mood=mira_mood,
        money=mira_money,
        inventory=_format_inventory(mira_inv),
        action_description=mira_desc,
        target=leo["name"]
    )

    events_created.append({
        "round": current_round,
        "actor": mira["name"],
        "action": mira_action,
        "target": leo["name"],
        "dialogue": mira_dialogue,
        "mood_after": mira_mood,
        "money_after": mira_money
    })

    # ============ LEO ACTS ============
    pending = None
    if mira_action == "OFFER_TRADE":
        pending = (mira["name"], mira_details["item"], mira_details["price"], "buy")

    leo_action, leo_details = decide_action(leo, mira, pending_offer=pending)

    if pending and leo_action == "ACCEPT":
        offerer, item, price, side = pending
        # Mira wants to buy from Leo
        mira_money -= price
        leo_money += price
        mira_inv[item] = mira_inv.get(item, 0) + 1
        leo_inv[item] = max(0, leo_inv.get(item, 0) - 1)
        mira_mood = shift_mood(mira_mood, 1)
        leo_mood = shift_mood(leo_mood, 1)
        leo_desc = (f"You are the SELLER. You are selling ONE {item} to Mira for {price} coins. "
                    f"Accept the deal in one line. Do not offer to pay her.")

    elif pending and leo_action == "REFUSE":
        mira_mood = shift_mood(mira_mood, -1)
        leo_mood = shift_mood(leo_mood, -1)
        leo_desc = f"You refuse Mira's offer in one short line."
    else:
        leo_desc = _describe(leo_action, leo_details, target=mira["name"])
        if leo_action == "CHAT":
            leo_mood = shift_mood(leo_mood, 1)
        if leo_action == "OFFER_TRADE":
            _LAST_PENDING_OFFER = ("Leo", leo_details["item"], leo_details["price"], "buy")

    leo_dialogue = generate_dialogue(
        agent_name=leo["name"],
        traits=leo["traits"],
        mood=leo_mood,
        money=leo_money,
        inventory=_format_inventory(leo_inv),
        action_description=leo_desc,
        target=mira["name"]
    )

    events_created.append({
        "round": current_round,
        "actor": leo["name"],
        "action": leo_action,
        "target": mira["name"],
        "dialogue": leo_dialogue,
        "mood_after": leo_mood,
        "money_after": leo_money
    })

    # ============ COMMIT EVERYTHING AT ONCE ============
    update_agent(mira["name"], mood=mira_mood, money=mira_money,
                 inventory=_format_inventory(mira_inv))
    update_agent(leo["name"], mood=leo_mood, money=leo_money,
                 inventory=_format_inventory(leo_inv))

    add_event(current_round, mira["name"], mira_action, leo["name"],
              mira_dialogue, mira_mood, mira_money)
    add_event(current_round, leo["name"], leo_action, mira["name"],
              leo_dialogue, leo_mood, leo_money)

    return events_created