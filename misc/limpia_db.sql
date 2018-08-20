delete from stock_quant_move_rel;
delete from stock_move;
delete from stock_quant;
delete from stock_inventory;
delete from stock_production_lot;
delete from stock_inventory_line;
delete from stock_scrap;
delete from stock_quant_package;
delete from stock_pack_operation;
delete from stock_pack_operation_lot;
delete from stock_picking;
delete from sale_order_line;
delete from sale_order;
delete from mail_message;
delete from mail_followers;
delete from procurement_order;
delete from product_product;

ALTER SEQUENCE stock_move_id_seq RESTART WITH 1;
ALTER SEQUENCE stock_quant_id_seq RESTART WITH 1;
ALTER SEQUENCE stock_inventory_id_seq RESTART WITH 1;
ALTER SEQUENCE stock_production_lot_id_seq RESTART WITH 1;
ALTER SEQUENCE stock_production_lot_serial_id_seq RESTART WITH 1;
ALTER SEQUENCE stock_inventory_line_id_seq RESTART WITH 1;
ALTER SEQUENCE stock_scrap_id_seq RESTART WITH 1;
ALTER SEQUENCE stock_quant_package_id_seq RESTART WITH 1;
ALTER SEQUENCE stock_pack_operation_id_seq RESTART WITH 1;
ALTER SEQUENCE stock_pack_operation_lot_id_seq RESTART WITH 1;
ALTER SEQUENCE stock_picking_id_seq RESTART WITH 1;
ALTER SEQUENCE sale_order_line_id_seq RESTART WITH 1;
ALTER SEQUENCE sale_order_id_seq RESTART WITH 1;
ALTER SEQUENCE mail_followers_id_seq RESTART WITH 1;

ALTER SEQUENCE ir_sequence_001 RESTART WITH 1;
ALTER SEQUENCE ir_sequence_002 RESTART WITH 1;
ALTER SEQUENCE ir_sequence_003 RESTART WITH 1;
ALTER SEQUENCE ir_sequence_004 RESTART WITH 1;
ALTER SEQUENCE ir_sequence_005 RESTART WITH 1;
ALTER SEQUENCE ir_sequence_006 RESTART WITH 1;
ALTER SEQUENCE ir_sequence_007 RESTART WITH 1;
ALTER SEQUENCE ir_sequence_008 RESTART WITH 1;
ALTER SEQUENCE ir_sequence_009 RESTART WITH 1;
ALTER SEQUENCE ir_sequence_010 RESTART WITH 1;
ALTER SEQUENCE ir_sequence_011 RESTART WITH 1;
ALTER SEQUENCE ir_sequence_012 RESTART WITH 1;
ALTER SEQUENCE ir_sequence_019 RESTART WITH 1;
ALTER SEQUENCE ir_sequence_027 RESTART WITH 1;
ALTER SEQUENCE ir_sequence_028 RESTART WITH 1;
ALTER SEQUENCE ir_sequence_029 RESTART WITH 1;
ALTER SEQUENCE ir_sequence_030 RESTART WITH 1;
ALTER SEQUENCE ir_sequence_031 RESTART WITH 1;