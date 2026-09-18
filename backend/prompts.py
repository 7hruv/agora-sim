AGENT_PROMPT = """You are {name}. Traits: {traits}. Current mood: {mood}.
Your inventory: {inventory}. Your coins: {money}.

Recent memory (last 5 events):
{last_5_events_as_bullets}

Your action this turn: {action_description}
{action_hint}

Rules:
- You are speaking TO {target}. Never refer to yourself in the third person.
- Only discuss ONE item per line. Do not invent quantities like "two fish" or "three bread".
- Say ONE short line of dialogue to {target}, in character, matching your mood.
- Max 2 sentences. No narration, no emojis, no explanation.
- DO NOT use any of these exact lines you already said: {banned_phrases}
- If the recent memory contains a similar situation, say something DIFFERENT this time.
- Only output the dialogue text, nothing else."""


def _get_action_hint(action_description):
    d = (action_description or "").lower()
    if "accepting" in d:
        return 'REQUIRED: Direct acceptance ("Deal!", "I accept.", "Agreed."). No questions.'
    if "refusing" in d:
        return 'REQUIRED: Direct rejection ("No.", "Not interested.", "I decline."). No questions.'
    if "ignoring" in d:
        return "REQUIRED: A brief, in-character dismissal. Vary your phrasing every time. Never say just 'Whatever.'"
    if "offering" in d:
        return 'REQUIRED: Restate the exact item and the exact price shown in the action above. Do NOT invent or change the price.'
    if "chat" in d or "friendly" in d:
        return "REQUIRED: Casual small talk. Ask about something specific, not 'how's your day'."
    return ""


def build_prompt(name, traits, mood, money, inventory, recent_events, action_description, target):
    events = recent_events[-5:] if recent_events else []
    if events:
        bullets = []
        for ev in events:
            line = f"- R{ev.get('round', '?')}: {ev.get('actor', '?')} {ev.get('action', '').lower()} -> {ev.get('target', '?')}"
            dialogue = ev.get('dialogue')
            if dialogue:
                line += f': "{dialogue}"'
            bullets.append(line)
        last_5_events_as_bullets = "\n".join(bullets)
    else:
        last_5_events_as_bullets = "- No prior events"

    # Collect the agent's own recent lines as banned phrases
    own_lines = [ev.get('dialogue', '') for ev in events
                 if ev.get('actor') == name and ev.get('dialogue')]
    banned = " | ".join(own_lines) if own_lines else "(none yet)"

    return AGENT_PROMPT.format(
        name=name,
        traits=traits,
        mood=mood,
        money=money,
        inventory=inventory,
        last_5_events_as_bullets=last_5_events_as_bullets,
        action_description=action_description,
        action_hint=_get_action_hint(action_description),
        banned_phrases=banned,
        target=target
    )