from backend.db import get_agents, update_agent, add_event, get_current_round
from backend.agents import decide_action, generate_dialogue, shift_mood, resolve_trade

def run_round():
    """
    Run one complete round: Mira acts, then Leo acts.
    Returns list of 2 events created.
    """
    agents = get_agents()
    mira = next((a for a in agents if a["name"] == "Mira"), None)
    leo = next((a for a in agents if a["name"] == "Leo"), None)
    
    if not mira or not leo:
        return []
    
    current_round = get_current_round() + 1
    events_created = []
    
    # Track pending offers within this round
    pending_offer = None  # (offerer_name, item, price)
    
    # === MIRA'S TURN ===
    action_type, action_details = decide_action(mira, leo, pending_offer=None)
    
    if action_type == "OFFER_TRADE":
        pending_offer = (mira["name"], action_details["item"], action_details["price"])
        action_desc = f"offering to buy {action_details['item']} for {action_details['price']} coins"
        target = leo["name"]
    elif action_type == "CHAT":
        action_desc = "starting a friendly conversation"
        target = leo["name"]
    elif action_type == "IGNORE":
        action_desc = "ignoring the other agent"
        target = leo["name"]
    else:
        action_desc = "taking an action"
        target = leo["name"]
    
    dialogue = generate_dialogue(
        agent_name=mira["name"],
        traits=mira["traits"],
        mood=mira["mood"],
        money=mira["money"],
        inventory=mira["inventory"],
        action_description=action_desc,
        target=target
    )
    
    # Determine mood change and apply effects
    new_mood = mira["mood"]
    new_money = mira["money"]
    new_inventory = mira["inventory"]
    
    if action_type == "OFFER_TRADE":
        pass  # Mood will be affected by response
    elif action_type == "CHAT":
        new_mood = shift_mood(mira["mood"], 1)  # Friendly chat → happier
    elif action_type == "IGNORE":
        pass  # Neutral
    elif action_type in ("ACCEPT", "REFUSE"):
        pass  # Will be handled when responding
    
    # Save Mira's event
    add_event(current_round, mira["name"], action_type, target, dialogue, new_mood, new_money)
    update_agent(mira["name"], mood=new_mood, money=new_money, inventory=new_inventory)
    
    events_created.append({
        "round": current_round,
        "actor": mira["name"],
        "action": action_type,
        "target": target,
        "dialogue": dialogue,
        "mood_after": new_mood,
        "money_after": new_money
    })
    
    # === LEO'S TURN ===
    # Leo may respond to Mira's offer
    leo_pending = pending_offer if pending_offer and pending_offer[0] == mira["name"] else None
    
    action_type_leo, action_details_leo = decide_action(leo, mira, pending_offer=leo_pending)
    
    # If Leo is responding to an offer
    if leo_pending and action_type_leo in ("ACCEPT", "REFUSE"):
        offerer, item, price = leo_pending
        
        if action_type_leo == "ACCEPT":
            success, msg, buyer_delta, seller_delta, transferred = resolve_trade(action_details_leo, mira["name"], leo["name"])
            
            if success:
                # Update money
                mira_new_money = mira["money"] + buyer_delta
                leo_new_money = leo["money"] + seller_delta
                
                # Update inventory
                if transferred == "fish":
                    # Leo gives fish to Mira
                    mira_inv_count = int(mira["inventory"].split()[0]) + 1
                    leo_inv_count = int(leo["inventory"].split()[0]) - 1
                    mira_new_inv = f"{mira_inv_count} {transferred}"
                    leo_new_inv = f"{leo_inv_count} {transferred}"
                elif transferred == "bread":
                    # Mira gives bread to Leo
                    mira_inv_count = int(mira["inventory"].split()[0]) - 1
                    leo_inv_count = int(leo["inventory"].split()[0]) + 1
                    mira_new_inv = f"{mira_inv_count} {transferred}"
                    leo_new_inv = f"{leo_inv_count} {transferred}"
                else:
                    mira_new_inv = mira["inventory"]
                    leo_new_inv = leo["inventory"]
                
                # Both become happy on successful trade
                mira_mood_after = shift_mood(new_mood, 1)
                leo_mood_after = shift_mood(leo["mood"], 1)
                
                # Save updates
                update_agent("Mira", mood=mira_mood_after, money=mira_new_money, inventory=mira_new_inv)
                update_agent("Leo", mood=leo_mood_after, money=leo_new_money, inventory=leo_new_inv)
                
                action_desc_leo = f"accepting trade for {item}"
                target_leo = mira["name"]
                
                # Also update Mira's previous event mood
                # (We already saved it, but we can note the trade succeeded)
            else:
                leo_mood_after = leo["mood"]
                action_desc_leo = f"attempting to accept but failed"
                target_leo = mira["name"]
        
        elif action_type_leo == "REFUSE":
            # Refuser becomes annoyed, offerer becomes sad
            leo_mood_after = shift_mood(leo["mood"], -1)  # annoyed
            mira_mood_after = shift_mood(new_mood, -2)  # sad
            
            update_agent("Leo", mood=leo_mood_after)
            update_agent("Mira", mood=mira_mood_after)
            
            action_desc_leo = f"refusing trade offer"
            target_leo = mira["name"]
    
    elif action_type_leo == "OFFER_TRADE":
        action_desc_leo = f"offering to buy {action_details_leo['item']} for {action_details_leo['price']} coins"
        target_leo = mira["name"]
        leo_mood_after = leo["mood"]
    elif action_type_leo == "CHAT":
        action_desc_leo = "responding with friendly chat"
        target_leo = mira["name"]
        leo_mood_after = shift_mood(leo["mood"], 1)
        update_agent("Leo", mood=leo_mood_after)
    elif action_type_leo == "IGNORE":
        action_desc_leo = "ignoring the other agent"
        target_leo = mira["name"]
        leo_mood_after = leo["mood"]
    else:
        action_desc_leo = "taking an action"
        target_leo = mira["name"]
        leo_mood_after = leo["mood"]
    
    dialogue_leo = generate_dialogue(
        agent_name=leo["name"],
        traits=leo["traits"],
        mood=leo_mood_after if 'leo_mood_after' in dir() else leo["mood"],
        money=leo["money"],
        inventory=leo["inventory"],
        action_description=action_desc_leo,
        target=target_leo
    )
    
    # Ensure mood is tracked
    if 'leo_mood_after' not in dir():
        leo_mood_after = leo["mood"]
    
    add_event(current_round, leo["name"], action_type_leo, target_leo, dialogue_leo, leo_mood_after, leo["money"])
    
    events_created.append({
        "round": current_round,
        "actor": leo["name"],
        "action": action_type_leo,
        "target": target_leo,
        "dialogue": dialogue_leo,
        "mood_after": leo_mood_after,
        "money_after": leo["money"]
    })
    
    return events_created
