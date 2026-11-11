import chisel3._
import chiseltest._
import org.scalatest.flatspec.AnyFlatSpec

class EnabledCounterSpec extends AnyFlatSpec
    with ChiselScalatestTester {
  behavior of "EnabledCounter"

  for (width <- Seq(1, 4, 8)) {
    it should s"reset, hold and wrap at width $width" in {
      test(new EnabledCounter(width))
        .withAnnotations(Seq(WriteVcdAnnotation)) { dut =>
          dut.io.enable.poke(false.B)
          dut.reset.poke(true.B)
          dut.clock.step()
          dut.io.value.expect(0.U)
          dut.reset.poke(false.B)

          val modulus = BigInt(1) << width
          var model = BigInt(0)
          // 足够的有效拍覆盖一次回绕，间隔插入暂停。
          for (cycle <- 0 until (1 << width) * 2 + 4) {
            val enable = cycle % 3 != 0
            dut.io.enable.poke(enable.B)
            dut.clock.step()
            if (enable) model = (model + 1) % modulus
            dut.io.value.expect(model.U)
          }

          // 使能与复位同时有效时，复位优先。
          dut.io.enable.poke(true.B)
          dut.reset.poke(true.B)
          dut.clock.step()
          dut.io.value.expect(0.U)
          dut.reset.poke(false.B)
          dut.clock.step()
          dut.io.value.expect(1.U)
        }
    }
  }
}
