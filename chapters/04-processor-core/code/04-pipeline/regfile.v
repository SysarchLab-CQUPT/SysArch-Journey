`timescale 1ns/1ps
module regfile (
    input wire clk, rst,
    input wire [4:0] rs1, rs2, rd,
    input wire we,
    input wire [31:0] wd,
    output wire [31:0] rv1, rv2
);
    reg [31:0] regs [0:31];
    integer i;
    always @(posedge clk) begin
        if (rst) begin
            for (i = 0; i < 32; i = i + 1) regs[i] <= 0;
        end else if (we && rd != 0) begin
            regs[rd] <= wd;
        end
    end
    // Explicit WB -> ID bypass avoids reliance on simulator scheduling or
    // a particular register-file primitive's read-during-write behavior.
    assign rv1 = (rs1 == 0) ? 32'b0 :
                 (we && rd == rs1) ? wd : regs[rs1];
    assign rv2 = (rs2 == 0) ? 32'b0 :
                 (we && rd == rs2) ? wd : regs[rs2];
endmodule
