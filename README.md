# Web Mercantile Warehouse Lease Optimizer

A Streamlit web app that solves the Web Mercantile warehouse-space leasing problem as a linear program.

## Original problem

Monthly required warehouse space:

| Month | Required space (sq ft) |
|---:|---:|
| 1 | 30,000 |
| 2 | 20,000 |
| 3 | 40,000 |
| 4 | 10,000 |
| 5 | 50,000 |

Lease cost per square foot:

| Lease length | Cost per sq ft |
|---:|---:|
| 1 month | $65 |
| 2 months | $100 |
| 3 months | $135 |
| 4 months | $160 |
| 5 months | $190 |

The app uses `scipy.optimize.linprog` to minimize total leasing cost while ensuring enough active leased space in every month.

For the original data, the minimum cost is **$7,650,000**.

One optimal solution is:

- Month 1: lease 30,000 sq ft for 5 months
- Month 3: lease 10,000 sq ft for 1 month
- Month 5: lease 20,000 sq ft for 1 month

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Put it on GitHub

1. Create a new GitHub repository.
2. Upload:
   - `app.py`
   - `requirements.txt`
   - `.streamlit/config.toml`
   - `README.md`
3. Commit the files to the main branch.

Example terminal workflow:

```bash
git init
git add .
git commit -m "Build warehouse lease optimization app"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
git push -u origin main
```

## Deploy with Streamlit Community Cloud

1. Sign in to Streamlit Community Cloud with GitHub.
2. Click **Create app**.
3. Select the GitHub repository and branch.
4. Set the main file path to `app.py`.
5. Deploy.

The app allows users to edit the requirements and leasing costs, solve the model, inspect the optimal lease plan, verify monthly capacity, and download the solution as a CSV.
