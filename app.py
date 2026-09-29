import streamlit as st
import pandas as pd
import numpy as np
from scipy.optimize import linprog

st.set_page_config(
    page_title="Web Mercantile Warehouse Optimizer",
    page_icon="🏭",
    layout="wide",
)

st.title("Web Mercantile Warehouse Lease Optimizer")
st.caption(
    "Find the least-cost combination of warehouse leases that meets monthly space requirements."
)

DEFAULT_REQUIREMENTS = pd.DataFrame(
    {
        "Month": [1, 2, 3, 4, 5],
        "Required Space (sq ft)": [30000, 20000, 40000, 10000, 50000],
    }
)

DEFAULT_COSTS = pd.DataFrame(
    {
        "Lease Length (months)": [1, 2, 3, 4, 5],
        "Cost per sq ft": [65, 100, 135, 160, 190],
    }
)

with st.sidebar:
    st.header("Model")
    st.write(
        "Decision variables represent square feet leased in a given month "
        "for a specified number of months."
    )
    st.markdown(
        """
        **Objective**

        Minimize total leasing cost.

        **Constraint**

        In every month, active leased space must be at least the required space.
        """
    )
    st.divider()
    st.info("All lease quantities are continuous square feet and cannot be negative.")

st.subheader("1. Enter the problem data")

left, right = st.columns(2)

with left:
    st.markdown("#### Monthly space requirements")
    requirements_df = st.data_editor(
        DEFAULT_REQUIREMENTS,
        hide_index=True,
        use_container_width=True,
        num_rows="fixed",
        key="requirements",
    )

with right:
    st.markdown("#### Lease costs")
    costs_df = st.data_editor(
        DEFAULT_COSTS,
        hide_index=True,
        use_container_width=True,
        num_rows="fixed",
        key="costs",
    )

def validate_inputs(requirements_df, costs_df):
    req = requirements_df["Required Space (sq ft)"].astype(float).to_numpy()
    cost = costs_df["Cost per sq ft"].astype(float).to_numpy()

    if len(req) != len(cost):
        raise ValueError(
            "For this app, the number of lease-length options must match the number of planning months."
        )
    if np.any(req < 0):
        raise ValueError("Space requirements cannot be negative.")
    if np.any(cost < 0):
        raise ValueError("Lease costs cannot be negative.")
    return req, cost

def solve_warehouse_lp(requirements, lease_costs):
    n_months = len(requirements)

    # Each variable is (start_month, lease_length).
    variables = []
    objective = []

    for start in range(1, n_months + 1):
        for length in range(1, n_months - start + 2):
            variables.append((start, length))
            objective.append(float(lease_costs[length - 1]))

    # coverage[m, j] = 1 if lease j is active during month m.
    coverage = np.zeros((n_months, len(variables)))

    for j, (start, length) in enumerate(variables):
        for month in range(start, start + length):
            coverage[month - 1, j] = 1

    # scipy.linprog uses <= constraints.
    # coverage @ x >= requirements becomes -coverage @ x <= -requirements.
    result = linprog(
        c=np.array(objective),
        A_ub=-coverage,
        b_ub=-requirements,
        bounds=[(0, None)] * len(variables),
        method="highs",
    )

    return result, variables, coverage, np.array(objective)

st.subheader("2. Optimize")

