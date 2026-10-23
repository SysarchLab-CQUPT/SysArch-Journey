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
