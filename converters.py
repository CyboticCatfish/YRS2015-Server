def user_to_xml(user):
    return "<user id='%s' name='%s'>" % (str(user.id), user.username)