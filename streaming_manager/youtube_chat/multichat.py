"""Pure mapping from YouTube provider events to the future InOneLine contract."""


def _fragments(message):
    if not message.fragments:
        return [{"kind": "text", "text": message.text}] if message.text else []
    result = []
    for fragment in message.fragments[:256]:
        if fragment.kind == "emoji" and fragment.image_url:
            result.append({"kind": "image", "text": fragment.text, "url": fragment.image_url})
        else:
            result.append({"kind": "text", "text": fragment.text})
    return result


def to_multichat_events(events, received_at, sequence_start=0):
    """Return JSON-ready events; preserve provider order and never sort."""
    output = []
    for offset, event in enumerate(events):
        sequence = sequence_start + offset
        if event.kind in {"delete", "delete_author"}:
            output.append({"kind": event.kind, "target": event.target, "platform": "youtube",
                           "received_at": received_at, "sequence": sequence})
            continue
        message = event.message
        if message is None or event.kind not in {"add", "replace"}:
            continue
        output.append({
            "kind": event.kind, "id": message.id, "target": event.target,
            "platform": "youtube",
            "author_id": message.author_id, "author": message.author,
            "avatar_url": message.avatar_url, "badges": [], "color": "",
            "text": message.text, "fragments": _fragments(message),
            "sent_at": message.sent_at, "received_at": received_at, "sequence": sequence,
        })
    return tuple(output)
