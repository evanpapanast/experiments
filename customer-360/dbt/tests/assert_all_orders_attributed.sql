-- Integrity: every order line is linked to a purchase visit, so its channel is known.
select order_item_id from {{ ref('stg_order_items') }} where purchase_channel = 'Unattributed'
