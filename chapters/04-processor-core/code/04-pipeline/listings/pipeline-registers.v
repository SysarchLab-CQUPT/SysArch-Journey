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
