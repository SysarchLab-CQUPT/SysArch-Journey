`timescale 1ns/1ps
// Teaching subset: ADD, SUB, ADDI, LW, SW, BEQ. Not a complete RV32I decoder.
module decoder (
    input  wire [31:0] instr,
    output wire [4:0]  rs1, rs2, rd,
    output reg  [31:0] imm,
    output reg uses_rs1, uses_rs2,
    output reg reg_write, mem_read, mem_write,
    output reg alu_imm, alu_sub, branch, legal
);
    assign rs1 = instr[19:15];
    assign rs2 = instr[24:20];
    assign rd  = instr[11:7];
    always @* begin
        imm = 32'b0;
        uses_rs1 = 0; uses_rs2 = 0;
        reg_write = 0; mem_read = 0; mem_write = 0;
        alu_imm = 0; alu_sub = 0; branch = 0; legal = 0;
        case (instr[6:0])
            7'b0110011: begin
                if (instr[14:12] == 3'b000 &&
                    (instr[31:25] == 7'b0000000 ||
                     instr[31:25] == 7'b0100000)) begin
                    legal = 1; uses_rs1 = 1; uses_rs2 = 1;
                    reg_write = 1; alu_sub = instr[30];
                end
            end
            7'b0010011: begin
                if (instr[14:12] == 3'b000) begin
                    legal = 1; uses_rs1 = 1; reg_write = 1; alu_imm = 1;
                    imm = {{20{instr[31]}}, instr[31:20]};
                end
            end
            7'b0000011: begin
                if (instr[14:12] == 3'b010) begin
                    legal = 1; uses_rs1 = 1; reg_write = 1;
                    mem_read = 1; alu_imm = 1;
                    imm = {{20{instr[31]}}, instr[31:20]};
                end
            end
            7'b0100011: begin
                if (instr[14:12] == 3'b010) begin
                    legal = 1; uses_rs1 = 1; uses_rs2 = 1;
                    mem_write = 1; alu_imm = 1;
                    imm = {{20{instr[31]}}, instr[31:25], instr[11:7]};
                end
            end
            7'b1100011: begin
                if (instr[14:12] == 3'b000) begin
                    legal = 1; uses_rs1 = 1; uses_rs2 = 1; branch = 1;
                    imm = {{19{instr[31]}}, instr[31], instr[7],
                           instr[30:25], instr[11:8], 1'b0};
                end
            end
            default: begin end
        endcase
    end
endmodule
