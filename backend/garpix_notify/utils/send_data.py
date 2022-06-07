def notify_create(template, context, user, email, phone, viber, json, time, room):
    data_dict = {
        'subject': template.render_subject(context),
        'text': template.render_text(context),
        'html': template.render_html(context),
        'user': user,
        'email': email,
        'phone': phone if phone is not None else "",
        'viber_chat_id': viber if viber is not None else "",
        'type': template.type,
        'event': template.event,
        'category': template.category if template.category else None,
        'data_json': json,
        'send_at': time,
        'room_name': room,
    }
    return data_dict
