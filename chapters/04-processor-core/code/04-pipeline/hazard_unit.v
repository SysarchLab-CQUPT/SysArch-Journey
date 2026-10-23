`timescale 1ns/1ps
module hazard_unit (
    input wire d_valid, d_uses_rs1, d_uses_rs2,
    input wire [4:0] d_rs1, d_rs2,
    input wire e_valid, e_mem_read,
    input wire [4:0] e_rd,
    input wire redirect,
    output wire load_use, pc_en, ifid_en, ifid_flush, idex_flush
);
    assign load_use = d_valid && e_valid && e_mem_read && e_rd != 0 &&
                      ((d_uses_rs1 && d_rs1 == e_rd) ||
                       (d_uses_rs2 && d_rs2 == e_rd));
    assign pc_en      = redirect || !load_use;
    assign ifid_en    = !load_use;
    assign ifid_flush = redirect;
    assign idex_flush = redirect || load_use;
endmodule
