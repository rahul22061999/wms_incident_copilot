SKILLS = {

    "inventory": {

        "description": "Schema and query guidance for on-hand inventory, case-level stock, SKU/location lookups, and inventory totals.",
        "content": """
# Inventory Lookup
# Follow guideline strictly
## Tables

### wms1.inventory
- id (PRIMARY KEY)
- case_number (UNIQUE)
- sku
- unit_qty
- location
- wrkref
- dtl_num
- ins_dt

## Use Cases
- How much inventory do we have for a SKU?
- Where is a SKU stored?
- Which cases contain a SKU?
- What inventory is tied to a work reference or detail number?

## Business Rules
- unit_qty is the quantity stored in a case-level inventory record.
- Total on-hand inventory for a SKU = SUM(unit_qty) from wms1.inventory.
- Inventory can be grouped by sku, location, case_number, wrkref, or dtl_num.
- case_number is unique per inventory record.
- SKUS are SKU###
- SKUS are all in uppercase only

## Example Queries

-- Total inventory for a SKU
SELECT
    sku,
    SUM(unit_qty) AS total_inventory
FROM wms1.inventory
WHERE sku = 'SKU004'
GROUP BY sku;

-- Inventory by location for a SKU
SELECT
    sku,
    location,
    SUM(unit_qty) AS total_units
FROM wms1.inventory
WHERE sku = 'SKU004'
GROUP BY sku, location
ORDER BY total_units DESC;

-- Case-level inventory for a SKU
SELECT
    case_number,
    sku,
    unit_qty,
    location,
    wrkref,
    dtl_num
FROM wms1.inventory
WHERE sku = 'SKU004'
ORDER BY ins_dt DESC;
""",
        "table_name": "wms1.inventory",
    },
    "outbound": {
        "description": "Schema and query guidance for outbound pick work, order allocation, pending picks, and picked quantities.",
        "content": """
# Outbound Picking

## Tables

### wms1.pckwrk
- id
- wrkref
- location
- sku
- dtl_num
- quantity
- pck_qty
- app_qty
- carton_number
- pck_dt
- status
- ins_dt
- order_number

## Use Cases
- Pending pick work
- Requested vs picked quantity
- Picked units over time
- Warehouse-level hourly pick volume

## Business Rules
- quantity = requested quantity
- pck_qty = picked quantity
- pck_dt = pick timestamp
- Warehouse average UPH for the last 24 hours can be approximated as total picked units in last 24 hours divided by 24
- This table does not support true user-level UPH because there is no picker/operator field

## Example Queries

-- Warehouse average UPH over last 24 hours
SELECT
    SUM(COALESCE(pck_qty, 0)) AS total_units_picked_24h,
    SUM(COALESCE(pck_qty, 0)) / 24.0 AS avg_uph_24h
FROM wms1.pckwrk
WHERE pck_dt >= NOW() - INTERVAL '24 hours'
  AND COALESCE(pck_qty, 0) > 0;

-- Hourly picked units over last 24 hours
SELECT
    DATE_TRUNC('hour', pck_dt) AS hour_bucket,
    SUM(COALESCE(pck_qty, 0)) AS units_picked
FROM wms1.pckwrk
WHERE pck_dt >= NOW() - INTERVAL '24 hours'
  AND COALESCE(pck_qty, 0) > 0
GROUP BY DATE_TRUNC('hour', pck_dt)
ORDER BY hour_bucket;
""",
        "table_name": "wms1.pckwrk",
    },
    "inbound": {
        "description": "Schema and query guidance for receipts, expected vs received quantities, receiving locations, and inbound status tracking.",
        "content": """
# Inbound Receiving

## Tables

### wms1.rcv_inventory
- rcv_id (PRIMARY KEY)
- rcv_inv
- warehouse_id
- sku
- supplier_number
- expected_qty
- received_qty
- received_date
- receiving_loc
- status
- created_at

## Use Cases
- What receipts exist for a SKU?
- How much was expected vs received?
- Which receiving location was used?
- Which receipts are pending, partial, received, or cancelled?

## Business Rules
- expected_qty is the planned receipt quantity.
- received_qty is the actual received quantity recorded.
- status is one of: PENDING, PARTIAL, RECEIVED, CANCELLED.
- Quantity variance can be checked as expected_qty - received_qty.

## Example Queries

-- Receipt history for a SKU
SELECT
    rcv_inv,
    warehouse_id,
    sku,
    supplier_number,
    expected_qty,
    received_qty,
    receiving_loc,
    status,
    received_date
FROM wms1.rcv_inventory
WHERE sku = 'SKU004'
ORDER BY created_at DESC;

-- Open inbound receipts
SELECT
    rcv_inv,
    sku,
    expected_qty,
    received_qty,
    status
FROM wms1.rcv_inventory
WHERE status IN ('PENDING', 'PARTIAL')
ORDER BY created_at DESC;

-- Receipt variance for a SKU
SELECT
    rcv_inv,
    sku,
    expected_qty,
    received_qty,
    (expected_qty - received_qty) AS variance_qty,
    status
FROM wms1.rcv_inventory
WHERE sku = 'SKU004'
ORDER BY created_at DESC;
""",
        "table_name": "wms1.rcv_inventory",
    },
}