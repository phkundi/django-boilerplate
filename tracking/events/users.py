from tracking.events import EventDefinition

# Auth + User
USER_LOGIN = EventDefinition(
    name="user_login",
    category="users",
    description="User logged in",
)
USER_LOGOUT = EventDefinition(
    name="user_logout",
    category="users",
    description="User logged out",
)
USER_REGISTER = EventDefinition(
    name="user_register",
    category="users",
    description="User registered",
)
USER_UPDATE = EventDefinition(
    name="user_update",
    category="users",
    description="User updated",
)
USER_DELETE = EventDefinition(
    name="user_delete",
    category="users",
    description="User deleted",
)
PASSWORD_RESET_REQUESTED = EventDefinition(
    name="password_reset_requested",
    category="users",
    description="User password reset was requested",
)
PASSWORD_RESET = EventDefinition(
    name="password_reset",
    category="users",
    description="User password was reset",
)
EMAIL_VERIFIED = EventDefinition(
    name="email_verified",
    category="users",
    description="User email was verified",
)

# Invites

CREATE_INVITE_LINK = EventDefinition(  # TODO: event is not used, check if necessary
    name="create_invite_link",
    category="users",
    description="Invite link was created",
)
ACCEPT_INVITE = EventDefinition(
    name="accept_invite",
    category="users",
    description="Invite was accepted",
)
USER_REFERRED = EventDefinition(
    name="user_referred",
    category="users",
    description="User referred another user",
)
