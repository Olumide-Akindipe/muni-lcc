# Inputs (codebook)

*Plain-language header: the list of every field a project file can contain. Open it when you set up a real project. The worked example in `examples/project.json` fills in every field.*

A project is one JSON file. Any section may be omitted; the report section needs the sections its objectives refer to.

## Top level

| Field | Type | Meaning |
|---|---|---|
| `confidence` | number | Confidence level for all uncertainty results. Default 0.90. FEMP v5.0 leaves the choice to the customer and treats 0.80 as the minimum (Section 5.3.2); use the value in the project M&V plan |
| `option_a` | list | Option A measures |
| `option_c` | object | Option C settings |
| `lcc` | object | Life-cycle cost study |
| `award`, `objectives`, `costs`, `significant_developments` | | Performance report |

## Option C billing CSV

One row per billing period. Columns: `period` (label), `days` (length of period), `energy` (total use in the period, any unit, consistent across files), `mean_temp` (mean outdoor dry-bulb temperature over the period, F or C, consistent across files).

`option_c` fields: `baseline_csv`, `reporting_csv`, `energy_units`, optional `force_model` (mean, 2P, 3PC, 3PH, 4P, 5P), optional `acceptance_criteria` (path to a criteria JSON).

## Option A measure

| Field | Meaning |
|---|---|
| `name` | Measure name, used to reference results |
| `baseline`, `reporting` | `{name, readings[], units}`: field measurements of the key parameter |
| `stipulated` | `{name, value, units, basis}`: basis is required |
| `interactive_factor` | Optional multiplier, default 1.0 |
| `savings_units` | Label, default kWh/yr |

## LCC

`study_period_years` (1 to 40), `real_discount_rate`, `midyear` (true or false), and `base` and `alternative`, each with:

* `initial_investment` (base-year dollars)
* `annual_costs`: `{name, category: energy | water | omr, amount, escalation}` or `{..., indices: [...]}` for a price index series, or `{name, category, quantity_source, unit_price}` to take the annual quantity from verified results. Quantity sources: `option_c:adjusted_baseline`, `option_c:reporting_actual` (annualized to 365 days), `option_a:<measure>:baseline_annual`, `option_a:<measure>:reporting_annual`.
* `one_time_costs`: `{name, amount, year, category: replacement | omr | residual}`

## Report

* `award`: `award_id`, `agency`, `recipient`, `project`, `is_subrecipient`, `period_of_performance_end`, `reporting_period {start, end, frequency: annual | semiannual | quarterly | final}`.
* `objectives[]`: `id`, `description`, `metric`, `units`, `target`, `actual_source` (`value` with `actual`, `option_c`, `option_a:<measure>`, or `lcc:net_savings`), `reason_not_met`.
* `costs`: `budget`, `actual_cost`, `planned_units`, `unit`, `unit_basis_source` (same forms as `actual_source`), `unit_cost_tolerance` (default 0.10), `explanation`.
* `significant_developments[]`: `type` (beneficial or adverse), `summary`, `corrective_action`, `assistance_needed`.
