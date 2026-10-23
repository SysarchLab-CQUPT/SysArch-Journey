`timescale 1ns/1ps
module forward_unit (
    input wire ex_valid, uses_rs1, uses_rs2,
    input wire [4:0] rs1, rs2,
    input wire m_valid, m_reg_write, m_mem_read,
    input wire [4:0] m_rd,
    input wire w_valid, w_reg_write,
    input wire [4:0] w_rd,
    output reg [1:0] forward_a, forward_b
);
    // 00: ID/EX value; 10: EX/MEM ALU result; 01: MEM/WB writeback value.
    wire m_a = ex_valid && uses_rs1 && rs1 != 0 &&
               m_valid && m_reg_write && m_rd == rs1;
    wire m_b = ex_valid && uses_rs2 && rs2 != 0 &&
               m_valid && m_reg_write && m_rd == rs2;
    wire w_a = ex_valid && uses_rs1 && rs1 != 0 &&
               w_valid && w_reg_write && w_rd == rs1;
    wire w_b = ex_valid && uses_rs2 && rs2 != 0 &&
               w_valid && w_reg_write && w_rd == rs2;
    always @* begin
        forward_a = 2'b00;
        forward_b = 2'b00;
        // The youngest matching writer owns the value. If it is a load,
        // it is not ready here; do NOT fall through to an older WB writer.
        if (m_a) begin
            if (!m_mem_read) forward_a = 2'b10;
        end else if (w_a) forward_a = 2'b01;
        if (m_b) begin
            if (!m_mem_read) forward_b = 2'b10;
        end else if (w_b) forward_b = 2'b01;
    end
endmodule
