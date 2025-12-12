"""
Pytest fixtures for AI infrastructure tests.
"""

import pytest
from typing import Dict, Any


# Mock accessibility snapshot data representing a typical login page
MOCK_LOGIN_PAGE_SNAPSHOT = """- WebArea "Login Page" [ref=root]:
  - form [ref=form1]:
    - textbox "Username" [ref=e1]: placeholder="Enter username"
    - textbox "Password" [ref=e2]: placeholder="Enter password"
    - button "Login" [ref=e3]:
  - link "Sign Up" [ref=e4]: href="/signup"
  - button "Help" [ref=e5]:"""


# Mock snapshot with tables
MOCK_TABLE_PAGE_SNAPSHOT = """- WebArea "Data Table" [ref=root]:
  - heading "User Data" [ref=h1]: level=1
  - table [ref=t1]:
    - columnheader "Name" [ref=th1]
    - columnheader "Email" [ref=th2]
    - columnheader "Status" [ref=th3]
  - button "Export" [ref=btn1]:"""


# Mock snapshot with navigation
MOCK_NAV_PAGE_SNAPSHOT = """- WebArea "Home Page" [ref=root]:
  - navigation [ref=nav1]:
    - link "Home" [ref=nav_home]: href="/"
    - link "Products" [ref=nav_products]: href="/products"
    - link "About" [ref=nav_about]: href="/about"
  - heading "Welcome" [ref=h1]: level=1"""


# Mock snapshot with dropdowns
MOCK_DROPDOWN_PAGE_SNAPSHOT = """- WebArea "Form Page" [ref=root]:
  - form [ref=form1]:
    - combobox "Country" [ref=dd1]: option="USA" option="Canada" option="UK"
    - checkbox "Subscribe" [ref=cb1]: checked
    - button "Submit" [ref=btn1]:"""


# Empty snapshot
MOCK_EMPTY_SNAPSHOT = ""


# Complex multi-form snapshot
MOCK_COMPLEX_PAGE_SNAPSHOT = """- WebArea "Registration" [ref=root]:
  - form [ref=form1]:
    - textbox "First Name" [ref=f1]: placeholder="John"
    - textbox "Last Name" [ref=f2]: placeholder="Doe"
    - textbox "Email" [ref=f3]: placeholder="email@example.com"
    - button "Next" [ref=btn1]:
  - form [ref=form2]:
    - textbox "Username" [ref=u1]: placeholder="username"
    - textbox "Password" [ref=p1]: placeholder="password"
    - searchbox "Search" [ref=s1]: placeholder="Search..."
    - button "Create Account" [ref=btn2]:
  - link "Terms" [ref=link1]: href="/terms"
  - link "Privacy" [ref=link2]: href="/privacy"
  - button "Cancel" [ref=btn3]:"""


@pytest.fixture
def login_page_snapshot() -> str:
    """Return mock login page snapshot."""
    return MOCK_LOGIN_PAGE_SNAPSHOT


@pytest.fixture
def table_page_snapshot() -> str:
    """Return mock table page snapshot."""
    return MOCK_TABLE_PAGE_SNAPSHOT


@pytest.fixture
def nav_page_snapshot() -> str:
    """Return mock navigation page snapshot."""
    return MOCK_NAV_PAGE_SNAPSHOT


@pytest.fixture
def dropdown_page_snapshot() -> str:
    """Return mock dropdown page snapshot."""
    return MOCK_DROPDOWN_PAGE_SNAPSHOT


@pytest.fixture
def empty_snapshot() -> str:
    """Return empty snapshot."""
    return MOCK_EMPTY_SNAPSHOT


@pytest.fixture
def complex_page_snapshot() -> str:
    """Return complex multi-form page snapshot."""
    return MOCK_COMPLEX_PAGE_SNAPSHOT


@pytest.fixture
def sample_page_dict() -> Dict[str, Any]:
    """Return sample page context as dict for MCP mock."""
    return {
        "url": "https://example.com/login",
        "title": "Example Login",
        "snapshot": MOCK_LOGIN_PAGE_SNAPSHOT,
    }
