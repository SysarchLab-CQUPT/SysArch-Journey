// ============================================================
// led_shifter.v —— 流水灯：每个 tick 把亮灯的位置挪一位
// 用拼接运算实现“循环移位”，最高位移出去后回到最低位。
// ============================================================
module led_shifter #(
    parameter integer WIDTH = 4          // LED 个数
) (
    input  wire             clk,         // 系统时钟
    input  wire             rst_n,       // 异步复位，低电平有效
    input  wire             tick,        // 移位节拍（一个周期的高脉冲）
    output reg  [WIDTH-1:0] led          // LED 输出，高电平点亮
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            // 复位：只有最低位亮。{(WIDTH-1){1'b0}} 表示复制 WIDTH-1 个 0
            led <= {{(WIDTH-1){1'b0}}, 1'b1};
        else if (tick)
            // 左移：丢掉最高位，同时把它接到最低位，形成循环
            led <= {led[WIDTH-2:0], led[WIDTH-1]};
    end

endmodule
