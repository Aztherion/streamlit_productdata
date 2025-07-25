def run():
    import streamlit as st
    import sqlite3
    from datetime import date

    st.header("Requirements Gap Assessment")

    frameworks = ["RED", "CRA", "NIS2", "EU Data Act", "IEC 62443-1", "IEC 62443-2", "IEC 62443-3"]
    statuses = [
        "Not Yet Assessed",
        "Implementing",
        "Covered by Another Product",
        "Implemented",
        "Will Be Implemented",
        "Will Not Implement"
    ]

    conn = sqlite3.connect("app.db")
    cur = conn.cursor()

    cur.execute("CREATE TABLE IF NOT EXISTS products (ProductID INTEGER PRIMARY KEY, ProductName TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS requirements (RequirementID INTEGER PRIMARY KEY, Framework TEXT, RequirementText TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS requirement_assessments (ProductID INTEGER, RequirementID INTEGER, Status TEXT, StartDate TEXT, EndDate TEXT, CoveredByProductID INTEGER, PRIMARY KEY (ProductID, RequirementID))")

    cur.execute("SELECT ProductID, ProductName FROM products")
    products = cur.fetchall()
    product_dict = {name: pid for pid, name in products}
    if not product_dict:
        st.warning("No products available. Please add a product first.")
        return
    selected_product_name = st.selectbox("Select Product", list(product_dict.keys()))
    selected_product_id = product_dict[selected_product_name]

    st.subheader("Framework Requirement Assessment")

    for fw in frameworks:
        with st.expander(f"{fw} Requirements"):
            cur.execute("SELECT RequirementID, RequirementText FROM requirements WHERE Framework = ?", (fw,))
            reqs = cur.fetchall()
            for req_id, req_text in reqs:
                st.markdown(f"**{req_text}**")
                status = st.selectbox(f"Status for '{req_text}'", statuses, key=f"{fw}_{req_id}_status")

                start_date, end_date, alt_product = None, None, None
                if status in ["Implementing", "Will Be Implemented"]:
                    col1, col2 = st.columns(2)
                    with col1:
                        start_date = st.date_input("Start Date", key=f"{fw}_{req_id}_start")
                    with col2:
                        end_date = st.date_input("Planned Completion", key=f"{fw}_{req_id}_end")
                elif status == "Covered by Another Product":
                    alt_product = st.selectbox("Select Covering Product", list(product_dict.keys()), key=f"{fw}_{req_id}_cover")

                cur.execute("""
                    INSERT INTO requirement_assessments
                    (ProductID, RequirementID, Status, StartDate, EndDate, CoveredByProductID)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(ProductID, RequirementID) DO UPDATE SET
                        Status = excluded.Status,
                        StartDate = excluded.StartDate,
                        EndDate = excluded.EndDate,
                        CoveredByProductID = excluded.CoveredByProductID
                """, (
                    selected_product_id,
                    req_id,
                    status,
                    start_date.strftime("%Y-%m-%d") if start_date else None,
                    end_date.strftime("%Y-%m-%d") if end_date else None,
                    product_dict.get(alt_product) if alt_product else None
                ))

    conn.commit()
    st.success("Assessment data saved.")