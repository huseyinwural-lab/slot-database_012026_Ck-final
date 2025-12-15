@router.post("/request-password-reset")
async def request_password_reset(payload: PasswordResetRequest, session: AsyncSession = Depends(get_session)):
    statement = select(AdminUser).where(AdminUser.email == payload.email)
    result = await session.execute(statement) # Changed exec to execute
    admin = result.scalars().first()

    # Generic response regardless of whether user exists or not (User Enumeration Prevention)
    generic_response = {"message": "If this email is registered, you will receive a password reset link."}

    if not admin:
        return generic_response

    token = create_access_token(
        data={"sub": admin.id, "purpose": "password_reset"},
        expires_delta=timedelta(minutes=30),
    )

    admin.password_reset_token = token
    session.add(admin)
    await session.commit()

    # In a real production scenario, we would send an email here.
    # For now, we just log it on the server side so it doesn't leak in the response.
    # TODO: Integrate SendGrid or SMTP here.
    print(f"[Password Reset] Token for {admin.email}: {token}")

    return generic_response
