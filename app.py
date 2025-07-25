
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# Connect to SQLite DB
conn = sqlite3.connect("app.db", check_same_thread=False)

@st.cache_data
def load_data():
    products = pd.read_sql_query("SELECT * FROM products", conn)
    commercial_refs = pd.read_sql_query("SELECT * FROM commercial_references", conn)
    metadata_templates = pd.read_sql_query("SELECT * FROM metadata_templates", conn)
    product_metadata = pd.read_sql_query("SELECT * FROM product_metadata", conn)
    return products, commercial_refs, metadata_templates, product_metadata

products, commercial_refs, metadata_templates, product_metadata = load_data()

st.set_page_config(page_title="Product Metadata Manager", layout="wide")
st.title("🧱 Product Metadata Manager")

# Sidebar Navigation
menu = ["Assign Metadata to Commercial References", "View Product Metadata", "Vulnerability Handling"]
choice = st.sidebar.radio("Menu", menu)

if choice == "Assign Metadata to Commercial References":
    st.subheader("Assign Metadata")

    commercial_refs['Label'] = commercial_refs.apply(
        lambda row: f"{products.loc[products['ProductID'] == row['ProductID'], 'ProductName'].values[0]} → {row['CommercialReferenceNumber']}", axis=1
    )
    selected_refs = st.multiselect("Select Commercial References", commercial_refs['Label'])

    if selected_refs:
        template_names = metadata_templates["TemplateName"].tolist()
        selected_template = st.selectbox("Select Metadata Template", template_names)
        template_row = metadata_templates[metadata_templates["TemplateName"] == selected_template].iloc[0]

        st.markdown("### Template Preview")
        st.json(template_row.to_dict())

        if st.button("Assign Metadata"):
            for label in selected_refs:
                ref_id = commercial_refs[commercial_refs['Label'] == label]["ReferenceID"].values[0]
                cur.execute("SELECT COALESCE(MAX(MetadataID), 0) + 1 FROM product_metadata")
                new_id = cur.fetchone()[0]
                cur.execute("""
                    INSERT INTO product_metadata (
                        MetadataID, ReferenceID, TemplateID, DBBricks, SEBricks, Chips,
                        ITStack, EncryptionLibs, SecureBoot
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    new_id, ref_id, template_row["TemplateID"],
                    template_row["DBBricks"], template_row["SEBricks"], template_row["Chips"],
                    template_row["ITStack"], template_row["EncryptionLibs"], template_row["SecureBoot"]
                ))

elif choice == "View Product Metadata":
    st.subheader("Product Metadata Records")
    df = pd.read_sql_query("""
        SELECT pm.*, cr.CommercialReferenceNumber, p.ProductName
        FROM product_metadata pm
        JOIN commercial_references cr ON pm.ReferenceID = cr.ReferenceID
        JOIN products p ON cr.ProductID = p.ProductID
    """, conn)
    st.dataframe(df)

elif choice == "Vulnerability Handling":
    st.subheader("Vulnerability Handling")

    user_email = st.text_input("Enter your email to view assigned products:")
    if user_email:
        assigned_products = products[
            (products["SecurityAdvisor"] == user_email) |
            (products["VulnerabilityHandler"] == user_email)
        ]

        if assigned_products.empty:
            st.info("You are not assigned to any products.")
        else:
            st.markdown("### Your Assigned Products")
            for _, row in assigned_products.iterrows():
                st.markdown(f"**{row['ProductName']}** ({row['ProductID']})")
                with st.form(f"vuln_form_{row['ProductID']}"):
                    aware = st.selectbox("Are you aware of your responsibilities under CRA?", ["Yes", "No"])
                    compliant = st.selectbox("Is the product ready to comply with CRA requirements?", ["Yes", "No"])
                    kev_process = st.selectbox("Is there a process to handle KEV issues?", ["Yes", "No"])
                    se_disclosure = st.selectbox("Is there a process aligned with SE expectations?", ["Yes", "No"])

                    action_required = "No" if all(ans == "Yes" for ans in [aware, compliant, kev_process, se_disclosure]) else "Yes"
                    action_desc, follow_up_date, support_requested = "", None, "No"

                    if action_required == "Yes":
                        st.warning("Since at least one response is 'No', please create an action point.")
                        action_desc = st.text_area("Action Description")
                        follow_up_date = st.date_input("Follow-up Date")
                        support_requested = st.selectbox("Would you like to request support?", ["Yes", "No"])

                    submitted = st.form_submit_button("Submit")

                    if submitted:
                        cur = conn.cursor()
                        cur.execute("UPDATE products SET CRAPlan = ?, CRA_EoL_Date = ?, CRA_StopSell_VPApproved = ?, CRA_StopSell_Flagged = ? WHERE ProductID = ?", (
                            plan_option,
                            eol_date.strftime("%Y-%m-%d") if plan_option == "EoL" and eol_date else "",
                            approved,
                            flagged,
                            selected_id
                        ))
                        conn.commit()

elif choice == "Product Search & Edit":
    st.subheader("🔍 Product Search & Management")

    search_query = st.text_input("Search by Product Name or Commercial Reference")

    if search_query:
        search_results = pd.read_sql_query(f'''
            SELECT p.*, cr.CommercialReferenceNumber
            FROM products p
            LEFT JOIN commercial_references cr ON cr.ProductID = p.ProductID
            WHERE p.ProductName LIKE '%{search_query}%'
            OR cr.CommercialReferenceNumber LIKE '%{search_query}%'
        ''', conn)
        st.dataframe(search_results)

    st.markdown("---")
    st.markdown("### ➕ Add New Product")
    with st.form("add_product_form"):
        new_name = st.text_input("Product Name")
        new_pim = st.text_input("PIM Link")
        new_offer = st.text_input("Offer Owner Email")
        new_pm = st.text_input("Product Manager Email")
        new_sec = st.text_input("Security Advisor Email")
        new_vuln = st.text_input("Vulnerability Handler Email")
        new_cert = st.text_input("Certification Engineer Email")
        new_vp = st.text_input("VP Email")
        new_svp = st.text_input("SVP Email")
        submitted = st.form_submit_button("Add Product")

        if submitted:
            cur = conn.cursor()
            cur.execute("SELECT COALESCE(MAX(ProductID), 0) + 1 FROM products")
            new_id = cur.fetchone()[0]
            cur.execute("""
                INSERT INTO products (
                    ProductID, ProductName, PIMLink, OfferOwner, ProductManager,
                    SecurityAdvisor, VulnerabilityHandler, CertificationEngineer, VP, SVP
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (new_id, new_name, new_pim, new_offer, new_pm, new_sec, new_vuln, new_cert, new_vp, new_svp))
            conn.commit()

    st.markdown("---")
    st.markdown("### ✏️ Edit Existing Product")
    product_list = pd.read_sql_query("SELECT ProductID, ProductName FROM products", conn)
    selected_id = st.selectbox("Select Product", product_list["ProductID"].tolist(), format_func=lambda x: product_list[product_list["ProductID"] == x]["ProductName"].values[0])
    if selected_id:
        product = pd.read_sql_query(f"SELECT * FROM products WHERE ProductID = {selected_id}", conn).iloc[0]
        with st.form("edit_product_form"):
            edit_name = st.text_input("Product Name", product["ProductName"])
            edit_pim = st.text_input("PIM Link", product["PIMLink"])
            edit_offer = st.text_input("Offer Owner Email", product["OfferOwner"])
            edit_pm = st.text_input("Product Manager Email", product["ProductManager"])
            edit_sec = st.text_input("Security Advisor Email", product["SecurityAdvisor"])
            edit_vuln = st.text_input("Vulnerability Handler Email", product["VulnerabilityHandler"])
            edit_cert = st.text_input("Certification Engineer Email", product["CertificationEngineer"])
            edit_vp = st.text_input("VP Email", product["VP"])
            edit_svp = st.text_input("SVP Email", product["SVP"])
            updated = st.form_submit_button("Update Product")

            if updated:
                cur.execute("""
                    UPDATE products
                    SET ProductName = ?, PIMLink = ?, OfferOwner = ?, ProductManager = ?,
                        SecurityAdvisor = ?, VulnerabilityHandler = ?, CertificationEngineer = ?,
                        VP = ?, SVP = ?
                    WHERE ProductID = ?
                """, (edit_name, edit_pim, edit_offer, edit_pm, edit_sec, edit_vuln, edit_cert, edit_vp, edit_svp, selected_id))


elif choice == "Bulk Import/Export":
    st.subheader("📥 Bulk Import / 📤 Export Products")

    st.markdown("### 🔽 Export All Products")
    export_df = pd.read_sql_query("SELECT * FROM products", conn)
    csv = export_df.to_csv(index=False).encode("utf-8")
    st.download_button("Download Products CSV", data=csv, file_name="products_export.csv", mime="text/csv")

    st.markdown("---")
    st.markdown("### 🔼 Import Products from CSV")
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded_file:
        try:
            imported_df = pd.read_csv(uploaded_file)
            st.dataframe(imported_df)
            if st.button("Import Products"):
                imported_df.to_sql("products", conn, if_exists="append", index=False)
        except Exception as e:
            st.error(f"Failed to import CSV: {e}")

elif choice == "Role-Based Access":
    st.subheader("🔐 Role-Based Access Control (RBAC)")
    role = st.selectbox("Select your role", ["Viewer", "Editor", "Admin"])

    st.markdown("### Role Capabilities")
    if role == "Viewer":
        st.info("🔍 Can view products, metadata, dashboards.")
    elif role == "Editor":
        st.info("✏️ Can also edit existing products and assign metadata.")
    elif role == "Admin":
        st.markdown("⚠️ This is a mock role selector for demo purposes. In a real deployment, roles would be validated via login.")


elif choice == "Dashboard Analytics":

    import plotly.express as px

    st.markdown("### Interactive Charts")

    # CRA Awareness Pie Chart
    cra_data = pd.read_sql_query("SELECT AwareOfCRA, COUNT(*) as Count FROM vulnerability_compliance GROUP BY AwareOfCRA", conn)
    if not cra_data.empty:
        pie_chart = px.pie(cra_data, names="AwareOfCRA", values="Count", title="CRA Awareness Distribution")
        st.plotly_chart(pie_chart)

    # KEV Process Bar Chart
    kev_data = pd.read_sql_query("SELECT KEVProcessExists, COUNT(*) as Count FROM vulnerability_compliance GROUP BY KEVProcessExists", conn)
    if not kev_data.empty:
        bar_chart = px.bar(kev_data, x="KEVProcessExists", y="Count", title="KEV Process Compliance", color="KEVProcessExists")
        st.plotly_chart(bar_chart)

    # Support Request Response Time Histogram
    tracking = pd.read_sql_query("SELECT * FROM vulnerability_tracking", conn)
    if not tracking.empty and "ResponseTimeHours" in tracking.columns:
        try:
            tracking["ResponseTimeHours"] = pd.to_numeric(tracking["ResponseTimeHours"], errors="coerce")
            tracking = tracking.dropna(subset=["ResponseTimeHours"])
            hist = px.histogram(tracking, x="ResponseTimeHours", nbins=10, title="Support Response Time Distribution (hours)")
            st.plotly_chart(hist)
        except Exception as e:
            st.warning(f"Could not generate histogram: {e}")

    st.subheader("📊 Risk & Compliance Dashboard")

    # Risk Assessment Stats (using vulnerability_compliance table)
    st.markdown("### Risk Assessment / Compliance Summary")
    ra_stats = pd.read_sql_query("""
        SELECT
            COUNT(*) AS Total,
            SUM(CASE WHEN AwareOfCRA = 'Yes' THEN 1 ELSE 0 END) AS CRA_Aware,
            SUM(CASE WHEN CRACompliant = 'Yes' THEN 1 ELSE 0 END) AS CRA_Compliant,
            SUM(CASE WHEN KEVProcessExists = 'Yes' THEN 1 ELSE 0 END) AS KEV_OK,
            SUM(CASE WHEN DisclosureProcessSE = 'Yes' THEN 1 ELSE 0 END) AS Disclosure_OK
        FROM vulnerability_compliance
    """, conn)
    st.dataframe(ra_stats)

    st.markdown("### Compliance Progress")
    if ra_stats["Total"].iloc[0] > 0:
        st.progress(ra_stats["CRA_Compliant"].iloc[0] / ra_stats["Total"].iloc[0])

    # Support Requests Overview
    st.markdown("### Support Request Status")
    tracking_df = pd.read_sql_query("SELECT * FROM vulnerability_tracking", conn)
    open_reqs = tracking_df[tracking_df["AnswerDate"] == ""]
    closed_reqs = tracking_df[tracking_df["AnswerDate"] != ""]
    st.metric("Open Support Requests", len(open_reqs))
    st.metric("Closed Support Requests", len(closed_reqs))

elif choice == "Admin Panel":
    st.subheader("🛠 Admin Control Panel")

    st.markdown("### Metadata Templates")
    templates = pd.read_sql_query("SELECT * FROM metadata_templates", conn)
    st.dataframe(templates)

    st.markdown("### Add New Template")
    with st.form("add_template_form"):
        template_name = st.text_input("Template Name")
        db_bricks = st.text_input("DB Bricks (comma-separated)")
        se_bricks = st.text_input("SE Bricks (comma-separated)")
        chips = st.text_input("Chips (comma-separated)")
        it_stack = st.text_input("IT Stack")
        encryption_libs = st.text_input("Encryption Libraries")
        secure_boot = st.selectbox("Secure Boot Enabled?", ["Yes", "No"])
        save_template = st.form_submit_button("Add Template")

        if save_template:
            cur.execute("SELECT COALESCE(MAX(TemplateID), 0) + 1 FROM metadata_templates")
            new_id = cur.fetchone()[0]
            cur.execute("""
                INSERT INTO metadata_templates (
                    TemplateID, TemplateName, DBBricks, SEBricks, Chips,
                    ITStack, EncryptionLibs, SecureBoot
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (new_id, template_name, db_bricks, se_bricks, chips, it_stack, encryption_libs, secure_boot))


elif choice == "CRA Planning":
    st.subheader("📋 CRA Planning for Products")

    # List all products
    product_list = pd.read_sql_query("SELECT ProductID, ProductName FROM products", conn)
    selected_id = st.selectbox("Select Product", product_list["ProductID"].tolist(), format_func=lambda x: product_list[product_list["ProductID"] == x]["ProductName"].values[0])

    if selected_id:
        product = pd.read_sql_query(f"SELECT * FROM products WHERE ProductID = {selected_id}", conn).iloc[0]

        with st.form("cra_plan_form"):
            current_plan = product.get("CRAPlan", "")
            plan_option = st.selectbox("CRA Plan", ["EoL", "Stop Sell in EU", "Become Compliant"], index=["EoL", "Stop Sell in EU", "Become Compliant"].index(current_plan) if current_plan else 0)

            eol_date = None
            if plan_option == "EoL":
                eol_date = st.date_input("Planned End-of-Life Date")

            if plan_option == "Stop Sell in EU":
                st.warning("This plan requires VP approval and is flagged until approved.")
                approved = st.selectbox("Has the VP approved this stop-sell plan?", ["No", "Yes"])
                flagged = "No" if approved == "Yes" else "Yes"
            else:
                approved = ""
                flagged = ""

            submitted = st.form_submit_button("Save CRA Plan")

            if submitted:
                cur = conn.cursor()
                cur.execute("""
                    UPDATE products
                    SET CRAPlan = ?, CRA_EoL_Date = ?, CRA_StopSell_VPApproved = ?, CRA_StopSell_Flagged = ?
                    WHERE ProductID = ?
                """, (
                    plan_option,
                    eol_date.strftime("%Y-%m-%d") if plan_option == "EoL" and eol_date else "",
                    approved,
                    flagged,
                    selected_id
                ))
                conn.commit()
            cur.execute("UPDATE products SET CRAPlan = ?, CRA_EoL_Date = ?, CRA_StopSell_VPApproved = ?, CRA_StopSell_Flagged = ? WHERE ProductID = ?", (
                plan_option,
                eol_date.strftime("%Y-%m-%d") if plan_option == "EoL" and eol_date else "",
                approved,
                flagged,
                selected_id
            ))
            cur.execute("UPDATE products SET CRAPlan = ?, CRA_EoL_Date = ? WHERE ProductID = ?", (
                plan_option,
                eol_date.strftime("%Y-%m-%d") if plan_option == "EoL" and eol_date else "",
                selected_id
            ))


elif choice == "CRA Stop-Sell Flags":
    st.subheader("🚩 Products Requiring VP Attention for CRA Stop Sell")

    flagged_products = pd.read_sql_query("""
        SELECT ProductID, ProductName, CRAPlan, CRA_StopSell_VPApproved, CRA_StopSell_Flagged
        FROM products
        WHERE CRAPlan = 'Stop Sell in EU' AND CRA_StopSell_Flagged = 'Yes'
    """, conn)

    if flagged_products.empty:
		st.info("Shouldn't be here")
    else:
        st.warning("The following products are flagged for VP approval:")
        st.dataframe(flagged_products)
