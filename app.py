"""VUB AI — Multi-objective Picking Planner (SONAE MVP1, PEER project).

A three-tab homepage:
  1. Planner 1        — the direct mACO1 multi-objective planner.
  2. Guided Planner   — learn from scratch -> beginner assignment -> advanced playground.
  3. About            — project, credits and literature.

Run with:  ``streamlit run app.py``
(The original interactive navigation simulator is preserved as ``app_navigation.py``.)
"""

import streamlit as st

import branding
import tab_planner
import tab_learn
import tab_about

st.set_page_config(page_title="VUB AI • Multi-objective Picking Planner",
                   page_icon="🛒", layout="wide")

branding.inject_css()
branding.header("Multi-objective Picking Planner",
                "VUB AI Research Group · mACO1 ant colony optimisation · SONAE / PEER use case")

tab1, tab2, tab3 = st.tabs(["Planner 1", "Guided Planner", "About"])

with tab1:
    tab_planner.render()

with tab2:
    tab_learn.render()

with tab3:
    tab_about.render()
