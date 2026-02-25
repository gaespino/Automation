# Unit Portfolio Dashboard

URL: `/portfolio`

## Overview
Track experiment results across units, view scores, manage templates and recipes.

## Loading Units
Unit data is read from JSON files in `DATA_PATH/{product}/`. Select a product from the dropdown to load available units.

## Experiments
- **Add experiment** — use the form card to set parameters and click Add
- **Edit experiment** — click the edit icon on the experiment row
- **Delete experiment** — click delete icon; confirm in modal

## Templates & Recipes
Load templates from `settings/templates/` or create inline. Scripts are configured via `settings/scripts_config.json`.

## Export
Use the Export button to download the current unit data as JSON or Excel.
