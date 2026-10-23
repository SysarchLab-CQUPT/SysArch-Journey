`timescale 1ns/1ps
// SystemVerilog is used only by the testbench; the DUT is Verilog-2001.
module tb_pipeline;
    reg clk = 0;
    reg rst = 1;
    always #5 clk = ~clk;
    wire [31:0] ia, da, dw, ir, dr, cp, cd;
    wire mr, mw, cv, cw;
    wire [4:0] cr;
    reg [31:0] imem [0:511];
    reg [31:0] dmem [0:255];
    assign ir = imem[ia[10:2]];
    assign dr = dmem[da[9:2]];
    pipeline_demo dut (
        .clk(clk), .rst(rst), .imem_addr(ia), .imem_rdata(ir),
        .dmem_addr(da), .dmem_wdata(dw), .dmem_read(mr), .dmem_write(mw),
        .dmem_rdata(dr), .commit_valid(cv), .commit_we(cw),
        .commit_pc(cp), .commit_rd(cr), .commit_data(cd)
    );
    integer cycle = 0, max_cycles, trace_fd, event_fd, i;
    reg prev_stall = 0, prev_redirect = 0;
    reg [31:0] prev_pc, prev_dpc, prev_instr, prev_target;
    reg [31:0] prev_epc;
    reg prev_evalid;
    initial begin
        for (i = 0; i < 512; i = i + 1) imem[i] = 32'h00000013;
        for (i = 0; i < 256; i = i + 1) dmem[i] = 0;
        $readmemh("program.hex", imem);
        $readmemh("memory.hex", dmem);
        if (!$value$plusargs("CYCLES=%d", max_cycles)) max_cycles = 60;
        trace_fd = $fopen("trace.csv", "w");
        event_fd = $fopen("events.csv", "w");
        $fdisplay(trace_fd, "cycle,pc_f,pc_d,pc_e,pc_m,pc_w,load_use,forward_a,forward_b,redirect,pc_en,ifid_en,ifid_flush,idex_flush,ex_a,ex_rs2,wb_we,wb_rd,wb_data,mem_we,mem_addr,mem_data");
        $fdisplay(event_fd, "kind,pc,dest,data");
        $dumpfile("wave.vcd");
        $dumpvars(0, tb_pipeline);
        repeat (2) @(negedge clk);
        #1 rst = 0;
    end
    // These samples describe the cycle ENDING at this rising edge.
    // All RHS values are sampled before DUT nonblocking assignments update.
    always @(posedge clk) begin
        if (!rst) begin
            cycle = cycle + 1;
            if (ia[1:0] != 0 || ia >= 2048) $fatal(1, "instruction address out of model");
            if ((mr || mw) && (da[1:0] != 0 || da >= 1024))
                $fatal(1, "unaligned/out-of-range data access");
            if (dut.ifid_valid && !dut.d_legal) $fatal(1, "unsupported instruction");
            if (prev_stall && !prev_redirect) begin
                if (ia !== prev_pc || dut.ifid_pc !== prev_dpc ||
                    dut.ifid_instr !== prev_instr || dut.idex_valid)
                    $fatal(1, "load-use must hold front end and bubble ID/EX");
                if (dut.exmem_valid !== prev_evalid || dut.exmem_pc !== prev_epc)
                    $fatal(1, "load must advance into MEM");
            end
            if (prev_redirect && (ia !== prev_target || dut.ifid_valid || dut.idex_valid))
                $fatal(1, "redirect must replace PC and invalidate younger stages");
            if (dut.idex_valid && dut.exmem_valid && dut.exmem_mr && dut.exmem_rd != 0 &&
                ((dut.idex_use1 && dut.idex_rs1 == dut.exmem_rd) ||
                 (dut.idex_use2 && dut.idex_rs2 == dut.exmem_rd)))
                $fatal(1, "consumer reached EX before youngest load is ready");
            if (dut.rf.regs[0] !== 0) $fatal(1, "x0 changed");
            if (mw) begin
                dmem[da[9:2]] <= dw;
                $fdisplay(event_fd,"S,%08x,%08x,%08x",dut.exmem_pc,da,dw);
            end
            if (cw) $fdisplay(event_fd,"W,%08x,%08x,%08x",cp,{27'b0,cr},cd);
            $fdisplay(trace_fd,"%0d,%08x,%08x,%08x,%08x,%08x,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%08x,%08x,%0d,%0d,%08x,%0d,%08x,%08x",
                cycle,ia,dut.ifid_valid?dut.ifid_pc:32'hffffffff,
                dut.idex_valid?dut.idex_pc:32'hffffffff,
                dut.exmem_valid?dut.exmem_pc:32'hffffffff,
                dut.memwb_valid?dut.memwb_pc:32'hffffffff,
                dut.load_use,dut.forward_a,dut.forward_b,dut.redirect,
                dut.pc_en,dut.ifid_en,dut.ifid_flush,dut.idex_flush,
                dut.ex_a,dut.ex_rs2,cw,cr,cd,mw,da,dw);
            prev_stall = dut.load_use; prev_redirect = dut.redirect;
            prev_pc = ia; prev_dpc = dut.ifid_pc; prev_instr = dut.ifid_instr;
            prev_target = dut.redirect_pc;
            prev_epc = dut.idex_pc; prev_evalid = dut.idex_valid;
            if (cycle == max_cycles) begin
                $fclose(trace_fd); $fclose(event_fd);
                $display("PASS: cycle invariants (%0d cycles)", cycle);
                $finish;
            end
        end
    end
endmodule
