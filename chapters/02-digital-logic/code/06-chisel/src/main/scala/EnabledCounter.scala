import chisel3._

class EnabledCounter(val width: Int) extends Module {
  require(width > 0, "width must be positive")

  val io = IO(new Bundle {
    val enable = Input(Bool())
    val value = Output(UInt(width.W))
  })

  // 显式采用同步复位，复位值为零。
  val count = withReset(reset.asBool) {
    RegInit(0.U(width.W))
  }
  when(io.enable) {
    count := count + 1.U
  }
  io.value := count
}
