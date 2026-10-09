// 五级流水线的寄存器传递骨架
module pipeline_regs (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [31:0] if_pc,
    output reg  [31:0] id_pc
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            id_pc <= 32'b0;          // 复位时清零
        else
            id_pc <= if_pc;          // 取指级的 PC 传给译码级
    end
endmodule
