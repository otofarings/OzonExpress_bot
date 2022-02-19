SQL_COMMANDS = {

    # *****Bot*****
    'start_up_bot': """
        INSERT INTO logs_bot_running (start_date) 
        VALUES($1);
    """,
    'turn_of_bot': """
        UPDATE logs_bot_running 
        SET finish_date = $1 
        WHERE id = (
            SELECT max(id) 
            FROM logs_bot_running
        );
    """,

    # *****Logging*****
    "button_click": """
        INSERT INTO logs_button_clicks 
        (date, tg_id, chat_id, message_id, from_user_tg_id, 
         first_name, last_name, username, button_name, button_data)
        VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
    """,

    # *****API*****
    'get_all_api': """
        SELECT *
        FROM api;
    """,
    'get_api': """
        SELECT *
        FROM api
        WHERE seller_id = (
            SELECT seller_id
            FROM employee
            WHERE tg_id = $1
        );
    """,
    'get_current_api': """
        SELECT *
        FROM api
        WHERE seller_id = (
            SELECT seller_id
            FROM employee
            WHERE tg_id = $1
        );
    """,
    'del_api': """
        DELETE FROM api
        WHERE seller_id = $1;
    """,
    'new_api': """
        INSERT INTO api (seller_id, api_key, seller_name, timezone, log_chat_id, warehouse_id)
        VALUES($1, $2, $3, $4, $5, $6);
    """,
    'update_api_key': """
        UPDATE api 
        SET api_key = $1 
        WHERE seller_id = $2;
    """,

    # *****Registration*****
    "new_creator": """
        INSERT INTO employee 
        (uuid, tg_id, username, state, function, begin_date)
        VALUES($1, $2, $3, $4, $5, $6)
        ON CONFLICT (uuid) DO NOTHING;
    """,
    'new_employee': """
        WITH src AS (
            INSERT INTO employee_stat
            (tg_id, orders_number, successful, unsuccessful)
            VALUES($2, 0, 0, 0)
            ON CONFLICT (tg_id) DO NOTHING
            RETURNING *
        )
        UPDATE employee
        SET tg_id = $2, username = $3, state = $4, begin_date = $6
        WHERE uuid = $1 
        AND state = $5;
    """,

    # *****Checking*****
    'check_state': """
        SELECT e.function, e.status, a.timezone
        FROM employee e, api a
        WHERE a.seller_id=e.seller_id
        AND e.tg_id = $1 
        AND e.state = $2
        AND a.seller_id IN (
            SELECT seller_id
            FROM employee
            WHERE tg_id = $1 
            AND state = $2
        );
    """,

    # *****Orders/delivery*****
    'get_all_orders': """
        SELECT posting_number, status, cancel_reason_id
        FROM order_info 
        WHERE warehouse_id = $1
        ORDER BY shipment_date;
    """,
    'update_order': """
        UPDATE order_info 
        SET status = $2, cancel_reason_id = $3
        WHERE posting_number = $1;
    """,
    'get_quantity_of_orders': """
        SELECT count(posting_number)
        FROM order_info 
        WHERE status = $2
        AND warehouse_id IN (
            SELECT warehouse_id
            FROM employee
            WHERE tg_id = $1
        );
    """,
    'orders_reserve_package': """
            WITH updated AS (
            UPDATE order_info 
            SET status = $3, packer_id = $1
            WHERE status = $2
            AND warehouse_id IN (
                SELECT warehouse_id
                FROM employee
                WHERE tg_id = $1
            )
            RETURNING *
        )
        SELECT u.posting_number, u.address, u.shipment_date, u.in_process_at, 
               u.latitude, u.longitude, u.customer_name, u.customer_phone, u.customer_comment,
               count(o.name), sum(o.quantity)
        FROM updated u, order_list o
        WHERE u.posting_number = o.posting_number
        AND u.status = $3
        AND u.warehouse_id IN (
            SELECT warehouse_id
            FROM employee
            WHERE tg_id = $1
        )
        GROUP BY (u.posting_number, u.address, u.shipment_date, u.in_process_at, 
                  u.latitude, u.longitude, u.customer_name, u.customer_phone, 
                  u.customer_comment)
        ORDER BY u.shipment_date;
    """,
    'orders_awaiting_delivery': """
        SELECT posting_number, latitude, longitude
        FROM order_info 
        WHERE status = $2
        AND warehouse_id IN (
            SELECT warehouse_id
            FROM employee
            WHERE tg_id = $1
        )
        ORDER BY shipment_date;
    """,
    'orders_reserve_delivery': """
            WITH updated AS (
            UPDATE order_info 
            SET status = $3, deliver_id = $2
            WHERE posting_number = ANY($1)
            RETURNING *
        )
        SELECT posting_number, address, shipment_date
        FROM updated
        WHERE status = $3
        AND warehouse_id IN (
            SELECT warehouse_id
            FROM employee
            WHERE tg_id = $2
        )
        ORDER BY shipment_date;
    """,
    'get_info_reserved_for_delivering': """
        SELECT posting_number, address, shipment_date, latitude, longitude
        FROM order_info
        WHERE posting_number = $1
        AND status = $2;
    """,
    'start_delivering': """
            WITH updated AS (
            UPDATE order_info 
            SET status = $3, start_delivery_date = $4
            WHERE posting_number = ANY($1)
            AND deliver_id = $2
            RETURNING *
        )
        SELECT order_id, posting_number, address, addressee_name, addressee_phone, 
               customer_comment, shipment_date, latitude, longitude
        FROM updated
        WHERE status = $3
        AND warehouse_id IN (
            SELECT warehouse_id
            FROM employee
            WHERE tg_id = $2
        );
    """,
    'complete_delivery': """
            WITH updated AS (
            UPDATE order_info 
            SET status = $2, finish_delivery_date = $3
            WHERE posting_number = $1
            RETURNING *
        )
        INSERT INTO logs_status_changes
        (date, status, status_ozon_seller, posting_number)
        VALUES($3, $2, $4, $1);
    """,
    'get_orders': """
        SELECT posting_number
        FROM order_info 
        WHERE status = $2 
        AND date_created > $3
        AND warehouse_id IN (
            SELECT warehouse_id
            FROM employee
            WHERE seller_id = $1
        );
    """,
    'get_orders_for_polling': """
        SELECT posting_number, status, cancel_reason_id
        FROM order_info 
        WHERE date_created > $2
        AND warehouse_id IN (
            SELECT warehouse_id
            FROM employee
            WHERE seller_id = $1
        );
    """,
    'get_orders_by_tg_id': """
        SELECT posting_number, packer_id, status
        FROM order_info 
        WHERE in_process_at > $2
        AND warehouse_id IN (
            SELECT warehouse_id
            FROM employee
            WHERE tg_id = $1
        );
    """,
    'complete_packaging': """
            WITH updated AS (
            UPDATE order_info 
            SET status = $2, finish_package_date = $3
            WHERE posting_number = $1
            RETURNING *
        )
        INSERT INTO logs_status_changes
        (date, status, status_ozon_seller, posting_number)
        VALUES($3, $2, $4, $1);
    """,
    'cancel_packaging': """
            WITH updated AS (
            UPDATE order_info 
            SET status = $2, finish_package_date = $3, 
                cancel_reason_id = $5, cancel_reason = $6, 
                cancellation_type = $7, cancellation_initiator = $8
            WHERE posting_number = $1
            RETURNING *
        )
        INSERT INTO logs_status_changes
        (date, status, status_ozon_seller, posting_number)
        VALUES($3, $2, $4, $1);
    """,
    'get_orders_all': """
            SELECT posting_number
            FROM order_info
    """,
    'update_employee': """
         UPDATE employee_stat  
         SET orders_number + 1, successful + 1
         WHERE id = $1;
    """,
    'create_moderator': """
        INSERT INTO employee 
        (uuid, state, name, function, added_by_id)
        VALUES($1, $2, $3, $4, $5);
    """,
    'get_moderator': """
        SELECT id, name
        FROM employee 
        WHERE function = $1 
        AND state != $2;
    """,
    'get_employee': """
        SELECT name, id
        FROM employee 
        WHERE seller_id = $1 
        AND function = $2 
        AND state != $3;
    """,
    'get_employee_special_v2': """
        SELECT name, id
        FROM employee 
        WHERE function = $2 
        AND state != $3
        AND warehouse_id IN (
            SELECT warehouse_id
            FROM employee
            WHERE tg_id = $1
        );
    """,
    'get_employee_special': """
        SELECT name, id
        FROM employee 
        WHERE tg_id != $1
        AND state != $2
        AND state != $3
        AND function IN (
            SELECT function
            FROM employee
            WHERE tg_id = $1
        )
        AND warehouse_id IN (
            SELECT warehouse_id
            FROM employee
            WHERE tg_id = $1
        );
    """,
    'get_employee_info': """
        SELECT *
        FROM employee 
        WHERE id = $1;
    """,
    'get_employee_by_tg_id': """
        SELECT *
        FROM employee 
        WHERE tg_id = $1;
    """,
    'create_user': """
        INSERT INTO employee 
        (uuid, warehouse_id, seller_id, name, phone, state, function, added_by_id)
        VALUES($1, $2, $3, $4, $5, $6, $7, $8);
    """,
    'delete_employee': """
        UPDATE employee  
        SET state = $1, end_date = $2
        WHERE id = $3;
    """,
    'delete_new_employee': """
        UPDATE employee  
        SET state = $1, end_date = $2
        WHERE uuid = $3;
    """,
    'update_msg_id': """
        UPDATE employee 
        SET msg_id = $1 
        WHERE tg_id = $2 AND state != $3
        RETURNING (
            SELECT msg_id 
            FROM employee 
            WHERE tg_id = $2 AND state != $3
        );
    """,
    'get_msg_id': """
        SELECT msg_id 
        FROM employee 
        WHERE tg_id = $1 AND state != $2;
    """,
    'get_orders_for_packaging': """
        SELECT order_id, posting_number, address, date_shipment
        FROM order_info 
        WHERE status = $2
        AND warehouse_id IN (
            SELECT warehouse_id
            FROM employee
            WHERE tg_id = $1
        )
        ORDER BY date_shipment;
    """,
    'get_orders_and_reserved_for_delivering': """
            WITH updated AS (
            UPDATE order_info 
            SET status = $3, deliver_id = $1
            WHERE status = $2
            AND warehouse_id IN (
                SELECT warehouse_id
                FROM employee
                WHERE tg_id = $1
            )
            RETURNING *
        )
        SELECT order_id, posting_number, address, date_shipment
        FROM updated
        ORDER BY date_shipment ASC;
    """,
    'get_reserved_orders_for_delivering': """
        SELECT order_id, posting_number, address, date_shipment 
        FROM order_info 
        WHERE status = $2
        AND warehouse_id IN (
            SELECT warehouse_id
            FROM employee
            WHERE tg_id = $1
        );
    """,
    'remove_reserve_orders_for_packaging': """
            WITH updated AS (
            UPDATE order_info 
            SET status = $3, packer_id = $4
            WHERE status = $2
            AND packer_id = $1
            RETURNING *
        )
        SELECT count(posting_number)
        FROM updated
        WHERE status = $3
        AND warehouse_id IN (
            SELECT warehouse_id
            FROM employee
            WHERE tg_id = $1
        );
    """,
    'start_packaging': """
            WITH updated AS (
            UPDATE order_info 
            SET status = $3, start_package_date = $7
            WHERE posting_number = $1
            RETURNING *
        )
        UPDATE order_info
        SET status = $4, packer_id = $6
        WHERE status = $2
        AND packer_id = $5
        AND posting_number != $1;
    """,
    'reserve_order_by_admin': """
        UPDATE order_info 
        SET status = $2, packer_id = $3
        WHERE posting_number = $1
        AND status = $4;
    """,
    'remove_reserve_orders_for_delivering': """
            WITH updated AS (
            UPDATE order_info 
            SET status = $3, deliver_id = $4
            WHERE status = $2
            AND deliver_id = $1
            RETURNING *
        )
        SELECT count(posting_number)
        FROM updated
        WHERE status = $3
        AND warehouse_id IN (
            SELECT warehouse_id
            FROM employee
            WHERE tg_id = $1
        );
    """,

    'get_order_quantity': """
        SELECT sum(fact_quantity), count(order_id)
        FROM order_list 
        WHERE posting_number = $1;
    """,
    'get_order_list': """
        SELECT *
        FROM order_list 
        WHERE posting_number = $1
        ORDER BY name;
    """,
    'update_order_list': """
        UPDATE order_list
        SET fact_quantity = $2 
        WHERE name = $1
        AND posting_number = $3;
    """,

    'get_order_info': """
        SELECT *
        FROM order_info 
        WHERE posting_number = $1;
    """,
    'delete_order': """
        DELETE FROM order_info  
        WHERE posting_number = $1;
    """,
    'reset_order': """
        UPDATE order_info
        SET status = $2, 
        packer_id = $3, start_package_date = $4, finish_package_date = $5, 
        deliver_id = $6, start_delivery_date = $7, finish_delivery_date = $8, 
        successfully = $9, non_delivery_reason = $10
        WHERE posting_number = $1;
    """,
    'reassign_packer_order': """
        UPDATE order_info
        SET packer_id = $2, start_package_date = $3
        WHERE posting_number = $1;
    """,
    'employee_stat': """
        SELECT a.seller_name, e.seller_id
        FROM api a, employee e
        WHERE a.seller_id = e.seller_id
    """,
    'employee_stat_demo': """
        SELECT a.seller_name, a.seller_id
        FROM api a
        WHERE a.seller_id = $1
        LIMIT 1
    """,
    "new_order": """
        WITH src AS (
                INSERT INTO order_info 
                (posting_number, order_id, order_number, warehouse_id, status, 
                address, zip_code, latitude, longitude, 
                customer_id, customer_name, customer_phone, customer_email, customer_comment, 
                addressee_name, addressee_phone, in_process_at, shipment_date, 
                cancel_reason_id, cancel_reason, cancellation_type, cancelled_after_ship, 
                affect_cancellation_rating, cancellation_initiator)
                VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, 
                       $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24)
                ON CONFLICT (posting_number) DO UPDATE
                SET status = $5, customer_comment = $14, cancel_reason_id = $19, cancel_reason = $20, 
                    cancellation_type = $21, cancelled_after_ship = $22, affect_cancellation_rating = $23, 
                    cancellation_initiator = $24
                RETURNING *
            )
        INSERT INTO logs_status_changes (date, status, status_ozon_seller, posting_number) 
        VALUES($25, $5, $5, $1);
    """,
    "new_products": """
        INSERT INTO order_list (order_id, posting_number, sku, name, 
                                offer_id, quantity, price, fact_quantity, changed) 
        VALUES($1, $2, $3, $4, $5, $6, $7, $6, $8);
    """
}
