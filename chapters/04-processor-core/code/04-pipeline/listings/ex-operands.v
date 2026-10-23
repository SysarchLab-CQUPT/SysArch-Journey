    wire [31:0] ex_a = (forward_a == 2'b10) ? exmem_result :
                       (forward_a == 2'b01) ? wb_data : idex_rv1;
    wire [31:0] ex_rs2 = (forward_b == 2'b10) ? exmem_result :
                         (forward_b == 2'b01) ? wb_data : idex_rv2;
    // Store/branch use ex_rs2; ALU's second operand may instead be immediate.
    wire [31:0] ex_b = idex_ai ? idex_imm : ex_rs2;
    wire [31:0] ex_result = idex_sub ? ex_a - ex_b : ex_a + ex_b;
    wire redirect = idex_valid && idex_br && ex_a == ex_rs2;
    wire [31:0] redirect_pc = idex_pc + idex_imm;
