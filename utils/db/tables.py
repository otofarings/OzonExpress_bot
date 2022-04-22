logs_bot_running = """CREATE TABLE IF NOT EXISTS logs_bot_running 
                      (id          SERIAL PRIMARY KEY,
                       start_date  TIMESTAMP, 
                       finish_date TIMESTAMP);"""

api = """CREATE TABLE IF NOT EXISTS api 
         (seller_id    BIGINT PRIMARY KEY,
          warehouse_id BIGINT,
          api_key      TEXT,
          seller_name  TEXT,
          timezone     TEXT,
          log_chat_id  TEXT,
          channel_id   TEXT,
          status       TEXT);"""

employee = """CREATE TABLE IF NOT EXISTS employee 
              (id            SERIAL,
               uuid          TEXT PRIMARY KEY,
               tg_id         BIGINT,
               msg_id        BIGINT,
               warehouse_id  BIGINT,
               seller_id     BIGINT,
               name          TEXT,
               username      TEXT,
               phone         TEXT,
               state         TEXT, 
               function      TEXT,
               status        TEXT,
               begin_date    TIMESTAMP,
               added_by_id   BIGINT,
               end_date      TIMESTAMP,
               deleted_by_id INT);"""

order_info = """CREATE TABLE IF NOT EXISTS order_info 
                (posting_number            TEXT PRIMARY KEY,
                 order_id                  BIGINT,
                 order_number              TEXT,
                 
                 received_date             TEXT,
                 message_id                BIGINT,
                 channel_id                TEXT,
                 message_channel_id        BIGINT,
                
                 warehouse_id              BIGINT,
                 status                    TEXT,
                 status_api                TEXT,
                 current_status            TEXT,
                
                 address                   TEXT,
                 zip_code                  TEXT,
                 latitude                  FLOAT,
                 longitude                 FLOAT, 
                
                 customer_id               BIGINT,
                 customer_name             TEXT,
                 customer_phone            TEXT,
                 customer_email            TEXT,
                 customer_comment          TEXT,
                 addressee_name            TEXT,
                 addressee_phone           TEXT,
                
                 in_process_at             TIMESTAMP,
                 shipment_date             TIMESTAMP,
                 packer_id                 BIGINT,
                 start_package_date        TIMESTAMP,
                 finish_package_date       TIMESTAMP,
                 deliver_id                BIGINT, 
                 start_delivery_date       TIMESTAMP,
                 start_delivery_latitude   FLOAT,
                 start_delivery_longitude  FLOAT,
                 finish_delivery_date      TIMESTAMP,
                 finish_delivery_latitude  FLOAT,
                 finish_delivery_longitude FLOAT,
                
                 cancel_reason_id           INT, 
                 cancel_reason              TEXT,
                 cancellation_type          TEXT,
                 cancelled_after_ship       BOOLEAN,
                 affect_cancellation_rating BOOLEAN,
                 cancellation_initiator     TEXT);"""

logs_button_clicks = """CREATE TABLE IF NOT EXISTS logs_button_clicks 
                        (id              SERIAL PRIMARY KEY,
                         date            TIMESTAMP,
                         tg_id           BIGINT,
                         chat_id         BIGINT,
                         message_id      BIGINT,
                         from_user_tg_id BIGINT, 
                         first_name      TEXT,
                         last_name       TEXT,
                         username        TEXT,
                         button_name     TEXT,
                         button_data     TEXT);"""

logs_status_changes = """CREATE TABLE IF NOT EXISTS logs_status_changes 
                         (id                 SERIAL PRIMARY KEY,
                          date               TIMESTAMP,
                          status             TEXT,
                          status_ozon_seller TEXT, 
                          posting_number     TEXT, 
                          employee_id        BIGINT,
                          latitude           FLOAT,
                          longitude          FLOAT);"""

logs_errors = """CREATE TABLE IF NOT EXISTS logs_errors
                 (id                 SERIAL PRIMARY KEY,
                  date               TIMESTAMP,
                  error_name         TEXT,
                  type               TEXT,
                  user_id            BIGINT,
                  posting_number     TEXT,
                  warehouse_id       BIGINT,
                  description        TEXT);"""


order_list = """CREATE TABLE IF NOT EXISTS order_list 
                (id             SERIAL PRIMARY KEY,
                 order_id       BIGINT,
                 posting_number TEXT,
                 sku            BIGINT,
                 name           TEXT,
                 offer_id       TEXT,
                 quantity       INT, 
                 price          FLOAT,
                 changed        BOOLEAN,
                 fact_quantity  INT,
                 weight         FLOAT,
                 volume_weight  FLOAT,
                 category_id    INT,
                 product_id     BIGINT,
                 barcode        BIGINT,
                 primary_image  TEXT,
                 rank           INT);"""

employee_stat = """CREATE TABLE IF NOT EXISTS employee_stat 
                   (tg_id         BIGINT PRIMARY KEY,
                    orders_number INT,
                    successful    INT,
                    unsuccessful  INT);"""

customer_stat = """CREATE TABLE IF NOT EXISTS customer_stat 
                   (customer_id   BIGINT PRIMARY KEY,
                    orders_number TEXT,
                    successful    INT,
                    unsuccessful  INT);"""

fsm = """CREATE TABLE IF NOT EXISTS finite_state_machine 
         (tg_id         BIGINT PRIMARY KEY,
          message_id    BIGINT,
          chat_id       BIGINT,
          text          TEXT,
          entities      json,
          reply_markup  json,
          data          TEXT,
          previous_data TEXT,
          date          TIMESTAMP);"""

routing = """CREATE TABLE IF NOT EXISTS routing 
             (id                        SERIAL PRIMARY KEY,
              total_rank                INT,
              weight                    BOOLEAN,
              parent_category_id        BIGINT,
              parent_category_name      TEXT,
              parent_category_rank      INT,
              child_category_id         BIGINT,
              child_category_name       TEXT,
              child_category_rank       INT,
              under_child_category_id   BIGINT,
              under_child_category_name TEXT,
              under_child_category_rank INT,
              date_added                TIMESTAMP,
              date_of_change            TIMESTAMP,
              deletion_date             TIMESTAMP,
              date                      TIMESTAMP);"""

tags = """CREATE TABLE IF NOT EXISTS tags
          (id SERIAL PRIMARY KEY,
           date TIMESTAMP,
           posting_number TEXT,
           hashtag TEXT);"""

tables = [logs_bot_running, api, employee, order_info, logs_button_clicks,
          logs_status_changes, order_list, employee_stat, customer_stat, fsm, routing, tags]
