`timescale 1ns/1ps
// Five-stage teaching datapath, fixed-latency Harvard memory interfaces.
// Instruction and data reads are COMBINATIONAL; data writes use posedge clk.
module pipeline_demo (
    input wire clk, rst,
    output reg [31:0] imem_addr,
    input wire [31:0] imem_rdata,
    output wire [31:0] dmem_addr, dmem_wdata,
    output wire dmem_read, dmem_write,
    input wire [31:0] dmem_rdata,
    output wire commit_valid, commit_we,
    output wire [31:0] commit_pc, commit_data,
    output wire [4:0] commit_rd
);
    // IF/ID: the instruction and ITS OWN address travel together.
    reg ifid_valid;
    reg [31:0] ifid_pc, ifid_instr;
    wire [4:0] d_rs1, d_rs2, d_rd;
    wire [31:0] d_imm, d_rv1, d_rv2;
    wire d_use1, d_use2, d_rw, d_mr, d_mw, d_ai, d_sub, d_br, d_legal;
    decoder dec (
        .instr(ifid_instr), .rs1(d_rs1), .rs2(d_rs2), .rd(d_rd),
        .imm(d_imm), .uses_rs1(d_use1), .uses_rs2(d_use2),
        .reg_write(d_rw), .mem_read(d_mr), .mem_write(d_mw),
        .alu_imm(d_ai), .alu_sub(d_sub), .branch(d_br), .legal(d_legal)
    );

    // ID/EX contains operands, register numbers and future-stage controls.
    reg idex_valid;
    reg [31:0] idex_pc, idex_rv1, idex_rv2, idex_imm;
    reg [4:0] idex_rs1, idex_rs2, idex_rd;
    reg idex_use1, idex_use2, idex_rw, idex_mr, idex_mw;
    reg idex_ai, idex_sub, idex_br;
    // EX/MEM holds an address/ALU result and forwarded store data.
    reg exmem_valid;
    reg [31:0] exmem_pc, exmem_result, exmem_store;
    reg [4:0] exmem_rd;
    reg exmem_rw, exmem_mr, exmem_mw;
    // MEM/WB holds the load result separately from the ALU result.
    reg memwb_valid;
    reg [31:0] memwb_pc, memwb_result, memwb_load;
    reg [4:0] memwb_rd;
    reg memwb_rw, memwb_mr;
    wire [31:0] wb_data = memwb_mr ? memwb_load : memwb_result;
    wire wb_we = !rst && memwb_valid && memwb_rw && memwb_rd != 0;
    regfile rf (
        .clk(clk), .rst(rst), .rs1(d_rs1), .rs2(d_rs2),
        .rd(memwb_rd), .we(wb_we), .wd(wb_data), .rv1(d_rv1), .rv2(d_rv2)
    );

    wire [1:0] forward_a, forward_b;
    forward_unit fwd (
        .ex_valid(idex_valid), .uses_rs1(idex_use1), .uses_rs2(idex_use2),
        .rs1(idex_rs1), .rs2(idex_rs2),
        .m_valid(exmem_valid), .m_reg_write(exmem_rw),
        .m_mem_read(exmem_mr), .m_rd(exmem_rd),
        .w_valid(memwb_valid), .w_reg_write(memwb_rw), .w_rd(memwb_rd),
        .forward_a(forward_a), .forward_b(forward_b)
    );
    wire [31:0] ex_a = (forward_a == 2'b10) ? exmem_result :
                       (forward_a == 2'b01) ? wb_data : idex_rv1;
    wire [31:0] ex_rs2 = (forward_b == 2'b10) ? exmem_result :
                         (forward_b == 2'b01) ? wb_data : idex_rv2;
    // Store/branch use ex_rs2; ALU's second operand may instead be immediate.
    wire [31:0] ex_b = idex_ai ? idex_imm : ex_rs2;
    wire [31:0] ex_result = idex_sub ? ex_a - ex_b : ex_a + ex_b;
    wire redirect = idex_valid && idex_br && ex_a == ex_rs2;
    wire [31:0] redirect_pc = idex_pc + idex_imm;
    wire load_use, pc_en, ifid_en, ifid_flush, idex_flush;
    hazard_unit hazards (
        .d_valid(ifid_valid && d_legal), .d_uses_rs1(d_use1),
        .d_uses_rs2(d_use2), .d_rs1(d_rs1), .d_rs2(d_rs2),
        .e_valid(idex_valid), .e_mem_read(idex_mr), .e_rd(idex_rd),
        .redirect(redirect), .load_use(load_use), .pc_en(pc_en),
        .ifid_en(ifid_en), .ifid_flush(ifid_flush), .idex_flush(idex_flush)
    );

    // IF: synchronous reset > redirect > hold/advance.
    always @(posedge clk) begin
        if (rst) imem_addr <= 0;
        else if (pc_en) imem_addr <= redirect ? redirect_pc : imem_addr + 4;
    end
    // Flush has priority over enable: killed instructions must not survive.
    always @(posedge clk) begin
        if (rst || ifid_flush) begin
            ifid_valid <= 0;
        end else if (ifid_en) begin
            ifid_valid <= 1;
            ifid_pc <= imem_addr;
            ifid_instr <= imem_rdata;
        end
    end
    // Hold PC and IF/ID on load-use, but INSERT A BUBBLE into ID/EX.
    always @(posedge clk) begin
        if (rst || idex_flush) begin
            idex_valid <= 0;
        end else begin
            idex_valid <= ifid_valid && d_legal;
            idex_pc <= ifid_pc;
            idex_rv1 <= d_rv1; idex_rv2 <= d_rv2; idex_imm <= d_imm;
            idex_rs1 <= d_rs1; idex_rs2 <= d_rs2; idex_rd <= d_rd;
            idex_use1 <= d_use1; idex_use2 <= d_use2;
            idex_rw <= d_rw; idex_mr <= d_mr; idex_mw <= d_mw;
            idex_ai <= d_ai; idex_sub <= d_sub; idex_br <= d_br;
        end
    end
    // Older instructions continue, even while the front end is paused/flushed.
    always @(posedge clk) begin
        if (rst) exmem_valid <= 0;
        else begin
            exmem_valid <= idex_valid;
            exmem_pc <= idex_pc; exmem_result <= ex_result;
            exmem_store <= ex_rs2; exmem_rd <= idex_rd;
            exmem_rw <= idex_rw; exmem_mr <= idex_mr; exmem_mw <= idex_mw;
        end
    end
    always @(posedge clk) begin
        if (rst) memwb_valid <= 0;
        else begin
            memwb_valid <= exmem_valid;
            memwb_pc <= exmem_pc; memwb_rd <= exmem_rd;
            memwb_result <= exmem_result; memwb_load <= dmem_rdata;
            memwb_rw <= exmem_rw; memwb_mr <= exmem_mr;
        end
    end
    assign dmem_addr  = exmem_result;
    assign dmem_wdata = exmem_store;
    assign dmem_read  = !rst && exmem_valid && exmem_mr;
    assign dmem_write = !rst && exmem_valid && exmem_mw;
    assign commit_valid = !rst && memwb_valid;
    assign commit_pc = memwb_pc;
    assign commit_we = wb_we;
    assign commit_rd = memwb_rd;
    assign commit_data = wb_data;
endmodule
