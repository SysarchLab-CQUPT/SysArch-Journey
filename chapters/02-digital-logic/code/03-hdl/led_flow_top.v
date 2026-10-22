// ============================================================
// led_flow_top.v —— 顶层：把“分频器”和“流水灯”连成完整电路
// 顶层不写逻辑，只负责例化和连线。
// ============================================================
module led_flow_top (
    input  wire       clk,      // 板载 50 MHz 时钟
    input  wire       rst_n,    // 复位按键，低电平有效
    output wire [3:0] led       // 4 个 LED
);

    wire tick;                  // 分频器与移位器之间的“节拍”连线

    clk_div #(
        .CLK_FREQ (50_000_000),
        .TICK_HZ  (1)
    ) u_clk_div (
        .clk   (clk),
        .rst_n (rst_n),
        .tick  (tick)
    );

    led_shifter #(
        .WIDTH (4)
    ) u_led_shifter (
        .clk   (clk),
        .rst_n (rst_n),
        .tick  (tick),
        .led   (led)
    );

endmodule
