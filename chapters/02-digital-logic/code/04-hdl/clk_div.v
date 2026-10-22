// ============================================================
// clk_div.v —— 时钟分频：把 50 MHz 变成 1 Hz 的“节拍脉冲”
// 50 MHz 表示每秒有 5000 万个时钟周期；1 Hz 表示每秒一个 tick。
// 所以数满 5000 万个周期给出一个 tick，正好一秒一次。
// ============================================================
module clk_div #(
    parameter integer CLK_FREQ = 50_000_000,  // 输入时钟频率，单位 Hz
    parameter integer TICK_HZ  = 1            // 每秒产生几个 tick（1 = 每秒一次）
) (
    input  wire clk,     // 系统时钟（50 MHz）
    input  wire rst_n,   // 异步复位，低电平有效
    output reg  tick     // 节拍：宽度恰好一个 clk 周期
);

    // 计数器从 0 数到 CNT_MAX 为一个循环，共 CNT_MAX+1 个周期。
    // 50 MHz、TICK_HZ=1 时：50000000 × 20 ns = 1 秒，
    // 所以 CNT_MAX = 50000000 - 1 = 49999999。
    localparam integer CNT_MAX = CLK_FREQ / TICK_HZ - 1;

    // 位宽要能装下 CNT_MAX（49999999）：2^26 = 67108864，26 位就够；
    // 这里直接给 32 位，留足余量，也省得换频率时重算位宽。
    reg [31:0] cnt;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cnt  <= 32'd0;
            tick <= 1'b0;
        end else if (cnt == CNT_MAX) begin
            cnt  <= 32'd0;
            tick <= 1'b1;             // 只高一个周期，形成一个脉冲
        end else begin
            cnt  <= cnt + 32'd1;
            tick <= 1'b0;
        end
    end

endmodule
