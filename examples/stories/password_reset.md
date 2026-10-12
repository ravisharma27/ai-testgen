# Password reset

As a registered user, I want to reset my password from the login page so that I can regain access if I forget it.

## Acceptance criteria
1. A "Forgot password?" link on the login page opens the reset form.
2. The user enters their email; if it belongs to an account, a reset link is emailed.
3. For an unknown email, the same confirmation message is shown (no account enumeration).
4. The reset link expires after 30 minutes and can be used only once.
5. The new password must be 8 to 64 characters and contain at least one digit and one letter.
6. The new password cannot match any of the last 3 passwords.
7. After 5 reset requests within one hour for the same email, further requests are blocked for that hour.
