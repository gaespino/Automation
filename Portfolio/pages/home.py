"""
Dashboard root redirect — /dashboard/ → /dashboard/portfolio
"""
import dash
from dash import dcc

dash.register_page(__name__, path='/', name='Home', title='THR Tools Portfolio')

# Immediately redirect to the Unit Portfolio (the actual dashboard page).
# This eliminates the intermediate "old main" screen at /dashboard/.
layout = dcc.Location(id='home-redirect', href='/dashboard/portfolio', refresh=True)
