# Data dictionary: Customer 360

All files are group totals for 20 Nov 2024 to 19 Nov 2026, adult customers only. Amounts in $ (the source states no currency).
Rates are fractions (0.12 = 12%). Empty cells are suppressed groups under 50 customers.

| File | One row per | Key columns |
|---|---|---|
| `segments.csv` | customer group | `customers`, `net_revenue`, `gross_margin`, `orders`, `aov`, `revenue_per_customer`, `return_rate`, `net_revenue_12m` (last 12 months), `visiting_customers` (visited in the window), `definition`, `action` |
| `segment_channel.csv` | group × preferred channel | `customers`, `net_revenue` |
| `channels.csv` | purchase channel | `net_revenue`, `revenue_share`, `product_cost`, `gross_margin`, `gm_pct`, `return_rate`, `cancel_rate`, `aov`, `sessions`, `visit_to_cart`, `visit_to_purchase`, `cart_to_purchase`, `repeat_rate_first_channel`, `preferred_by_buyers`, `preferred_share` |
| `acquisition_channels.csv` | first channel (how the customer found the shop) | `registered`, `buyers`, `repeat_buyers`, `net_revenue`, `buyer_rate`, `repeat_rate`, `revenue_per_buyer`, `gm_pct` |
| `demographics.csv` | region, age band or gender (`dim`, `val`) | `customers`, `buyers`, `net_revenue`, `gross_margin`, `revenue_per_buyer`, `gm_pct`, `return_rate` |
| `region_channel.csv` | region × preferred channel (buyers only) | `customers` |
| `categories.csv` | product category (department) | `net_revenue`, `gross_margin`, `gm_pct`, `returned_value`, `return_rate` |
| `monthly_by_channel.csv` | month | net revenue per purchase channel, total `gross_margin` |

## Definitions

| Term | Meaning |
|---|---|
| Net revenue | Sale value of items not cancelled and not returned |
| Gross sales | Sale value of items not cancelled (base for return rate) |
| Gross margin | Net revenue minus product cost of those items |
| Return rate | Returned value ÷ gross sales |
| Cancellation rate | Cancelled value ÷ (gross sales + cancelled value) |
| Purchase channel | Channel of the purchase visit closest to the order (within 24 h): Email, Google Ads, Facebook, YouTube, Organic |
| Preferred channel | Channel of most of a customer's visits; ties go to the most recent visit, then channel name (A–Z). "No visits" if none in the window |
| First channel | `traffic_source` at sign-up: Search, Organic, Facebook, Email, Display |
| Champions | 3+ orders, last order within 180 days |
| Loyal | 2 orders, last order within 180 days |
| At risk | 2+ orders, last order more than 180 days ago |
| New | 1 order, placed in the last 90 days |
| One-time buyers | 1 order, placed more than 90 days ago |
| Lapsed | No order in the window, but bought before it |
| Never bought | Registered, no order ever |
