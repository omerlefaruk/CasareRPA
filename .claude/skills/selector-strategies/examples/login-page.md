# Login Page Selectors

## Good

```python
# Anchor to form, then target input
USERNAME_SELECTOR = '[data-testid="login-form"] input[name="username"]'
PASSWORD_SELECTOR = '[data-testid="login-form"] input[name="password"]'
SUBMIT_SELECTOR = '[data-testid="login-form"] button[type="submit"]'

# Alternative: aria-label for accessibility-focused sites
USERNAME_SELECTOR = 'input[aria-label="Username or email"]'
PASSWORD_SELECTOR = 'input[aria-label="Password"]'
```

## Bad

```python
# Brittle - breaks if form structure changes
USERNAME_SELECTOR = 'div.login-container > div.row > div.col > input.form-control'

# Fragile - relies on class names tied to styling
USERNAME_SELECTOR = 'input.MuiTextField-input'

# Dangerous - nth-child breaks if field order changes
USERNAME_SELECTOR = 'form:nth-child(2) > input:nth-of-type(1)'
```

---

*Why Good Works*: Anchoring to `data-testid` isolates from CSS/styling changes. The `name` attribute on inputs rarely changes.