if st.button("Solve optimization model", type="primary", use_container_width=True):
    try:
        requirements, lease_costs = validate_inputs(requirements_df, costs_df)
        result, variables, coverage_matrix, objective = solve_warehouse_lp(
            requirements, lease_costs
        )

        if not result.success:
            st.error(f"The optimization model could not be solved: {result.message}")
            st.stop()

        solution = np.where(result.x < 1e-7, 0, result.x)
        monthly_space = coverage_matrix @ solution
        excess_space = monthly_space - requirements

        lease_rows = []
        for (start, length), qty, unit_cost in zip(variables, solution, objective):
            if qty > 1e-6:
                lease_rows.append(
                    {
                        "Start Month": start,
                        "Lease Length (months)": length,
                        "End Month": start + length - 1,
                        "Space Leased (sq ft)": qty,
                        "Cost per sq ft": unit_cost,
                        "Lease Cost": qty * unit_cost,
                    }
                )

        leases_df = pd.DataFrame(lease_rows)

        monthly_df = pd.DataFrame(
            {
                "Month": np.arange(1, len(requirements) + 1),
                "Required Space": requirements,
                "Leased Space Available": monthly_space,
                "Excess Space": excess_space,
            }
        )

        st.session_state["result"] = {
            "total_cost": float(result.fun),
            "leases_df": leases_df,
            "monthly_df": monthly_df,
        }

    except Exception as exc:
        st.error(str(exc))

if "result" in st.session_state:
    result_data = st.session_state["result"]
    total_cost = result_data["total_cost"]
    leases_df = result_data["leases_df"]
    monthly_df = result_data["monthly_df"]

    st.subheader("3. Optimal solution")

    c1, c2, c3 = st.columns(3)
    c1.metric("Minimum total leasing cost", f"${total_cost:,.0f}")
    c2.metric(
        "Number of leases used",
        f"{len(leases_df):,}",
    )
    c3.metric(
        "Total sq ft initiated",
        f"{leases_df['Space Leased (sq ft)'].sum():,.0f}",
    )

    st.markdown("#### Lease plan")
    display_leases = leases_df.copy()
    for col in ["Space Leased (sq ft)", "Cost per sq ft", "Lease Cost"]:
        display_leases[col] = display_leases[col].map(
            lambda x: f"{x:,.0f}" if col == "Space Leased (sq ft)" else f"${x:,.0f}"
        )
    st.dataframe(display_leases, hide_index=True, use_container_width=True)

    st.markdown("#### Monthly capacity check")
    display_monthly = monthly_df.copy()
    for col in ["Required Space", "Leased Space Available", "Excess Space"]:
        display_monthly[col] = display_monthly[col].map(lambda x: f"{x:,.0f}")
    st.dataframe(display_monthly, hide_index=True, use_container_width=True)

    chart_df = monthly_df.set_index("Month")[["Required Space", "Leased Space Available"]]
    st.bar_chart(chart_df)

    st.markdown("#### Interpretation")
    if len(requirements_df) == 5 and np.allclose(
        requirements_df["Required Space (sq ft)"].astype(float).to_numpy(),
        [30000, 20000, 40000, 10000, 50000],
    ) and np.allclose(
        costs_df["Cost per sq ft"].astype(float).to_numpy(),
        [65, 100, 135, 160, 190],
    ):
        st.success(
            "For the original Web Mercantile data, the minimum total cost is "
            f"${total_cost:,.0f}. One optimal plan is to lease 30,000 sq ft "
            "starting in Month 1 for five months, add 10,000 sq ft for Month 3, "
            "and add 20,000 sq ft for Month 5."
        )
    else:
        st.write(
            "The table above shows the least-cost lease combination for the values "
            "currently entered."
        )

    st.download_button(
        "Download optimal lease plan as CSV",
        data=leases_df.to_csv(index=False).encode("utf-8"),
        file_name="optimal_warehouse_lease_plan.csv",
        mime="text/csv",
        use_container_width=True,
    )

with st.expander("How the linear programming model works"):
    st.markdown(
        r"""
Let \(x_{s,\ell}\) be the square feet leased beginning in month \(s\)
for \(\ell\) months.

The model minimizes:

\[
\text{Total Cost}
=
\sum_{s,\ell} c_{\ell}x_{s,\ell}
\]

subject to one coverage constraint for each month:

\[
\sum_{\text{leases active in month }m} x_{s,\ell}
\geq R_m
\]

where \(R_m\) is the warehouse space required in month \(m\).

All decision variables satisfy:

\[
x_{s,\ell}\geq 0
\]
"""
    )
