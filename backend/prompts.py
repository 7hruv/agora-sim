AGENT_PROMPT = """You are {name}. Traits: {traits}. Current mood: {mood}.
You have {money} coins and {inventory}.
Recent memory:
{last_3_events_as_bullets}

You are about to: {action_description}
Say ONE short line of dialogue to {target}, in character, matching your mood.
Max 2 sentences. No narration, no emojis, no explanation."""

def build_prompt(name, traits, mood, money, inventory, recent_events, action_description, target):
    # Format recent events as bullet points
    if recent_events:
        bullets = []
        for ev in recent_events[-3:]:
            bullets.append(f"- Round {ev['round']}: {ev['actor']} {ev['action'].lower()} with {ev['target']}")
        last_3_events_as_bullets = "\n".join(bullets)
    else:
        last_3_events_as_bullets = "- No prior events"
    
    return AGENT_PROMPT.format(
        name=name,
        traits=traits,
        mood=mood,
        money=money,
        inventory=inventory,
        last_3_events_as_bullets=last_3_events_as_bullets,
        action_description=action_description,
        target=target
    )
