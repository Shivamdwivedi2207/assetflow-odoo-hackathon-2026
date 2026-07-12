# AssetFlow

Enterprise asset and resource management system for the Odoo Hackathon 2026.

The application maintains one workflow across the dashboard, domain layer, and
in-memory data store: allocate an available asset, check it back in, raise and
approve a maintenance ticket, assign a technician, then resolve the repair.

## Run the dashboard

```powershell
python -m pip install streamlit
streamlit run assetflow/streamlit_app.py
```

Use the seeded Asset Manager profile to exercise the complete workflow.
